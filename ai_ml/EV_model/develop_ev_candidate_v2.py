"""Develop and lock EV candidate v2 without reading any test outcomes.

The existing validation resources are deterministically divided into disjoint
model-selection and safety-calibration subsets. Candidate v1 files are never
modified by this module.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from math import ceil
from pathlib import Path
from typing import Callable, Sequence

import numpy as np
import sklearn
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor

from ai_ml.EV_model.evidence import canonical_sha256
from ai_ml.EV_model.load_ev_training_data import DEFAULT_INPUT_PATH, EVSplit, EVTrainingData, load_ev_training_data
from ai_ml.EV_model.train_ev_random_forest import _calculate_metrics


V2_DIR = Path("data/processed/ev_training/v2")
DEFAULT_REPORT_PATH = V2_DIR / "ev_candidate_v2_development.json"
DEFAULT_CONFIG_PATH = V2_DIR / "ev_candidate_v2_config.json"
CANDIDATE_VERSION = "ev_model_candidate_v2"
RANDOM_STATE = 2810
CALIBRATION_COVERAGE = 0.875
MAX_FINAL_OVERPREDICTION_PERCENT = 15.0
MINIMUM_RETENTION_PERCENT = 50.0


@dataclass(frozen=True)
class Candidate:
    name: str
    family: str
    parameters: dict
    factory: Callable[[], object]


def model_candidates() -> tuple[Candidate, ...]:
    return (
        Candidate(
            "random_forest_balanced",
            "RandomForestRegressor",
            {
                "n_estimators": 300,
                "max_depth": 10,
                "min_samples_leaf": 6,
                "max_features": 0.75,
                "random_state": RANDOM_STATE,
                "n_jobs": 1,
            },
            lambda: RandomForestRegressor(
                n_estimators=300,
                max_depth=10,
                min_samples_leaf=6,
                max_features=0.75,
                random_state=RANDOM_STATE,
                n_jobs=1,
            ),
        ),
        Candidate(
            "extra_trees_regularized",
            "ExtraTreesRegressor",
            {
                "n_estimators": 300,
                "max_depth": 12,
                "min_samples_leaf": 6,
                "max_features": 0.75,
                "random_state": RANDOM_STATE,
                "n_jobs": 1,
            },
            lambda: ExtraTreesRegressor(
                n_estimators=300,
                max_depth=12,
                min_samples_leaf=6,
                max_features=0.75,
                random_state=RANDOM_STATE,
                n_jobs=1,
            ),
        ),
        Candidate(
            "hist_gradient_boosting",
            "HistGradientBoostingRegressor",
            {
                "learning_rate": 0.05,
                "max_iter": 200,
                "max_leaf_nodes": 15,
                "min_samples_leaf": 20,
                "l2_regularization": 1.0,
                "random_state": RANDOM_STATE,
            },
            lambda: HistGradientBoostingRegressor(
                learning_rate=0.05,
                max_iter=200,
                max_leaf_nodes=15,
                min_samples_leaf=20,
                l2_regularization=1.0,
                random_state=RANDOM_STATE,
            ),
        ),
    )


def lower_bound_candidates() -> tuple[Candidate, ...]:
    """Conditional lower-tail models considered for trusted flexibility."""
    return tuple(
        Candidate(
            f"hist_gradient_quantile_{quantile:g}",
            "HistGradientBoostingRegressor",
            {
                "loss": "quantile",
                "quantile": quantile,
                "learning_rate": 0.05,
                "max_iter": 200,
                "max_leaf_nodes": 15,
                "min_samples_leaf": 20,
                "l2_regularization": 1.0,
                "random_state": RANDOM_STATE,
            },
            lambda quantile=quantile: HistGradientBoostingRegressor(
                loss="quantile",
                quantile=quantile,
                learning_rate=0.05,
                max_iter=200,
                max_leaf_nodes=15,
                min_samples_leaf=20,
                l2_regularization=1.0,
                random_state=RANDOM_STATE,
            ),
        )
        for quantile in (0.10, 0.125, 0.15, 0.175)
    )


def build_model(family: str, parameters: dict):
    factories = {
        "RandomForestRegressor": RandomForestRegressor,
        "ExtraTreesRegressor": ExtraTreesRegressor,
        "HistGradientBoostingRegressor": HistGradientBoostingRegressor,
    }
    if family not in factories:
        raise ValueError(f"unsupported model family: {family}")
    return factories[family](**parameters)


def _resource_partition(resource_id: str) -> str:
    digest = hashlib.sha256(resource_id.encode("utf-8")).digest()
    return "selection" if digest[0] % 2 == 0 else "calibration"


def _subset(split: EVSplit, indices: Sequence[int]) -> EVSplit:
    if split.targets is None or split.evaluation_dispatched_kw is None:
        raise ValueError("development subsets require visible outcomes")
    return EVSplit(
        resource_ids=tuple(split.resource_ids[index] for index in indices),
        features=tuple(split.features[index] for index in indices),
        targets=tuple(split.targets[index] for index in indices),
        evaluation_dispatched_kw=tuple(
            split.evaluation_dispatched_kw[index] for index in indices
        ),
    )


def split_validation_by_resource(validation: EVSplit) -> tuple[EVSplit, EVSplit]:
    """Create disjoint deterministic selection and calibration resources."""
    selection_indices = [
        index
        for index, resource_id in enumerate(validation.resource_ids)
        if _resource_partition(resource_id) == "selection"
    ]
    calibration_indices = [
        index
        for index, resource_id in enumerate(validation.resource_ids)
        if _resource_partition(resource_id) == "calibration"
    ]
    if not selection_indices or not calibration_indices:
        raise ValueError("validation resource partition produced an empty subset")
    selection = _subset(validation, selection_indices)
    calibration = _subset(validation, calibration_indices)
    if set(selection.resource_ids) & set(calibration.resource_ids):
        raise AssertionError("selection and calibration resources overlap")
    return selection, calibration


def _baseline_predictions(data: EVTrainingData, split: EVSplit) -> np.ndarray:
    if data.train.targets is None:
        raise ValueError("training targets are required")
    prior_index = data.feature_names.index("prior_delivery_ratio_mean")
    count_index = data.feature_names.index("prior_event_count")
    global_mean = float(np.mean(data.train.targets))
    return np.asarray(
        [global_mean if row[count_index] == 0 else row[prior_index] for row in split.features],
        dtype=float,
    )


def _dispatch_thresholds(dispatch: Sequence[float]) -> tuple[float, float]:
    low, high = np.quantile(np.asarray(dispatch, dtype=float), [1 / 3, 2 / 3])
    return float(low), float(high)


def _group_masks(dispatch: np.ndarray, low: float, high: float) -> dict[str, np.ndarray]:
    return {
        "small": dispatch <= low,
        "medium": (dispatch > low) & (dispatch <= high),
        "large": dispatch > high,
    }


def conformal_margin(actual: np.ndarray, predicted: np.ndarray, coverage: float) -> float:
    """Return a finite-sample one-sided residual quantile."""
    if not len(actual) or len(actual) != len(predicted):
        raise ValueError("actual and predicted arrays must be non-empty and aligned")
    if not 0.0 < coverage < 1.0:
        raise ValueError("coverage must be between zero and one")
    residuals = np.sort(np.asarray(predicted) - np.asarray(actual))
    rank = min(len(residuals) - 1, ceil((len(residuals) + 1) * coverage) - 1)
    return max(0.0, float(residuals[rank]))


def develop_candidate(data: EVTrainingData) -> tuple[dict, dict]:
    """Select a model and calibrate safety without opening test outcomes."""
    if data.train.targets is None or data.validation.targets is None:
        raise ValueError("training and validation targets are required")
    if data.train.evaluation_dispatched_kw is None:
        raise ValueError("training dispatch values are required")
    if data.test.targets is not None or data.test.evaluation_dispatched_kw is not None:
        raise ValueError("candidate v1 test outcomes must remain sealed")

    selection, calibration = split_validation_by_resource(data.validation)
    selection_dispatch = np.asarray(selection.evaluation_dispatched_kw, dtype=float)
    baseline_predictions = _baseline_predictions(data, selection)
    baseline_metrics = _calculate_metrics(
        selection.targets, baseline_predictions, selection_dispatch
    )

    results = []
    fitted_models = {}
    for candidate in model_candidates():
        model = candidate.factory()
        model.fit(data.train.features, data.train.targets)
        predictions = np.clip(model.predict(selection.features), 0.0, 1.0)
        metrics = _calculate_metrics(selection.targets, predictions, selection_dispatch)
        results.append(
            {
                "name": candidate.name,
                "family": candidate.family,
                "parameters": candidate.parameters,
                "selection_metrics": metrics,
            }
        )
        fitted_models[candidate.name] = model

    selected = min(
        results,
        key=lambda row: (
            float(row["selection_metrics"]["mae_ratio"]),
            float(row["selection_metrics"]["mae_kw"]),
            str(row["name"]),
        ),
    )
    model = fitted_models[selected["name"]]
    calibration_actual = np.asarray(calibration.targets, dtype=float)
    calibration_dispatch = np.asarray(calibration.evaluation_dispatched_kw, dtype=float)
    calibration_expected = np.clip(model.predict(calibration.features), 0.0, 1.0)
    low, high = _dispatch_thresholds(data.train.evaluation_dispatched_kw)
    masks = _group_masks(calibration_dispatch, low, high)
    expected_mean_kw = float(np.mean(calibration_expected * calibration_dispatch))
    lower_bound_results = []
    for lower_candidate in lower_bound_candidates():
        lower_model = lower_candidate.factory()
        lower_model.fit(data.train.features, data.train.targets)
        raw_lower = np.minimum(
            calibration_expected,
            np.clip(lower_model.predict(calibration.features), 0.0, 1.0),
        )
        trusted = raw_lower.copy()
        group_safety = {}
        for group, mask in masks.items():
            if not np.any(mask):
                raise ValueError(f"calibration dispatch group {group} is empty")
            margin = conformal_margin(
                calibration_actual[mask], raw_lower[mask], CALIBRATION_COVERAGE
            )
            trusted[mask] = np.clip(raw_lower[mask] - margin, 0.0, 1.0)
            overprediction = 100.0 * float(
                np.mean(trusted[mask] > calibration_actual[mask] + 1e-12)
            )
            group_safety[group] = {
                "row_count": int(np.sum(mask)),
                "conformal_adjustment_ratio": round(margin, 8),
                "overprediction_rate_percent": round(overprediction, 6),
                "passes_15_percent_limit": (
                    overprediction <= MAX_FINAL_OVERPREDICTION_PERCENT
                ),
            }
        trusted_mean_kw = float(np.mean(trusted * calibration_dispatch))
        retained_percent = (
            100.0 * trusted_mean_kw / expected_mean_kw if expected_mean_kw else 0.0
        )
        lower_bound_results.append(
            {
                "name": lower_candidate.name,
                "family": lower_candidate.family,
                "parameters": lower_candidate.parameters,
                "group_safety": group_safety,
                "mean_trusted_kw": round(trusted_mean_kw, 6),
                "trusted_kw_retained_percent": round(retained_percent, 6),
                "all_groups_pass": all(
                    row["passes_15_percent_limit"] for row in group_safety.values()
                ),
            }
        )
    eligible_lower_bounds = [
        row
        for row in lower_bound_results
        if row["all_groups_pass"]
        and row["trusted_kw_retained_percent"] >= MINIMUM_RETENTION_PERCENT
    ]
    selected_lower_bound = max(
        eligible_lower_bounds or lower_bound_results,
        key=lambda row: (float(row["trusted_kw_retained_percent"]), str(row["name"])),
    )
    group_safety = selected_lower_bound["group_safety"]
    trusted_mean_kw = float(selected_lower_bound["mean_trusted_kw"])
    retained_percent = float(selected_lower_bound["trusted_kw_retained_percent"])
    selected_metrics = selected["selection_metrics"]
    development_checks = {
        "selected_expected_mae_ratio_beats_baseline": (
            float(selected_metrics["mae_ratio"]) < float(baseline_metrics["mae_ratio"])
        ),
        "selected_expected_mae_kw_beats_baseline": (
            float(selected_metrics["mae_kw"]) < float(baseline_metrics["mae_kw"])
        ),
        "all_calibration_groups_pass_15_percent_limit": all(
            row["passes_15_percent_limit"] for row in group_safety.values()
        ),
        "trusted_kw_retention_passes_floor": retained_percent >= MINIMUM_RETENTION_PERCENT,
        "old_test_outcomes_remained_sealed": True,
        "selection_and_calibration_resources_are_disjoint": True,
    }
    locked = all(development_checks.values())
    report = {
        "candidate_version": CANDIDATE_VERSION,
        "status": "locked_for_new_holdout" if locked else "development_rejected",
        "data_boundary": {
            "fit_rows": data.train.row_count,
            "selection_rows": selection.row_count,
            "selection_resources": len(set(selection.resource_ids)),
            "calibration_rows": calibration.row_count,
            "calibration_resources": len(set(calibration.resource_ids)),
            "old_consumed_test_rows_used": 0,
        },
        "baseline_selection_metrics": baseline_metrics,
        "candidates": results,
        "selected": selected,
        "safety_calibration": {
            "method": "conditional quantile lower bound with grouped split-conformal adjustment",
            "coverage_target": CALIBRATION_COVERAGE,
            "maximum_final_overprediction_percent": MAX_FINAL_OVERPREDICTION_PERCENT,
            "dispatch_thresholds_kw": {"small_max": low, "medium_max": high},
            "groups": group_safety,
            "lower_bound_candidates": lower_bound_results,
            "selected_lower_bound": selected_lower_bound,
            "mean_expected_kw": round(expected_mean_kw, 6),
            "mean_trusted_kw": round(trusted_mean_kw, 6),
            "trusted_kw_retained_percent": round(retained_percent, 6),
            "minimum_retention_percent": MINIMUM_RETENTION_PERCENT,
        },
        "development_checks": development_checks,
        "limitations": [
            "Development evidence uses ACN structure with synthetic EV behaviour.",
            "Candidate 1's consumed test split was not used.",
            "Passing development checks does not approve deployment.",
            "A separately generated, source-disjoint holdout is still required.",
        ],
    }
    config = {
        "candidate_version": CANDIDATE_VERSION,
        "status": report["status"],
        "deployment_allowed": False,
        "model": {
            "family": selected["family"],
            "name": selected["name"],
            "parameters": selected["parameters"],
            "fit_split": "original_train_only",
        },
        "feature_contract": {
            "names_in_order": list(data.feature_names),
            "imputation_medians": dict(zip(data.feature_names, data.imputation_medians)),
        },
        "safety_policy": {
            "calibration_coverage": CALIBRATION_COVERAGE,
            "maximum_allowed_overprediction_rate_percent": MAX_FINAL_OVERPREDICTION_PERCENT,
            "minimum_retention_percent": MINIMUM_RETENTION_PERCENT,
            "dispatch_group_thresholds_kw": {"small_max": low, "medium_max": high},
            "lower_bound_model": {
                "family": selected_lower_bound["family"],
                "name": selected_lower_bound["name"],
                "parameters": selected_lower_bound["parameters"],
            },
            "conformal_adjustment_ratio_by_dispatch_group": {
                group: values["conformal_adjustment_ratio"]
                for group, values in group_safety.items()
            },
        },
        "final_gate": {
            "holdout": "new source-disjoint ACN-anchored synthetic dataset",
            "required_checks": development_checks,
            "evaluated": False,
        },
        "library_versions": {
            "scikit_learn": sklearn.__version__,
            "numpy": np.__version__,
        },
    }
    return report, config


def run_development(
    input_path: Path = DEFAULT_INPUT_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> tuple[dict, dict]:
    data = load_ev_training_data(input_path)
    report, config = develop_candidate(data)
    report["input"] = {
        "path": str(input_path),
        "canonical_sha256": canonical_sha256(input_path),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    config["evidence"] = {
        "training_table_canonical_sha256": canonical_sha256(input_path),
        "development_report_canonical_sha256": canonical_sha256(report_path),
    }
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return report, config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    report, _ = run_development(args.input, args.report, args.config)
    selected = report["selected"]
    print(f"Candidate v2 status: {report['status']}")
    print(f"Selected model: {selected['name']}")
    print(f"Selection MAE ratio: {selected['selection_metrics']['mae_ratio']:.6f}")
    print(
        "Calibration retained expected kW: "
        f"{report['safety_calibration']['trusted_kw_retained_percent']:.2f}%"
    )
    print("Candidate 1 test outcomes used: 0")


if __name__ == "__main__":
    main()
