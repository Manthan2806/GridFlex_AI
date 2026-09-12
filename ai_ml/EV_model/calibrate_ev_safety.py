"""Calibrate conservative EV trusted predictions on validation data only."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence

import numpy as np
from sklearn.ensemble import RandomForestRegressor

from ai_ml.EV_model.load_ev_training_data import (
    DEFAULT_INPUT_PATH,
    EVTrainingData,
    load_ev_training_data,
)
from ai_ml.EV_model.train_ev_random_forest import (
    DEFAULT_BASELINE_PATH,
    _calculate_metrics,
    _load_selected_baseline,
)
from ai_ml.EV_model.tune_ev_random_forest import DEFAULT_OUTPUT_PATH as DEFAULT_TUNING_PATH


DEFAULT_OUTPUT_PATH = Path(
    "data/processed/ev_training/ev_random_forest_safety_calibration.json"
)
CALIBRATION_VERSION = "ev_random_forest_safety_v1"
TARGET_COVERAGE = 0.90
MAX_OVERPREDICTION_RATE_PERCENT = 100.0 * (1.0 - TARGET_COVERAGE)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dispatch_thresholds(training_dispatch: Sequence[float]) -> tuple[float, float]:
    values = np.asarray(training_dispatch, dtype=float)
    if not len(values):
        raise ValueError("training dispatch values cannot be empty")
    low, high = np.quantile(values, [1.0 / 3.0, 2.0 / 3.0])
    return float(low), float(high)


def _dispatch_groups(dispatch: np.ndarray, low: float, high: float) -> dict[str, np.ndarray]:
    return {
        "small": dispatch <= low,
        "medium": (dispatch > low) & (dispatch <= high),
        "large": dispatch > high,
    }


def _safety_margin(
    actual: np.ndarray,
    predicted: np.ndarray,
    coverage_target: float = TARGET_COVERAGE,
) -> float:
    """Return a non-negative margin targeting the requested lower-bound coverage."""

    if not len(actual) or len(actual) != len(predicted):
        raise ValueError("actual and predicted arrays must be non-empty and aligned")
    if not 0.0 < coverage_target < 1.0:
        raise ValueError("coverage target must be between zero and one")
    signed_overprediction = predicted - actual
    return max(
        0.0,
        float(np.quantile(signed_overprediction, coverage_target, method="higher")),
    )


def calibrate_predictions(
    data: EVTrainingData,
    expected_predictions: Sequence[float],
    *,
    baseline_metrics: dict[str, float | int],
    coverage_target: float = TARGET_COVERAGE,
) -> dict:
    """Create dispatch-specific trusted predictions and an acceptance report."""

    if data.validation.targets is None:
        raise ValueError("validation targets are required")
    if data.train.evaluation_dispatched_kw is None:
        raise ValueError("training dispatch values are required")
    if data.validation.evaluation_dispatched_kw is None:
        raise ValueError("validation dispatch values are required")
    if data.test.targets is not None or data.test.evaluation_dispatched_kw is not None:
        raise ValueError("test outcomes must remain sealed")

    actual = np.asarray(data.validation.targets, dtype=float)
    expected = np.asarray(expected_predictions, dtype=float)
    dispatch = np.asarray(data.validation.evaluation_dispatched_kw, dtype=float)
    if len(expected) != len(actual):
        raise ValueError("prediction count must match validation row count")
    if not 0.0 < coverage_target < 1.0:
        raise ValueError("coverage target must be between zero and one")

    max_overprediction_rate_percent = 100.0 * (1.0 - coverage_target)

    low, high = _dispatch_thresholds(data.train.evaluation_dispatched_kw)
    groups = _dispatch_groups(dispatch, low, high)
    trusted = expected.copy()
    group_report: dict[str, dict] = {}
    tolerance = 1e-12

    for name, mask in groups.items():
        if not np.any(mask):
            raise ValueError(f"validation dispatch group {name!r} is empty")
        margin = _safety_margin(actual[mask], expected[mask], coverage_target)
        trusted[mask] = np.clip(expected[mask] - margin, 0.0, 1.0)
        over_rate = 100.0 * float(np.mean(trusted[mask] > actual[mask] + tolerance))
        group_report[name] = {
            "row_count": int(np.sum(mask)),
            "safety_margin_ratio": round(margin, 6),
            "overprediction_rate_percent": round(over_rate, 6),
            "target_max_overprediction_rate_percent": round(
                max_overprediction_rate_percent, 6
            ),
            "passes_risk_limit": over_rate <= max_overprediction_rate_percent + 1e-9,
        }

    expected_metrics = _calculate_metrics(actual, expected, dispatch)
    trusted_metrics = _calculate_metrics(actual, trusted, dispatch)
    overall_over_rate = 100.0 * float(np.mean(trusted > actual + tolerance))
    average_ratio_reduction = float(np.mean(expected - trusted))
    average_kw_reduction = float(np.mean((expected - trusted) * dispatch))
    mean_expected_ratio = float(np.mean(expected))
    mean_trusted_ratio = float(np.mean(trusted))
    mean_expected_kw = float(np.mean(expected * dispatch))
    mean_trusted_kw = float(np.mean(trusted * dispatch))
    retained_expected_kw_percent = (
        100.0 * mean_trusted_kw / mean_expected_kw if mean_expected_kw else 0.0
    )

    checks = {
        "expected_mae_ratio_beats_baseline": (
            float(expected_metrics["mae_ratio"]) < float(baseline_metrics["mae_ratio"])
        ),
        "expected_mae_kw_beats_baseline": (
            float(expected_metrics["mae_kw"]) < float(baseline_metrics["mae_kw"])
        ),
        "expected_predictions_within_zero_and_one": (
            expected_metrics["prediction_bound_violations"] == 0
        ),
        "trusted_predictions_never_exceed_expected": bool(
            np.all(trusted <= expected + tolerance)
        ),
        "all_dispatch_groups_pass_risk_limit": all(
            group["passes_risk_limit"] for group in group_report.values()
        ),
        "overall_passes_risk_limit": (
            overall_over_rate <= max_overprediction_rate_percent + 1e-9
        ),
        "test_targets_remain_sealed": True,
    }

    return {
        "calibration_version": CALIBRATION_VERSION,
        "scope": "Validation-calibrated safety margin on hybrid/synthetic EV behaviour.",
        "definitions": {
            "expected_ratio": "Raw tuned Random Forest delivery-ratio prediction.",
            "trusted_ratio": "Expected ratio minus its dispatch-group safety margin, clipped to 0..1.",
            "expected_kw": "dispatch_kw multiplied by expected_ratio.",
            "trusted_kw": "dispatch_kw multiplied by trusted_ratio.",
        },
        "coverage_target": coverage_target,
        "calibration_split": "validation",
        "calibration_and_measurement_share_same_split": True,
        "dispatch_thresholds": {
            "source_split": "train",
            "small_max_kw": round(low, 6),
            "medium_max_kw": round(high, 6),
        },
        "dispatch_group_safety": group_report,
        "validation": {
            "row_count": int(len(actual)),
            "expected_metrics": expected_metrics,
            "trusted_metrics": trusted_metrics,
            "trusted_overprediction_rate_percent": round(overall_over_rate, 6),
            "average_safety_reduction_ratio": round(average_ratio_reduction, 6),
            "average_safety_reduction_kw": round(average_kw_reduction, 6),
            "mean_expected_ratio": round(mean_expected_ratio, 6),
            "mean_trusted_ratio": round(mean_trusted_ratio, 6),
            "mean_expected_kw": round(mean_expected_kw, 6),
            "mean_trusted_kw": round(mean_trusted_kw, 6),
            "trusted_kw_retained_percent_of_expected": round(
                retained_expected_kw_percent, 6
            ),
        },
        "acceptance_checks": checks,
        "risk_rule_passed": all(checks.values()),
        "provisional_acceptance": False,
        "decision_status": "risk_target_met_but_usefulness_review_required",
        "decision_reason": (
            f"The {coverage_target:.0%} per-session rule is technically satisfied, but it removes a "
            "large share of expected kW. A portfolio-level safety rule or a chosen "
            "business trade-off is required before final test evaluation."
        ),
        "test_holdout": {
            "row_count": data.test.row_count,
            "targets_read": False,
            "status": "sealed",
        },
        "limitations": [
            "Safety margins were calibrated and measured on the same validation split.",
            "Coverage must be checked once on the untouched test split before final acceptance.",
            "Results describe hybrid/synthetic EV behaviour, not real Ahmedabad reliability.",
        ],
    }


def run_calibration(
    input_path: Path = DEFAULT_INPUT_PATH,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    tuning_path: Path = DEFAULT_TUNING_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> dict:
    data = load_ev_training_data(input_path)
    _, baseline_metrics = _load_selected_baseline(baseline_path)
    with tuning_path.open(encoding="utf-8") as handle:
        tuning_report = json.load(handle)
    parameters = tuning_report["selected"]["parameters"]

    model = RandomForestRegressor(**parameters)
    if data.train.targets is None:
        raise ValueError("training targets are required")
    model.fit(data.train.features, data.train.targets)
    expected_predictions = model.predict(data.validation.features)
    report = calibrate_predictions(
        data, expected_predictions, baseline_metrics=baseline_metrics
    )
    report["selected_model"] = {
        "name": tuning_report["selected"]["name"],
        "parameters": parameters,
    }
    report["inputs"] = {
        "training_table": {"path": str(input_path), "sha256": _sha256(input_path)},
        "baseline_report": {
            "path": str(baseline_path),
            "sha256": _sha256(baseline_path),
        },
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

    report = run_calibration(args.input, args.baseline, args.tuning, args.output)
    print(f"Wrote EV safety calibration to {args.output}")
    print(f"Provisional acceptance: {report['provisional_acceptance']}")
    print("Test outcomes remain sealed.")


if __name__ == "__main__":
    main()
