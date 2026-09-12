"""Compare fixed EV safety levels on validation data while sealing test outcomes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence

from sklearn.ensemble import RandomForestRegressor

from ai_ml.EV_model.calibrate_ev_safety import calibrate_predictions
from ai_ml.EV_model.load_ev_training_data import DEFAULT_INPUT_PATH, load_ev_training_data
from ai_ml.EV_model.train_ev_random_forest import DEFAULT_BASELINE_PATH, _load_selected_baseline
from ai_ml.EV_model.tune_ev_random_forest import DEFAULT_OUTPUT_PATH as DEFAULT_TUNING_PATH


DEFAULT_OUTPUT_PATH = Path("data/processed/ev_training/ev_random_forest_safety_tradeoff.json")
COMPARISON_VERSION = "ev_random_forest_safety_tradeoff_v1"
COVERAGE_CANDIDATES = (0.80, 0.85, 0.90)
MIN_TRUSTED_KW_RETENTION_PERCENT = 50.0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def select_safety_level(results: Sequence[dict], minimum_retention_percent: float = MIN_TRUSTED_KW_RETENTION_PERCENT) -> dict | None:
    """Choose the safest result that passes risk and the usefulness floor."""
    eligible = [result for result in results if result["risk_rule_passed"] and result["trusted_kw_retained_percent_of_expected"] >= minimum_retention_percent]
    return max(eligible, key=lambda item: float(item["coverage_target"])) if eligible else None


def compare_safety_levels(data, expected_predictions: Sequence[float], *, baseline_metrics: dict[str, float | int], coverage_candidates: Sequence[float] = COVERAGE_CANDIDATES, minimum_retention_percent: float = MIN_TRUSTED_KW_RETENTION_PERCENT) -> dict:
    """Measure trade-offs and select with a rule declared before evaluation."""
    results: list[dict] = []
    for coverage_target in coverage_candidates:
        calibration = calibrate_predictions(data, expected_predictions, baseline_metrics=baseline_metrics, coverage_target=float(coverage_target))
        validation = calibration["validation"]
        results.append({
            "coverage_target": float(coverage_target),
            "maximum_allowed_overprediction_rate_percent": round(100.0 * (1.0 - float(coverage_target)), 6),
            "actual_overprediction_rate_percent": validation["trusted_overprediction_rate_percent"],
            "mean_expected_kw": validation["mean_expected_kw"],
            "mean_trusted_kw": validation["mean_trusted_kw"],
            "trusted_kw_retained_percent_of_expected": validation["trusted_kw_retained_percent_of_expected"],
            "trusted_mae_ratio": validation["trusted_metrics"]["mae_ratio"],
            "trusted_mae_kw": validation["trusted_metrics"]["mae_kw"],
            "dispatch_group_safety": calibration["dispatch_group_safety"],
            "risk_rule_passed": calibration["risk_rule_passed"],
        })
    selected = select_safety_level(results, minimum_retention_percent)
    return {
        "comparison_version": COMPARISON_VERSION,
        "scope": "Validation-only comparison of fixed EV safety levels.",
        "coverage_candidates": [float(value) for value in coverage_candidates],
        "selection_rule": {"minimum_trusted_kw_retention_percent": minimum_retention_percent, "then_choose": "highest coverage target among eligible levels", "status": "hackathon working assumption; adjustable before final evaluation"},
        "results": results,
        "selected": selected,
        "selection_status": "selected_on_validation_test_still_sealed" if selected is not None else "no_candidate_met_usefulness_floor_test_still_sealed",
        "test_holdout": {"row_count": data.test.row_count, "targets_read": False, "status": "sealed"},
        "limitations": ["Safety margins were calibrated and measured on the same validation split.", "The 50% retained-kW floor is a working product choice, not a grid standard.", "Results describe hybrid/synthetic EV behaviour, not real Ahmedabad reliability."],
    }


def run_comparison(input_path: Path = DEFAULT_INPUT_PATH, baseline_path: Path = DEFAULT_BASELINE_PATH, tuning_path: Path = DEFAULT_TUNING_PATH, output_path: Path = DEFAULT_OUTPUT_PATH) -> dict:
    data = load_ev_training_data(input_path)
    _, baseline_metrics = _load_selected_baseline(baseline_path)
    with tuning_path.open(encoding="utf-8") as handle:
        tuning_report = json.load(handle)
    parameters = tuning_report["selected"]["parameters"]
    if data.train.targets is None:
        raise ValueError("training targets are required")
    model = RandomForestRegressor(**parameters)
    model.fit(data.train.features, data.train.targets)
    report = compare_safety_levels(data, model.predict(data.validation.features), baseline_metrics=baseline_metrics)
    report["selected_model"] = {"name": tuning_report["selected"]["name"], "parameters": parameters}
    report["inputs"] = {
        "training_table": {"path": str(input_path), "sha256": _sha256(input_path)},
        "baseline_report": {"path": str(baseline_path), "sha256": _sha256(baseline_path)},
        "tuning_report": {"path": str(tuning_path), "sha256": _sha256(tuning_path)},
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--tuning", type=Path, default=DEFAULT_TUNING_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()
    report = run_comparison(args.input, args.baseline, args.tuning, args.output)
    selected = report["selected"]
    print("No safety level passed the usefulness floor." if selected is None else f"Selected coverage target: {selected['coverage_target']:.0%}")
    print(f"Wrote EV safety trade-off report to {args.output}")
    print("Test outcomes remain sealed.")


if __name__ == "__main__":
    main()
