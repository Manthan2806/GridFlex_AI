"""Freeze the water-heater expected and conservative prediction recipe.

Only train and validation outcomes are read. The test split remains sealed for
the one-time final evaluation performed by evaluate_water_heater_final.py.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

from ai_ml.water_heater_model.train_water_heater_candidate import (
    DEFAULT_BASELINE_REPORT,
    DEFAULT_INPUT,
    DEFAULT_OUTPUT as DEFAULT_DEVELOPMENT_REPORT,
    MODEL_PARAMETERS,
    _canonical_sha256,
    _impute,
    _load_development_data,
)
from ai_ml.water_heater_model.prepare_water_heater_training_data import MODEL_FEATURE_COLUMNS


DEFAULT_OUTPUT = Path("data/processed/water_heater_training/water_heater_candidate_v1_config.json")
LOWER_QUANTILE = 0.10
MAX_OVERPREDICTION_PERCENT = 15.0


def _groups(potential: np.ndarray, group_rows: list[tuple[int, int, int]], thresholds: dict[str, float]):
    heater = np.asarray([row[1] for row in group_rows])
    direction = np.asarray([row[2] for row in group_rows])
    return {
        "all": np.ones(len(potential), dtype=bool),
        "heat_pump": heater == 1,
        "electric_resistance": heater == 0,
        "reduce": direction == 1,
        "increase": direction == 0,
        "small": potential <= thresholds["small_max"],
        "medium": (potential > thresholds["small_max"]) & (potential <= thresholds["medium_max"]),
        "large": potential > thresholds["medium_max"],
    }


def calibrate(
    input_path: Path = DEFAULT_INPUT,
    development_path: Path = DEFAULT_DEVELOPMENT_REPORT,
    baseline_path: Path = DEFAULT_BASELINE_REPORT,
) -> tuple[dict, HistGradientBoostingRegressor, HistGradientBoostingRegressor]:
    development = json.loads(development_path.read_text(encoding="utf-8"))
    if development.get("status") != "accepted_for_safety_calibration":
        raise ValueError("development candidate is not accepted for calibration")
    input_hash = _canonical_sha256(input_path)
    if development["evidence"]["training_table_canonical_sha256"] != input_hash:
        raise ValueError("training table changed after candidate development")

    data = _load_development_data(input_path)
    train_x, validation_x, medians = _impute(
        data["features"]["train"], data["features"]["validation"]
    )
    train_y = np.asarray(data["targets"]["train"], dtype=float)
    actual = np.asarray(data["targets"]["validation"], dtype=float)
    potential = np.asarray(data["potentials"]["validation"], dtype=float)
    train_potential = np.asarray(data["potentials"]["train"], dtype=float)

    expected_model = HistGradientBoostingRegressor(**MODEL_PARAMETERS).fit(train_x, train_y)
    lower_parameters = {
        **MODEL_PARAMETERS,
        "loss": "quantile",
        "quantile": LOWER_QUANTILE,
    }
    lower_model = HistGradientBoostingRegressor(**lower_parameters).fit(train_x, train_y)
    expected = np.clip(expected_model.predict(validation_x), 0.0, 1.0)
    trusted = np.minimum(expected, np.clip(lower_model.predict(validation_x), 0.0, 1.0))
    small, medium = np.quantile(train_potential, [1 / 3, 2 / 3])
    thresholds = {"small_max": round(float(small), 8), "medium_max": round(float(medium), 8)}

    group_results = {}
    for name, mask in _groups(potential, data["groups"]["validation"], thresholds).items():
        if not np.any(mask):
            raise ValueError(f"validation group {name} is empty")
        rate = 100.0 * float(np.mean(trusted[mask] > actual[mask] + 1e-12))
        group_results[name] = {
            "row_count": int(np.sum(mask)),
            "overprediction_rate_percent": round(rate, 6),
            "maximum_allowed_percent": MAX_OVERPREDICTION_PERCENT,
            "passes": rate <= MAX_OVERPREDICTION_PERCENT,
        }
    expected_kw = expected * potential
    trusted_kw = trusted * potential
    retention = 100.0 * float(np.sum(trusted_kw) / np.sum(expected_kw))
    checks = {
        "all_validation_groups_pass": all(value["passes"] for value in group_results.values()),
        "trusted_never_exceeds_expected": bool(np.all(trusted <= expected + 1e-12)),
        "trusted_power_is_nonzero": bool(np.sum(trusted_kw) > 0),
        "test_outcomes_remained_unread": True,
    }
    config = {
        "candidate_version": "water_heater_candidate_v1",
        "status": "locked_for_final_holdout" if all(checks.values()) else "calibration_rejected",
        "deployment_allowed": False,
        "feature_contract": {
            "names_in_order": list(MODEL_FEATURE_COLUMNS),
            "imputation_medians": medians,
            "features_allowed_to_be_missing": [
                name for name in MODEL_FEATURE_COLUMNS if name.startswith("prior_")
            ],
        },
        "expected_model": {"family": "HistGradientBoostingRegressor", "parameters": MODEL_PARAMETERS},
        "safety_policy": {
            "method": "validation-selected lower conditional quantile",
            "lower_quantile": LOWER_QUANTILE,
            "lower_model_parameters": lower_parameters,
            "maximum_allowed_overprediction_rate_percent": MAX_OVERPREDICTION_PERCENT,
            "potential_group_thresholds_kw": thresholds,
            "validation_groups": group_results,
            "validation_trusted_kw_retained_percent": round(retention, 6),
            "retention_is_acceptance_gate": False,
        },
        "locking_checks": checks,
        "test_holdout": {"status": "sealed", "target_columns_read": False},
        "evidence": {
            "training_table_canonical_sha256": input_hash,
            "development_report_canonical_sha256": _canonical_sha256(development_path),
            "baseline_report_canonical_sha256": _canonical_sha256(baseline_path),
        },
        "limitations": [
            "All water-heater outcomes are synthetic, so this supports a hackathon prototype only.",
            "The conservative estimate retains little power; retention is reported, not hidden.",
            "No final test outcome was used to select this policy.",
        ],
    }
    return config, expected_model, lower_model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--development", type=Path, default=DEFAULT_DEVELOPMENT_REPORT)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    config, _, _ = calibrate(args.input, args.development, args.baseline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"Water-heater candidate status: {config['status']}")
    print(f"Validation trusted kW retained: {config['safety_policy']['validation_trusted_kw_retained_percent']:.2f}%")
    for name, result in config["safety_policy"]["validation_groups"].items():
        print(f"{name}: {result['overprediction_rate_percent']:.2f}% ({'PASS' if result['passes'] else 'FAIL'})")
    print("Final test outcomes read: false")


if __name__ == "__main__":
    main()
