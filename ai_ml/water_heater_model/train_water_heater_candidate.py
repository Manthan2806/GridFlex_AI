"""Train the first water-heater classical model candidate.

The model fits training resources and is evaluated on validation resources.
Final test outcomes are not parsed. This stage does not calibrate trusted_kw,
save a release artifact, or approve any deployment use.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from statistics import fmean

import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor

from ai_ml.water_heater_model.prepare_water_heater_training_data import (
    MODEL_FEATURE_COLUMNS,
)


DEFAULT_INPUT = Path(
    "data/processed/water_heater_training/water_heater_training_examples.csv"
)
DEFAULT_BASELINE_REPORT = Path(
    "data/processed/water_heater_training/water_heater_baseline_evaluation.json"
)
DEFAULT_OUTPUT = Path(
    "data/processed/water_heater_training/water_heater_candidate_v1_development.json"
)
CANDIDATE_VERSION = "water_heater_candidate_v1"
RANDOM_STATE = 2901
MODEL_PARAMETERS = {
    "learning_rate": 0.05,
    "max_iter": 200,
    "max_leaf_nodes": 15,
    "min_samples_leaf": 20,
    "l2_regularization": 1.0,
    "random_state": RANDOM_STATE,
}
REQUIRED_COLUMNS = frozenset(
    {
        "resource_id",
        "dataset_split",
        "potential_kw",
        "prior_event_count",
        "heater_type_heat_pump",
        "flex_direction_reduce",
        "target_delivered_kw",
        "target_response_ratio",
        *MODEL_FEATURE_COLUMNS,
    }
)


class CandidateTrainingError(ValueError):
    """Raised when the candidate cannot be trained safely."""


def _float(value: str, field: str, row_number: int) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise CandidateTrainingError(f"row {row_number}: {field} must be numeric") from exc
    if not math.isfinite(parsed):
        raise CandidateTrainingError(f"row {row_number}: {field} must be finite")
    return parsed


def _canonical_sha256(path: Path) -> str:
    payload = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(payload).hexdigest()


def _load_development_data(path: Path) -> dict[str, object]:
    """Load train/validation outcomes while leaving test outcomes untouched."""
    if not path.is_file():
        raise CandidateTrainingError(f"training table does not exist: {path}")
    features: dict[str, list[list[float]]] = {"train": [], "validation": []}
    targets: dict[str, list[float]] = {"train": [], "validation": []}
    potentials: dict[str, list[float]] = {"train": [], "validation": []}
    delivered: dict[str, list[float]] = {"train": [], "validation": []}
    groups: dict[str, list[tuple[int, int, int]]] = {"train": [], "validation": []}
    resource_ids: dict[str, set[str]] = {
        "train": set(), "validation": set(), "test": set()
    }
    row_counts: Counter[str] = Counter()
    resource_splits: dict[str, str] = {}

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = sorted(REQUIRED_COLUMNS - frozenset(reader.fieldnames or ()))
        if missing:
            raise CandidateTrainingError(
                f"{path} is missing columns: {', '.join(missing)}"
            )
        for row_number, row in enumerate(reader, start=2):
            resource_id = row["resource_id"].strip()
            split = row["dataset_split"].strip()
            if not resource_id:
                raise CandidateTrainingError(f"row {row_number}: resource_id is blank")
            if split not in {"train", "validation", "test"}:
                raise CandidateTrainingError(f"row {row_number}: invalid split {split!r}")
            prior_split = resource_splits.setdefault(resource_id, split)
            if prior_split != split:
                raise CandidateTrainingError(
                    f"resource {resource_id} appears in multiple splits"
                )
            row_counts[split] += 1
            resource_ids[split].add(resource_id)

            # Test rows stop here. Their feature and outcome fields are not
            # parsed or used during candidate development.
            if split == "test":
                continue

            vector: list[float] = []
            for name in MODEL_FEATURE_COLUMNS:
                raw = row[name].strip()
                vector.append(np.nan if raw == "" else _float(raw, name, row_number))
            target = _float(row["target_response_ratio"], "target_response_ratio", row_number)
            potential = _float(row["potential_kw"], "potential_kw", row_number)
            actual_kw = _float(row["target_delivered_kw"], "target_delivered_kw", row_number)
            if not 0 <= target <= 1:
                raise CandidateTrainingError(
                    f"row {row_number}: target_response_ratio must be within 0..1"
                )
            if potential <= 0 or actual_kw < 0 or actual_kw > potential + 1e-6:
                raise CandidateTrainingError(
                    f"row {row_number}: power values are outside physical bounds"
                )
            try:
                prior_count = int(row["prior_event_count"])
                heater_type = int(row["heater_type_heat_pump"])
                direction = int(row["flex_direction_reduce"])
            except ValueError as exc:
                raise CandidateTrainingError(
                    f"row {row_number}: group fields must be integers"
                ) from exc
            features[split].append(vector)
            targets[split].append(target)
            potentials[split].append(potential)
            delivered[split].append(actual_kw)
            groups[split].append((prior_count, heater_type, direction))

    if not features["train"] or not features["validation"] or not row_counts["test"]:
        raise CandidateTrainingError("train, validation, and sealed test splits are required")
    return {
        "features": features,
        "targets": targets,
        "potentials": potentials,
        "delivered": delivered,
        "groups": groups,
        "row_counts": dict(row_counts),
        "resource_counts": {key: len(value) for key, value in resource_ids.items()},
    }


def _impute(
    train_rows: list[list[float]], validation_rows: list[list[float]]
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    train = np.asarray(train_rows, dtype=float)
    validation = np.asarray(validation_rows, dtype=float)
    medians = np.nanmedian(train, axis=0)
    if np.any(~np.isfinite(medians)):
        missing = [
            MODEL_FEATURE_COLUMNS[index]
            for index, value in enumerate(medians)
            if not np.isfinite(value)
        ]
        raise CandidateTrainingError(
            f"training columns have no finite values: {', '.join(missing)}"
        )
    train = np.where(np.isnan(train), medians, train)
    validation = np.where(np.isnan(validation), medians, validation)
    if not np.all(np.isfinite(train)) or not np.all(np.isfinite(validation)):
        raise CandidateTrainingError("feature matrices contain non-finite values")
    return (
        train,
        validation,
        {
            name: round(float(value), 8)
            for name, value in zip(MODEL_FEATURE_COLUMNS, medians)
        },
    )


def _metrics(
    actual_ratio: np.ndarray,
    prediction: np.ndarray,
    potential_kw: np.ndarray,
    delivered_kw: np.ndarray,
) -> dict[str, object]:
    if not len(actual_ratio) or not (
        len(actual_ratio) == len(prediction) == len(potential_kw) == len(delivered_kw)
    ):
        raise CandidateTrainingError("metric arrays must be non-empty and aligned")
    raw_bound_violations = int(np.sum((prediction < 0) | (prediction > 1)))
    bounded = np.clip(prediction, 0.0, 1.0)
    ratio_error = bounded - actual_ratio
    expected_kw = bounded * potential_kw
    power_error = expected_kw - delivered_kw
    return {
        "row_count": int(len(actual_ratio)),
        "mae_ratio": round(float(np.mean(np.abs(ratio_error))), 6),
        "rmse_ratio": round(float(np.sqrt(np.mean(ratio_error**2))), 6),
        "bias_ratio": round(float(np.mean(ratio_error)), 6),
        "mae_kw": round(float(np.mean(np.abs(power_error))), 6),
        "rmse_kw": round(float(np.sqrt(np.mean(power_error**2))), 6),
        "bias_kw": round(float(np.mean(power_error)), 6),
        "overprediction_rate_percent": round(
            100 * float(np.mean(power_error > 1e-9)), 6
        ),
        "mean_expected_kw": round(float(np.mean(expected_kw)), 6),
        "expected_to_potential_percent": round(
            100 * float(np.sum(expected_kw) / np.sum(potential_kw)), 6
        ),
        "raw_prediction_bound_violations": raw_bound_violations,
        "prediction_bound_violations": 0,
    }


def _validation_groups(
    actual: np.ndarray,
    prediction: np.ndarray,
    potential: np.ndarray,
    delivered: np.ndarray,
    groups: list[tuple[int, int, int]],
) -> dict[str, dict[str, object]]:
    indices = np.arange(len(groups))
    prior = np.asarray([row[0] for row in groups])
    heater = np.asarray([row[1] for row in groups])
    direction = np.asarray([row[2] for row in groups])
    masks = {
        "all": indices >= 0,
        "cold_start": prior == 0,
        "with_history": prior > 0,
        "heat_pump": heater == 1,
        "electric_resistance": heater == 0,
        "reduce": direction == 1,
        "increase": direction == 0,
    }
    return {
        name: _metrics(actual[mask], prediction[mask], potential[mask], delivered[mask])
        for name, mask in masks.items()
        if np.any(mask)
    }


def train_candidate(
    input_path: Path = DEFAULT_INPUT,
    baseline_report_path: Path = DEFAULT_BASELINE_REPORT,
) -> tuple[HistGradientBoostingRegressor, dict[str, object]]:
    data = _load_development_data(input_path)
    if not baseline_report_path.is_file():
        raise CandidateTrainingError(f"baseline report does not exist: {baseline_report_path}")
    baseline = json.loads(baseline_report_path.read_text(encoding="utf-8"))
    input_hash = _canonical_sha256(input_path)
    if baseline.get("input", {}).get("canonical_sha256") != input_hash:
        raise CandidateTrainingError("baseline report does not match the training table")

    train_x, validation_x, medians = _impute(
        data["features"]["train"], data["features"]["validation"]
    )
    train_y = np.asarray(data["targets"]["train"], dtype=float)
    validation_y = np.asarray(data["targets"]["validation"], dtype=float)
    validation_potential = np.asarray(data["potentials"]["validation"], dtype=float)
    validation_delivered = np.asarray(data["delivered"]["validation"], dtype=float)

    model = HistGradientBoostingRegressor(**MODEL_PARAMETERS)
    model.fit(train_x, train_y)
    raw_predictions = np.asarray(model.predict(validation_x), dtype=float)
    validation_metrics = _validation_groups(
        validation_y,
        raw_predictions,
        validation_potential,
        validation_delivered,
        data["groups"]["validation"],
    )
    selected_baseline = baseline["validation_comparison"]["selected_baseline"]
    baseline_metrics = baseline["baselines"][selected_baseline]["validation"]["all"]
    model_metrics = validation_metrics["all"]
    checks = {
        "mae_ratio_beats_selected_baseline": (
            float(model_metrics["mae_ratio"]) < float(baseline_metrics["mae_ratio"])
        ),
        "mae_kw_beats_selected_baseline": (
            float(model_metrics["mae_kw"]) < float(baseline_metrics["mae_kw"])
        ),
        "bounded_predictions": model_metrics["prediction_bound_violations"] == 0,
        "test_outcomes_remained_unread": True,
    }
    accepted = all(checks.values())
    report: dict[str, object] = {
        "candidate_version": CANDIDATE_VERSION,
        "status": "accepted_for_safety_calibration" if accepted else "development_rejected",
        "deployment_allowed": False,
        "model_artifact_saved": False,
        "data_boundary": {
            "fit_rows": data["row_counts"]["train"],
            "fit_resources": data["resource_counts"]["train"],
            "validation_rows": data["row_counts"]["validation"],
            "validation_resources": data["resource_counts"]["validation"],
            "sealed_test_rows": data["row_counts"]["test"],
            "sealed_test_resources": data["resource_counts"]["test"],
            "test_outcomes_read": False,
        },
        "model": {
            "family": "HistGradientBoostingRegressor",
            "parameters": MODEL_PARAMETERS,
            "target": "target_response_ratio",
            "prediction_clipping": "final expected ratio clipped to 0..1",
            "feature_names_in_order": list(MODEL_FEATURE_COLUMNS),
            "training_only_imputation_medians": medians,
        },
        "selected_baseline": {
            "name": selected_baseline,
            "validation_all": baseline_metrics,
        },
        "candidate_validation": validation_metrics,
        "improvement": {
            "mae_ratio_percent_vs_selected_baseline": round(
                100
                * (float(baseline_metrics["mae_ratio"]) - float(model_metrics["mae_ratio"]))
                / float(baseline_metrics["mae_ratio"]),
                6,
            ),
            "mae_kw_percent_vs_selected_baseline": round(
                100
                * (float(baseline_metrics["mae_kw"]) - float(model_metrics["mae_kw"]))
                / float(baseline_metrics["mae_kw"]),
                6,
            ),
        },
        "development_checks": checks,
        "next_stage": (
            "calibrate trusted_kw using validation-only evidence"
            if accepted
            else "revise candidate without opening test outcomes"
        ),
        "test_holdout": {
            "status": "sealed",
            "target_columns_read": False,
            "allowed_use": "one final evaluation after model and safety policy are frozen",
        },
        "evidence": {
            "training_table_canonical_sha256": input_hash,
            "baseline_report_canonical_sha256": _canonical_sha256(baseline_report_path),
        },
        "library_versions": {
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "limitations": [
            "All water-heater response outcomes are synthetic.",
            "Validation acceptance permits safety-calibration work only.",
            "No trusted_kw policy has been calibrated and no release artifact is saved.",
            "The final test split remains sealed.",
        ],
    }
    return model, report


def write_report(report: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--baseline-report", type=Path, default=DEFAULT_BASELINE_REPORT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    _, report = train_candidate(args.input, args.baseline_report)
    write_report(report, args.output)
    metrics = report["candidate_validation"]["all"]
    print(f"Water-heater candidate status: {report['status']}")
    print("Model: HistGradientBoostingRegressor")
    print(f"Validation ratio MAE: {metrics['mae_ratio']:.6f}")
    print(f"Validation power MAE: {metrics['mae_kw']:.6f} kW")
    print(
        "Ratio MAE improvement over baseline: "
        f"{report['improvement']['mae_ratio_percent_vs_selected_baseline']:.2f}%"
    )
    print("Final test outcomes read: false")


if __name__ == "__main__":
    main()
