"""Train one deterministic Random Forest for EV delivery-ratio prediction.

This first classical model uses only the training split, evaluates only on the
validation split, and keeps the final test outcomes sealed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence

import numpy as np
import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from ai_ml.EV_model.load_ev_training_data import (
    DEFAULT_INPUT_PATH,
    EVTrainingData,
    load_ev_training_data,
)


DEFAULT_BASELINE_PATH = Path("data/processed/ev_training/ev_baseline_evaluation.json")
DEFAULT_REPORT_PATH = Path(
    "data/processed/ev_training/ev_random_forest_validation.json"
)
MODEL_VERSION = "ev_random_forest_v1"
RANDOM_STATE = 2806

MODEL_PARAMETERS = {
    "n_estimators": 200,
    "max_depth": 12,
    "min_samples_leaf": 5,
    "max_features": "sqrt",
    "random_state": RANDOM_STATE,
    "n_jobs": 1,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_model() -> RandomForestRegressor:
    """Create the fixed first-pass model without hyperparameter tuning."""

    return RandomForestRegressor(**MODEL_PARAMETERS)


def _calculate_metrics(
    actual_ratio: Sequence[float],
    predicted_ratio: Sequence[float],
    dispatched_kw: Sequence[float],
) -> dict[str, float | int]:
    actual = np.asarray(actual_ratio, dtype=float)
    predicted = np.asarray(predicted_ratio, dtype=float)
    dispatched = np.asarray(dispatched_kw, dtype=float)
    if not (len(actual) == len(predicted) == len(dispatched)) or not len(actual):
        raise ValueError("metric arrays must be non-empty and have equal lengths")

    ratio_error = predicted - actual
    kw_error = ratio_error * dispatched
    return {
        "row_count": int(len(actual)),
        "mae_ratio": round(float(mean_absolute_error(actual, predicted)), 6),
        "rmse_ratio": round(float(mean_squared_error(actual, predicted) ** 0.5), 6),
        "bias_ratio": round(float(np.mean(ratio_error)), 6),
        "mean_overestimation_ratio": round(
            float(np.mean(np.maximum(ratio_error, 0.0))), 6
        ),
        "mae_kw": round(float(np.mean(np.abs(kw_error))), 6),
        "rmse_kw": round(float(np.mean(kw_error**2) ** 0.5), 6),
        "bias_kw": round(float(np.mean(kw_error)), 6),
        "mean_overestimation_kw": round(
            float(np.mean(np.maximum(kw_error, 0.0))), 6
        ),
        "prediction_bound_violations": int(
            np.sum((predicted < 0.0) | (predicted > 1.0))
        ),
    }


def _load_selected_baseline(path: Path) -> tuple[str, dict[str, float | int]]:
    with path.open(encoding="utf-8") as handle:
        report = json.load(handle)
    name = report["validation_comparison"]["selected_baseline"]
    metrics = report["baselines"][name]["validation"]["all"]
    return str(name), metrics


def train_and_evaluate(
    data: EVTrainingData,
    *,
    baseline_name: str,
    baseline_metrics: dict[str, float | int],
) -> tuple[RandomForestRegressor, dict]:
    """Fit on train, evaluate on validation, and never use test outcomes."""

    if data.train.targets is None or data.validation.targets is None:
        raise ValueError("training and validation targets are required")
    if data.validation.evaluation_dispatched_kw is None:
        raise ValueError("validation dispatch values are required for kW metrics")
    if data.test.targets is not None or data.test.evaluation_dispatched_kw is not None:
        raise ValueError("test outcomes must remain sealed")

    model = build_model()
    model.fit(data.train.features, data.train.targets)
    predictions = model.predict(data.validation.features)
    metrics = _calculate_metrics(
        data.validation.targets,
        predictions,
        data.validation.evaluation_dispatched_kw,
    )

    importance_pairs = sorted(
        zip(data.feature_names, model.feature_importances_),
        key=lambda pair: (-pair[1], pair[0]),
    )
    feature_importance = [
        {"feature": name, "importance": round(float(importance), 6)}
        for name, importance in importance_pairs
    ]

    baseline_mae_ratio = float(baseline_metrics["mae_ratio"])
    baseline_mae_kw = float(baseline_metrics["mae_kw"])
    model_mae_ratio = float(metrics["mae_ratio"])
    model_mae_kw = float(metrics["mae_kw"])

    report = {
        "model_version": MODEL_VERSION,
        "scope": "First untuned classical model on hybrid/synthetic EV behaviour; not real-world validation.",
        "algorithm": "RandomForestRegressor",
        "parameters": MODEL_PARAMETERS,
        "library_versions": {
            "scikit_learn": sklearn.__version__,
            "numpy": np.__version__,
        },
        "feature_count": len(data.feature_names),
        "feature_names": list(data.feature_names),
        "missing_value_handling": {
            "method": "median",
            "fit_split": "train",
        },
        "split_usage": {
            "training": {"row_count": data.train.row_count, "targets_read": True},
            "validation": {
                "row_count": data.validation.row_count,
                "targets_read": True,
            },
            "test": {
                "row_count": data.test.row_count,
                "targets_read": False,
                "status": "sealed",
            },
        },
        "validation_metrics": metrics,
        "baseline_comparison": {
            "baseline": baseline_name,
            "baseline_mae_ratio": baseline_mae_ratio,
            "model_mae_ratio": model_mae_ratio,
            "mae_ratio_improvement_percent": round(
                100.0 * (baseline_mae_ratio - model_mae_ratio) / baseline_mae_ratio,
                6,
            ),
            "baseline_mae_kw": baseline_mae_kw,
            "model_mae_kw": model_mae_kw,
            "mae_kw_improvement_percent": round(
                100.0 * (baseline_mae_kw - model_mae_kw) / baseline_mae_kw,
                6,
            ),
        },
        "feature_importance": feature_importance,
        "selection_status": "validation_only",
        "model_artifact_saved": False,
        "model_artifact_note": "Save a model artifact only after validation review and model selection.",
    }
    return model, report


def write_report(report: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )


def run_training(
    input_path: Path = DEFAULT_INPUT_PATH,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
) -> dict:
    data = load_ev_training_data(input_path)
    baseline_name, baseline_metrics = _load_selected_baseline(baseline_path)
    _, report = train_and_evaluate(
        data,
        baseline_name=baseline_name,
        baseline_metrics=baseline_metrics,
    )
    report["input"] = {"path": str(input_path), "sha256": _sha256(input_path)}
    report["baseline_report"] = {
        "path": str(baseline_path),
        "sha256": _sha256(baseline_path),
    }
    write_report(report, report_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    args = parser.parse_args()

    report = run_training(args.input, args.baseline, args.output)
    comparison = report["baseline_comparison"]
    print(f"Wrote validation report to {args.output}")
    print(
        "Validation MAE ratio: "
        f"{report['validation_metrics']['mae_ratio']:.6f} "
        f"({comparison['mae_ratio_improvement_percent']:.2f}% vs baseline)"
    )
    print("Test outcomes remain sealed.")


if __name__ == "__main__":
    main()

