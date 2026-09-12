"""Tune a small, fixed Random Forest candidate set on EV validation data."""

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
    MODEL_PARAMETERS,
    _calculate_metrics,
    _load_selected_baseline,
)


DEFAULT_OUTPUT_PATH = Path("data/processed/ev_training/ev_random_forest_tuning.json")
TUNING_VERSION = "ev_random_forest_tuning_v1"

# A deliberately small search. The first entry is the Stage 3 control model.
CANDIDATES = (
    {"name": "control", **MODEL_PARAMETERS},
    {"name": "shallower", **MODEL_PARAMETERS, "max_depth": 8},
    {"name": "deeper", **MODEL_PARAMETERS, "max_depth": 16},
    {"name": "unlimited_depth", **MODEL_PARAMETERS, "max_depth": None},
    {"name": "smaller_leaves", **MODEL_PARAMETERS, "min_samples_leaf": 2},
    {"name": "larger_leaves", **MODEL_PARAMETERS, "min_samples_leaf": 10},
    {"name": "half_features", **MODEL_PARAMETERS, "max_features": 0.5},
    {"name": "all_features", **MODEL_PARAMETERS, "max_features": 1.0},
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _improvement(reference: float, candidate: float) -> float:
    return round(100.0 * (reference - candidate) / reference, 6)


def select_candidate(results: Sequence[dict]) -> dict:
    """Select lowest ratio MAE, then kW MAE, then stable candidate name."""

    if not results:
        raise ValueError("at least one tuning result is required")
    return min(
        results,
        key=lambda result: (
            float(result["validation_metrics"]["mae_ratio"]),
            float(result["validation_metrics"]["mae_kw"]),
            str(result["name"]),
        ),
    )


def tune_models(
    data: EVTrainingData,
    *,
    baseline_name: str,
    baseline_metrics: dict[str, float | int],
    candidates: Sequence[dict] = CANDIDATES,
) -> tuple[RandomForestRegressor, dict]:
    """Fit candidates on train and rank them on validation only."""

    if data.train.targets is None or data.validation.targets is None:
        raise ValueError("training and validation targets are required")
    if data.validation.evaluation_dispatched_kw is None:
        raise ValueError("validation dispatch values are required")
    if data.test.targets is not None or data.test.evaluation_dispatched_kw is not None:
        raise ValueError("test outcomes must remain sealed")

    candidate_results: list[dict] = []
    trained_models: dict[str, RandomForestRegressor] = {}
    seen_names: set[str] = set()
    for candidate in candidates:
        name = str(candidate["name"])
        if name in seen_names:
            raise ValueError(f"duplicate candidate name: {name}")
        seen_names.add(name)
        parameters = {key: value for key, value in candidate.items() if key != "name"}
        model = RandomForestRegressor(**parameters)
        model.fit(data.train.features, data.train.targets)
        predictions = model.predict(data.validation.features)
        metrics = _calculate_metrics(
            data.validation.targets,
            predictions,
            data.validation.evaluation_dispatched_kw,
        )
        candidate_results.append(
            {"name": name, "parameters": parameters, "validation_metrics": metrics}
        )
        trained_models[name] = model

    selected = select_candidate(candidate_results)
    selected_name = str(selected["name"])
    selected_model = trained_models[selected_name]
    control = next(
        (result for result in candidate_results if result["name"] == "control"), None
    )
    if control is None:
        raise ValueError("candidate set must contain the Stage 3 control")

    selected_metrics = selected["validation_metrics"]
    control_metrics = control["validation_metrics"]
    feature_importance = sorted(
        zip(data.feature_names, selected_model.feature_importances_),
        key=lambda pair: (-pair[1], pair[0]),
    )
    report = {
        "tuning_version": TUNING_VERSION,
        "scope": "Small fixed Random Forest search on hybrid/synthetic EV validation data.",
        "selection_rule": [
            "lowest validation mae_ratio",
            "lowest validation mae_kw as tie-breaker",
            "candidate name as deterministic final tie-breaker",
        ],
        "candidate_count": len(candidate_results),
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
        "candidates": candidate_results,
        "selected": selected,
        "comparison": {
            "baseline_name": baseline_name,
            "baseline_mae_ratio": float(baseline_metrics["mae_ratio"]),
            "selected_mae_ratio_improvement_percent_vs_baseline": _improvement(
                float(baseline_metrics["mae_ratio"]),
                float(selected_metrics["mae_ratio"]),
            ),
            "baseline_mae_kw": float(baseline_metrics["mae_kw"]),
            "selected_mae_kw_improvement_percent_vs_baseline": _improvement(
                float(baseline_metrics["mae_kw"]),
                float(selected_metrics["mae_kw"]),
            ),
            "control_mae_ratio": float(control_metrics["mae_ratio"]),
            "selected_mae_ratio_improvement_percent_vs_control": _improvement(
                float(control_metrics["mae_ratio"]),
                float(selected_metrics["mae_ratio"]),
            ),
            "control_mae_kw": float(control_metrics["mae_kw"]),
            "selected_mae_kw_improvement_percent_vs_control": _improvement(
                float(control_metrics["mae_kw"]),
                float(selected_metrics["mae_kw"]),
            ),
        },
        "selected_feature_importance": [
            {"feature": name, "importance": round(float(value), 6)}
            for name, value in feature_importance
        ],
        "selection_status": "validation_selected_test_still_sealed",
        "model_artifact_saved": False,
        "model_artifact_note": "Save only after the selected settings receive final holdout evaluation.",
    }
    return selected_model, report


def run_tuning(
    input_path: Path = DEFAULT_INPUT_PATH,
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> dict:
    data = load_ev_training_data(input_path)
    baseline_name, baseline_metrics = _load_selected_baseline(baseline_path)
    _, report = tune_models(
        data,
        baseline_name=baseline_name,
        baseline_metrics=baseline_metrics,
    )
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

    report = run_tuning(args.input, args.baseline, args.output)
    selected = report["selected"]
    print(f"Wrote EV Random Forest tuning report to {args.output}")
    print(
        f"Selected {selected['name']} with validation MAE ratio "
        f"{selected['validation_metrics']['mae_ratio']:.6f}"
    )
    print("Test outcomes remain sealed.")


if __name__ == "__main__":
    main()

