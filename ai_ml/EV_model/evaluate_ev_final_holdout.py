"""Run the one-time final EV holdout evaluation for the locked candidate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from math import isfinite
from pathlib import Path
from statistics import fmean

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor

from ai_ml.EV_model.load_ev_training_data import (
    DEFAULT_INPUT_PATH,
    EVALUATION_DISPATCH_COLUMN,
    TARGET_COLUMN,
    load_ev_training_data,
)
from ai_ml.EV_model.lock_ev_model_candidate import DEFAULT_OUTPUT_PATH as DEFAULT_CONFIG_PATH
from ai_ml.EV_model.predict_ev_flexibility import predict_flexibility
from ai_ml.EV_model.train_ev_random_forest import _calculate_metrics


DEFAULT_REPORT_PATH = Path("data/processed/ev_training/ev_final_holdout_evaluation.json")
DEFAULT_MODEL_PATH = Path("ai_ml/EV_model/artifacts/ev_random_forest_v1.joblib")
EVALUATION_VERSION = "ev_final_holdout_evaluation_v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_locked_inputs(config: dict, input_path: Path, config_path: Path) -> None:
    if config.get("status") != "locked_before_final_holdout_evaluation":
        raise ValueError("candidate configuration is not locked for final evaluation")
    locked_input = config.get("inputs", {}).get("training_table", {})
    if locked_input.get("sha256") != _sha256(input_path):
        raise ValueError("training table changed after the candidate was locked")
    if not config_path.is_file():
        raise ValueError("locked candidate configuration does not exist")


def _load_test_outcomes(input_path: Path, expected_resource_ids: tuple[str, ...]) -> tuple[np.ndarray, np.ndarray]:
    """Open final test answers and verify they align with sealed feature rows."""
    resource_ids: list[str] = []
    actual_ratios: list[float] = []
    dispatched_kw: list[float] = []
    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"resource_id", "dataset_split", TARGET_COLUMN, EVALUATION_DISPATCH_COLUMN}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"holdout source is missing columns: {sorted(missing)}")
        for row_number, row in enumerate(reader, start=2):
            if row["dataset_split"].strip() != "test":
                continue
            try:
                ratio = float(row[TARGET_COLUMN])
                dispatch = float(row[EVALUATION_DISPATCH_COLUMN])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"row {row_number}: invalid test outcome") from exc
            if not isfinite(ratio) or not 0.0 <= ratio <= 1.0:
                raise ValueError(f"row {row_number}: test ratio must be within 0..1")
            if not isfinite(dispatch) or dispatch < 0.0:
                raise ValueError(f"row {row_number}: test dispatch must be non-negative")
            resource_ids.append(row["resource_id"].strip())
            actual_ratios.append(ratio)
            dispatched_kw.append(dispatch)
    if tuple(resource_ids) != expected_resource_ids:
        raise ValueError("test outcomes do not align with the sealed feature rows")
    return np.asarray(actual_ratios, dtype=float), np.asarray(dispatched_kw, dtype=float)


def _baseline_predictions(data) -> np.ndarray:
    prior_index = data.feature_names.index("prior_delivery_ratio_mean")
    count_index = data.feature_names.index("prior_event_count")
    global_train_mean = fmean(data.train.targets or ())
    return np.asarray([
        global_train_mean if row[count_index] == 0 else row[prior_index]
        for row in data.test.features
    ], dtype=float)


def evaluate_predictions(actual: np.ndarray, dispatch: np.ndarray, expected: np.ndarray, trusted: np.ndarray, baseline: np.ndarray, config: dict) -> dict:
    """Calculate final metrics and apply rules declared before opening the holdout."""
    if not (len(actual) == len(dispatch) == len(expected) == len(trusted) == len(baseline)) or not len(actual):
        raise ValueError("all final evaluation arrays must be non-empty and aligned")
    expected_metrics = _calculate_metrics(actual, expected, dispatch)
    trusted_metrics = _calculate_metrics(actual, trusted, dispatch)
    baseline_metrics = _calculate_metrics(actual, baseline, dispatch)
    policy = config["safety_policy"]
    thresholds = policy["dispatch_group_thresholds_kw"]
    max_over_rate = float(policy["maximum_allowed_overprediction_rate_percent"])
    tolerance = 1e-12
    masks = {
        "small": dispatch <= float(thresholds["small_max"]),
        "medium": (dispatch > float(thresholds["small_max"])) & (dispatch <= float(thresholds["medium_max"])),
        "large": dispatch > float(thresholds["medium_max"]),
    }
    group_results = {}
    for name, mask in masks.items():
        if not np.any(mask):
            raise ValueError(f"final test dispatch group {name!r} is empty")
        rate = 100.0 * float(np.mean(trusted[mask] > actual[mask] + tolerance))
        group_results[name] = {
            "row_count": int(np.sum(mask)),
            "overprediction_rate_percent": round(rate, 6),
            "maximum_allowed_percent": max_over_rate,
            "passes": rate <= max_over_rate + 1e-9,
        }
    overall_rate = 100.0 * float(np.mean(trusted > actual + tolerance))
    mean_expected_kw = float(np.mean(expected * dispatch))
    mean_trusted_kw = float(np.mean(trusted * dispatch))
    retained = 100.0 * mean_trusted_kw / mean_expected_kw if mean_expected_kw else 0.0
    checks = {
        "expected_mae_ratio_beats_baseline": float(expected_metrics["mae_ratio"]) < float(baseline_metrics["mae_ratio"]),
        "expected_mae_kw_beats_baseline": float(expected_metrics["mae_kw"]) < float(baseline_metrics["mae_kw"]),
        "expected_predictions_within_zero_and_one": expected_metrics["prediction_bound_violations"] == 0,
        "trusted_predictions_never_exceed_expected": bool(np.all(trusted <= expected + tolerance)),
        "all_dispatch_groups_pass_overprediction_limit": all(group["passes"] for group in group_results.values()),
        "overall_passes_overprediction_limit": overall_rate <= max_over_rate + 1e-9,
        "trusted_kw_retention_passes_floor": retained >= float(policy["minimum_required_retention_percent"]),
    }
    return {
        "row_count": int(len(actual)),
        "baseline_metrics": baseline_metrics,
        "expected_metrics": expected_metrics,
        "trusted_metrics": trusted_metrics,
        "safety": {
            "coverage_target": float(policy["coverage_target"]),
            "overall_overprediction_rate_percent": round(overall_rate, 6),
            "maximum_allowed_overprediction_rate_percent": max_over_rate,
            "mean_expected_kw": round(mean_expected_kw, 6),
            "mean_trusted_kw": round(mean_trusted_kw, 6),
            "trusted_kw_retained_percent_of_expected": round(retained, 6),
            "minimum_required_retention_percent": float(policy["minimum_required_retention_percent"]),
            "dispatch_groups": group_results,
        },
        "acceptance_checks": checks,
        "accepted": all(checks.values()),
    }


def run_final_evaluation(input_path: Path = DEFAULT_INPUT_PATH, config_path: Path = DEFAULT_CONFIG_PATH, report_path: Path = DEFAULT_REPORT_PATH, model_path: Path = DEFAULT_MODEL_PATH) -> dict:
    if report_path.exists():
        raise FileExistsError("final holdout report already exists; refusing to evaluate twice")
    with config_path.open(encoding="utf-8") as handle:
        config = json.load(handle)
    _verify_locked_inputs(config, input_path, config_path)
    data = load_ev_training_data(input_path)
    model = RandomForestRegressor(**config["model"]["parameters"])
    model.fit(data.train.features, data.train.targets)

    # This is the single point where the previously sealed answers are opened.
    actual, dispatch = _load_test_outcomes(input_path, data.test.resource_ids)
    feature_rows = [dict(zip(data.feature_names, row)) for row in data.test.features]
    outputs = predict_flexibility(model, config, feature_rows, dispatch)
    expected = np.asarray([row["expected_ratio"] for row in outputs], dtype=float)
    trusted = np.asarray([row["trusted_ratio"] for row in outputs], dtype=float)
    result = evaluate_predictions(actual, dispatch, expected, trusted, _baseline_predictions(data), config)
    report = {
        "evaluation_version": EVALUATION_VERSION,
        "status": "final_holdout_evaluated_once",
        "locked_config": {"path": str(config_path), "sha256": _sha256(config_path)},
        "input": {"path": str(input_path), "sha256": _sha256(input_path)},
        "holdout": result,
        "decision": "accepted" if result["accepted"] else "rejected",
        "limitations": [
            "The EV records combine ACN session structure with synthetic behaviour.",
            "This is offline evidence and not real Ahmedabad grid validation.",
            "The holdout must not be reused for further tuning after this evaluation.",
        ],
    }
    if result["accepted"]:
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_path)
        report["model_artifact"] = {"saved": True, "path": str(model_path), "sha256": _sha256(model_path)}
    else:
        report["model_artifact"] = {"saved": False, "reason": "candidate failed a locked acceptance rule"}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    args = parser.parse_args()
    report = run_final_evaluation(args.input, args.config, args.report, args.model)
    holdout = report["holdout"]
    print(f"Final decision: {report['decision']}")
    print(f"Expected MAE ratio: {holdout['expected_metrics']['mae_ratio']:.6f}")
    print(f"Trusted overprediction rate: {holdout['safety']['overall_overprediction_rate_percent']:.2f}%")


if __name__ == "__main__":
    main()
