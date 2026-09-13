"""Analyze Random Forest validation errors without opening the EV test set."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence

import numpy as np

from ai_ml.EV_model.load_ev_training_data import (
    DEFAULT_INPUT_PATH,
    EVTrainingData,
    load_ev_training_data,
)
from ai_ml.EV_model.train_ev_random_forest import (
    DEFAULT_BASELINE_PATH,
    MODEL_PARAMETERS,
    MODEL_VERSION,
    _calculate_metrics,
    _load_selected_baseline,
    train_and_evaluate,
)


DEFAULT_OUTPUT_PATH = Path(
    "data/processed/ev_training/ev_random_forest_error_analysis.json"
)
ANALYSIS_VERSION = "ev_random_forest_error_analysis_v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _segment_metrics(
    mask: np.ndarray,
    actual: np.ndarray,
    predicted: np.ndarray,
    dispatched: np.ndarray,
) -> dict[str, float | int | str]:
    if not np.any(mask):
        return {"row_count": 0, "status": "empty"}
    return _calculate_metrics(actual[mask], predicted[mask], dispatched[mask])


def _improvement(baseline: float, model: float) -> float:
    return round(100.0 * (baseline - model) / baseline, 6)


def _history_analysis(
    data: EVTrainingData,
    actual: np.ndarray,
    predicted: np.ndarray,
    dispatched: np.ndarray,
    baseline_report: dict,
) -> dict:
    prior_index = data.feature_names.index("prior_event_count")
    prior_counts = np.asarray(data.validation.features, dtype=float)[:, prior_index]
    masks = {
        "cold_start": prior_counts == 0.0,
        "with_history": prior_counts > 0.0,
    }
    baseline_name = baseline_report["validation_comparison"]["selected_baseline"]
    baseline_segments = baseline_report["baselines"][baseline_name]["validation"]

    result: dict[str, dict] = {}
    for name, mask in masks.items():
        metrics = _segment_metrics(mask, actual, predicted, dispatched)
        baseline = baseline_segments[name]
        metrics["baseline_mae_ratio"] = baseline["mae_ratio"]
        metrics["mae_ratio_improvement_percent"] = _improvement(
            float(baseline["mae_ratio"]), float(metrics["mae_ratio"])
        )
        metrics["baseline_mae_kw"] = baseline["mae_kw"]
        metrics["mae_kw_improvement_percent"] = _improvement(
            float(baseline["mae_kw"]), float(metrics["mae_kw"])
        )
        result[name] = metrics
    return result


def _dispatch_analysis(
    training_dispatch: Sequence[float],
    actual: np.ndarray,
    predicted: np.ndarray,
    validation_dispatch: np.ndarray,
) -> tuple[dict, dict]:
    low_cutoff, high_cutoff = np.quantile(
        np.asarray(training_dispatch, dtype=float), [1.0 / 3.0, 2.0 / 3.0]
    )
    masks = {
        "small": validation_dispatch <= low_cutoff,
        "medium": (validation_dispatch > low_cutoff)
        & (validation_dispatch <= high_cutoff),
        "large": validation_dispatch > high_cutoff,
    }
    segments = {
        name: _segment_metrics(mask, actual, predicted, validation_dispatch)
        for name, mask in masks.items()
    }
    thresholds = {
        "source_split": "train",
        "small_max_kw": round(float(low_cutoff), 6),
        "medium_max_kw": round(float(high_cutoff), 6),
        "rules": {
            "small": "dispatch_kw <= small_max_kw",
            "medium": "small_max_kw < dispatch_kw <= medium_max_kw",
            "large": "dispatch_kw > medium_max_kw",
        },
    }
    return thresholds, segments


def analyze_predictions(
    data: EVTrainingData,
    predictions: Sequence[float],
    baseline_report: dict,
) -> dict:
    """Describe validation errors by history and dispatch size."""

    if data.validation.targets is None:
        raise ValueError("validation targets are required")
    if data.train.evaluation_dispatched_kw is None:
        raise ValueError("training dispatch values are required for fixed segments")
    if data.validation.evaluation_dispatched_kw is None:
        raise ValueError("validation dispatch values are required")
    if data.test.targets is not None or data.test.evaluation_dispatched_kw is not None:
        raise ValueError("test outcomes must remain sealed")

    actual = np.asarray(data.validation.targets, dtype=float)
    predicted = np.asarray(predictions, dtype=float)
    dispatched = np.asarray(data.validation.evaluation_dispatched_kw, dtype=float)
    if len(predicted) != len(actual):
        raise ValueError("prediction count must match validation row count")

    history = _history_analysis(
        data, actual, predicted, dispatched, baseline_report
    )
    dispatch_thresholds, dispatch_segments = _dispatch_analysis(
        data.train.evaluation_dispatched_kw, actual, predicted, dispatched
    )

    ratio_error = predicted - actual
    absolute_ratio_error = np.abs(ratio_error)
    absolute_kw_error = absolute_ratio_error * dispatched
    tolerance = 1e-12
    under_count = int(np.sum(ratio_error < -tolerance))
    over_count = int(np.sum(ratio_error > tolerance))
    equal_count = int(len(ratio_error) - under_count - over_count)

    named_segments = {
        "history.cold_start": history["cold_start"],
        "history.with_history": history["with_history"],
        "dispatch.small": dispatch_segments["small"],
        "dispatch.medium": dispatch_segments["medium"],
        "dispatch.large": dispatch_segments["large"],
    }
    nonempty = {
        name: metrics
        for name, metrics in named_segments.items()
        if metrics.get("row_count", 0) > 0
    }

    return {
        "analysis_version": ANALYSIS_VERSION,
        "model_version": MODEL_VERSION,
        "scope": "Validation-only error analysis on hybrid/synthetic EV behaviour.",
        "model_parameters": MODEL_PARAMETERS,
        "validation_row_count": int(len(actual)),
        "test_holdout": {
            "row_count": data.test.row_count,
            "targets_read": False,
            "status": "sealed",
        },
        "history_segments": history,
        "dispatch_thresholds": dispatch_thresholds,
        "dispatch_segments": dispatch_segments,
        "absolute_error_distribution": {
            "ratio": {
                "median": round(float(np.quantile(absolute_ratio_error, 0.50)), 6),
                "p90": round(float(np.quantile(absolute_ratio_error, 0.90)), 6),
                "p95": round(float(np.quantile(absolute_ratio_error, 0.95)), 6),
                "maximum": round(float(np.max(absolute_ratio_error)), 6),
            },
            "kw": {
                "median": round(float(np.quantile(absolute_kw_error, 0.50)), 6),
                "p90": round(float(np.quantile(absolute_kw_error, 0.90)), 6),
                "p95": round(float(np.quantile(absolute_kw_error, 0.95)), 6),
                "maximum": round(float(np.max(absolute_kw_error)), 6),
            },
        },
        "prediction_direction": {
            "underpredicted_rows": under_count,
            "overpredicted_rows": over_count,
            "equal_rows": equal_count,
        },
        "hardest_segments": {
            "highest_mae_ratio": max(
                nonempty, key=lambda name: float(nonempty[name]["mae_ratio"])
            ),
            "highest_mae_kw": max(
                nonempty, key=lambda name: float(nonempty[name]["mae_kw"])
            ),
        },
        "dispatch_usage_note": (
            "Dispatch kW is used only to group and score predictions after prediction; "
            "it is not a model input."
        ),
    }


def run_analysis(
    input_path: Path = DEFAULT_INPUT_PATH,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> dict:
    data = load_ev_training_data(input_path)
    baseline_name, baseline_metrics = _load_selected_baseline(baseline_path)
    model, _ = train_and_evaluate(
        data,
        baseline_name=baseline_name,
        baseline_metrics=baseline_metrics,
    )
    predictions = model.predict(data.validation.features)

    with baseline_path.open(encoding="utf-8") as handle:
        baseline_report = json.load(handle)
    report = analyze_predictions(data, predictions, baseline_report)
    report["input"] = {"path": str(input_path), "sha256": _sha256(input_path)}
    report["baseline_report"] = {
        "path": str(baseline_path),
        "sha256": _sha256(baseline_path),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    report = run_analysis(args.input, args.baseline, args.output)
    print(f"Wrote EV validation error analysis to {args.output}")
    print(
        "Hardest ratio segment: "
        f"{report['hardest_segments']['highest_mae_ratio']}"
    )
    print("Test outcomes remain sealed.")


if __name__ == "__main__":
    main()

