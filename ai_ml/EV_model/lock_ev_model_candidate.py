"""Lock the selected EV model recipe before final holdout evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ai_ml.EV_model.calibrate_ev_safety import _dispatch_thresholds
from ai_ml.EV_model.load_ev_training_data import DEFAULT_INPUT_PATH, EVTrainingData, IMPUTABLE_FEATURE_COLUMNS, load_ev_training_data
from ai_ml.EV_model.compare_ev_safety_levels import DEFAULT_OUTPUT_PATH as DEFAULT_TRADEOFF_PATH
from ai_ml.EV_model.tune_ev_random_forest import DEFAULT_OUTPUT_PATH as DEFAULT_TUNING_PATH


DEFAULT_OUTPUT_PATH = Path("data/processed/ev_training/ev_model_candidate_config.json")
CANDIDATE_VERSION = "ev_model_candidate_v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_candidate_config(data: EVTrainingData, tuning_report: dict, tradeoff_report: dict) -> dict:
    """Build an immutable candidate recipe without reading test outcomes."""
    if data.test.targets is not None or data.test.evaluation_dispatched_kw is not None:
        raise ValueError("test outcomes must remain sealed")
    selected_model = tuning_report.get("selected")
    selected_safety = tradeoff_report.get("selected")
    if not selected_model or not selected_safety:
        raise ValueError("model and safety selections must exist")
    if not selected_safety.get("risk_rule_passed"):
        raise ValueError("selected safety level must pass its risk rule")
    tradeoff_model = tradeoff_report.get("selected_model")
    if tradeoff_model != {
        "name": selected_model["name"],
        "parameters": selected_model["parameters"],
    }:
        raise ValueError("tuning and safety reports must select the same model")
    minimum_retention = float(tradeoff_report["selection_rule"]["minimum_trusted_kw_retention_percent"])
    retained = float(selected_safety["trusted_kw_retained_percent_of_expected"])
    if retained < minimum_retention:
        raise ValueError("selected safety level must pass the usefulness floor")
    if data.train.evaluation_dispatched_kw is None:
        raise ValueError("training dispatch values are required")

    low, high = _dispatch_thresholds(data.train.evaluation_dispatched_kw)
    margins = {
        group: float(selected_safety["dispatch_group_safety"][group]["safety_margin_ratio"])
        for group in ("small", "medium", "large")
    }
    return {
        "candidate_version": CANDIDATE_VERSION,
        "status": "locked_before_final_holdout_evaluation",
        "model": {
            "family": "RandomForestRegressor",
            "selected_name": selected_model["name"],
            "parameters": selected_model["parameters"],
            "fit_split": "train",
        },
        "feature_contract": {
            "names_in_order": list(data.feature_names),
            "imputation_medians": {
                name: value for name, value in zip(data.feature_names, data.imputation_medians)
            },
            "features_allowed_to_be_missing": sorted(IMPUTABLE_FEATURE_COLUMNS),
        },
        "safety_policy": {
            "coverage_target": float(selected_safety["coverage_target"]),
            "maximum_allowed_overprediction_rate_percent": float(selected_safety["maximum_allowed_overprediction_rate_percent"]),
            "dispatch_group_thresholds_kw": {"small_max": low, "medium_max": high},
            "margin_ratio_by_dispatch_group": margins,
            "validation_trusted_kw_retained_percent": retained,
            "minimum_required_retention_percent": minimum_retention,
        },
        "output_contract": {
            "expected_ratio": "raw model prediction clipped to 0..1",
            "trusted_ratio": "expected ratio minus the selected safety margin, clipped to 0..1",
            "expected_kw": "requested dispatch kW multiplied by expected ratio",
            "trusted_kw": "requested dispatch kW multiplied by trusted ratio",
        },
        "test_holdout": {"row_count": data.test.row_count, "targets_read": False, "status": "sealed"},
        "model_artifact_saved": False,
        "next_gate": "one-time evaluation on the untouched test split",
    }


def run_lock(input_path: Path = DEFAULT_INPUT_PATH, tuning_path: Path = DEFAULT_TUNING_PATH, tradeoff_path: Path = DEFAULT_TRADEOFF_PATH, output_path: Path = DEFAULT_OUTPUT_PATH) -> dict:
    data = load_ev_training_data(input_path)
    with tuning_path.open(encoding="utf-8") as handle:
        tuning_report = json.load(handle)
    with tradeoff_path.open(encoding="utf-8") as handle:
        tradeoff_report = json.load(handle)
    input_hash = _sha256(input_path)
    tuning_hash = _sha256(tuning_path)
    if tuning_report.get("input", {}).get("sha256") != input_hash:
        raise ValueError("tuning report does not match the current training table")
    if tradeoff_report.get("inputs", {}).get("training_table", {}).get("sha256") != input_hash:
        raise ValueError("safety report does not match the current training table")
    if tradeoff_report.get("inputs", {}).get("tuning_report", {}).get("sha256") != tuning_hash:
        raise ValueError("safety report does not match the current tuning report")
    config = build_candidate_config(data, tuning_report, tradeoff_report)
    config["inputs"] = {
        "training_table": {"path": str(input_path), "sha256": input_hash},
        "tuning_report": {"path": str(tuning_path), "sha256": tuning_hash},
        "safety_tradeoff_report": {"path": str(tradeoff_path), "sha256": _sha256(tradeoff_path)},
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--tuning", type=Path, default=DEFAULT_TUNING_PATH)
    parser.add_argument("--tradeoff", type=Path, default=DEFAULT_TRADEOFF_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()
    config = run_lock(args.input, args.tuning, args.tradeoff, args.output)
    print(f"Locked EV candidate at {args.output}")
    print(f"Safety coverage: {config['safety_policy']['coverage_target']:.0%}")
    print("Test outcomes remain sealed.")


if __name__ == "__main__":
    main()
