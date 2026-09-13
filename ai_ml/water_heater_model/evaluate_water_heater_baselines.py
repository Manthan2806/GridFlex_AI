"""Evaluate simple water-heater response baselines without training ML.

Training outcomes define population/group averages. Validation outcomes compare
the baselines. Test outcomes remain unread and sealed for a later final gate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean


DEFAULT_INPUT = Path(
    "data/processed/water_heater_training/water_heater_training_examples.csv"
)
DEFAULT_OUTPUT = Path(
    "data/processed/water_heater_training/water_heater_baseline_evaluation.json"
)
EVALUATION_VERSION = "gridflex-water-heater-baselines-v1"
ALLOWED_SPLITS = frozenset({"train", "validation", "test"})
REQUIRED_COLUMNS = frozenset(
    {
        "resource_id",
        "dataset_split",
        "heater_type_heat_pump",
        "flex_direction_reduce",
        "potential_kw",
        "prior_event_count",
        "prior_response_ratio_mean",
        "prior_response_ratio_ema",
        "target_delivered_kw",
        "target_response_ratio",
    }
)


class BaselineEvaluationError(ValueError):
    """Raised when the prepared table is invalid for baseline evaluation."""


@dataclass(frozen=True)
class EvaluationRow:
    resource_id: str
    dataset_split: str
    heater_type_heat_pump: int
    flex_direction_reduce: int
    potential_kw: float
    prior_event_count: int
    prior_mean: float | None
    prior_ema: float | None
    target_delivered_kw: float | None
    target_response_ratio: float | None


def _float(value: str, field: str, row_number: int) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise BaselineEvaluationError(f"row {row_number}: {field} must be numeric") from exc
    if not math.isfinite(parsed):
        raise BaselineEvaluationError(f"row {row_number}: {field} must be finite")
    return parsed


def _optional_ratio(value: str, field: str, row_number: int) -> float | None:
    if value.strip() == "":
        return None
    parsed = _float(value, field, row_number)
    if not 0 <= parsed <= 1:
        raise BaselineEvaluationError(f"row {row_number}: {field} must be within 0..1")
    return parsed


def load_rows(path: Path) -> list[EvaluationRow]:
    if not path.is_file():
        raise BaselineEvaluationError(f"training table does not exist: {path}")
    rows: list[EvaluationRow] = []
    resource_splits: dict[str, str] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = sorted(REQUIRED_COLUMNS - frozenset(reader.fieldnames or ()))
        if missing:
            raise BaselineEvaluationError(f"{path} is missing columns: {', '.join(missing)}")
        for row_number, source in enumerate(reader, start=2):
            resource_id = source["resource_id"].strip()
            split = source["dataset_split"].strip()
            if not resource_id:
                raise BaselineEvaluationError(f"row {row_number}: resource_id is blank")
            if split not in ALLOWED_SPLITS:
                raise BaselineEvaluationError(f"row {row_number}: invalid split {split!r}")
            previous = resource_splits.setdefault(resource_id, split)
            if previous != split:
                raise BaselineEvaluationError(
                    f"resource {resource_id} appears in multiple splits"
                )
            try:
                heater_type = int(source["heater_type_heat_pump"])
                direction = int(source["flex_direction_reduce"])
                prior_count = int(source["prior_event_count"])
            except ValueError as exc:
                raise BaselineEvaluationError(
                    f"row {row_number}: indicator/count fields must be integers"
                ) from exc
            if heater_type not in {0, 1} or direction not in {0, 1} or prior_count < 0:
                raise BaselineEvaluationError(f"row {row_number}: invalid indicator/count value")
            potential = _float(source["potential_kw"], "potential_kw", row_number)
            if potential <= 0:
                raise BaselineEvaluationError(f"row {row_number}: potential_kw must be positive")
            prior_mean = _optional_ratio(
                source["prior_response_ratio_mean"], "prior_response_ratio_mean", row_number
            )
            prior_ema = _optional_ratio(
                source["prior_response_ratio_ema"], "prior_response_ratio_ema", row_number
            )
            if prior_count == 0 and (prior_mean is not None or prior_ema is not None):
                raise BaselineEvaluationError(
                    f"row {row_number}: cold-start event contains historical features"
                )
            if prior_count > 0 and (prior_mean is None or prior_ema is None):
                raise BaselineEvaluationError(
                    f"row {row_number}: historical features are missing"
                )

            # Test outcome strings are deliberately never parsed. This keeps the
            # final test evidence sealed during baseline selection.
            target_kw: float | None = None
            target_ratio: float | None = None
            if split != "test":
                target_kw = _float(source["target_delivered_kw"], "target_delivered_kw", row_number)
                target_ratio = _float(
                    source["target_response_ratio"], "target_response_ratio", row_number
                )
                if target_kw < 0 or target_kw > potential + 1e-6:
                    raise BaselineEvaluationError(
                        f"row {row_number}: target_delivered_kw is outside physical bounds"
                    )
                if not 0 <= target_ratio <= 1:
                    raise BaselineEvaluationError(
                        f"row {row_number}: target_response_ratio must be within 0..1"
                    )
            rows.append(
                EvaluationRow(
                    resource_id=resource_id,
                    dataset_split=split,
                    heater_type_heat_pump=heater_type,
                    flex_direction_reduce=direction,
                    potential_kw=potential,
                    prior_event_count=prior_count,
                    prior_mean=prior_mean,
                    prior_ema=prior_ema,
                    target_delivered_kw=target_kw,
                    target_response_ratio=target_ratio,
                )
            )
    if not rows:
        raise BaselineEvaluationError("training table contains no rows")
    return rows


def _metrics(rows: list[EvaluationRow], predictions: list[float]) -> dict[str, object]:
    if not rows or len(rows) != len(predictions):
        raise BaselineEvaluationError("evaluation rows and predictions must align")
    ratio_errors: list[float] = []
    power_errors: list[float] = []
    overpredicted = 0
    bound_violations = 0
    expected_power: list[float] = []
    potential_power: list[float] = []
    for row, prediction in zip(rows, predictions):
        if row.target_response_ratio is None or row.target_delivered_kw is None:
            raise BaselineEvaluationError("sealed test outcomes cannot be evaluated")
        if not math.isfinite(prediction):
            raise BaselineEvaluationError("prediction must be finite")
        if not 0 <= prediction <= 1:
            bound_violations += 1
        bounded = min(1.0, max(0.0, prediction))
        predicted_kw = row.potential_kw * bounded
        ratio_error = bounded - row.target_response_ratio
        power_error = predicted_kw - row.target_delivered_kw
        ratio_errors.append(ratio_error)
        power_errors.append(power_error)
        expected_power.append(predicted_kw)
        potential_power.append(row.potential_kw)
        if power_error > 1e-9:
            overpredicted += 1
    count = len(rows)
    return {
        "row_count": count,
        "mae_ratio": round(fmean(abs(value) for value in ratio_errors), 6),
        "rmse_ratio": round(math.sqrt(fmean(value * value for value in ratio_errors)), 6),
        "bias_ratio": round(fmean(ratio_errors), 6),
        "mae_kw": round(fmean(abs(value) for value in power_errors), 6),
        "rmse_kw": round(math.sqrt(fmean(value * value for value in power_errors)), 6),
        "bias_kw": round(fmean(power_errors), 6),
        "overprediction_rate_percent": round(100 * overpredicted / count, 6),
        "mean_expected_kw": round(fmean(expected_power), 6),
        "mean_potential_kw": round(fmean(potential_power), 6),
        "expected_to_potential_percent": round(
            100 * sum(expected_power) / sum(potential_power), 6
        ),
        "prediction_bound_violations": bound_violations,
    }


def _group_metrics(
    rows: list[EvaluationRow], predictions: list[float]
) -> dict[str, dict[str, object]]:
    groups = {
        "all": list(range(len(rows))),
        "cold_start": [i for i, row in enumerate(rows) if row.prior_event_count == 0],
        "with_history": [i for i, row in enumerate(rows) if row.prior_event_count > 0],
        "heat_pump": [i for i, row in enumerate(rows) if row.heater_type_heat_pump == 1],
        "electric_resistance": [i for i, row in enumerate(rows) if row.heater_type_heat_pump == 0],
        "reduce": [i for i, row in enumerate(rows) if row.flex_direction_reduce == 1],
        "increase": [i for i, row in enumerate(rows) if row.flex_direction_reduce == 0],
    }
    return {
        name: _metrics(
            [rows[index] for index in indices],
            [predictions[index] for index in indices],
        )
        for name, indices in groups.items()
        if indices
    }


def _training_group_means(
    rows: list[EvaluationRow], key_fields: tuple[str, ...]
) -> dict[tuple[int, ...], float]:
    values: dict[tuple[int, ...], list[float]] = defaultdict(list)
    for row in rows:
        if row.target_response_ratio is None:
            raise BaselineEvaluationError("training outcome is missing")
        key = tuple(int(getattr(row, field)) for field in key_fields)
        values[key].append(row.target_response_ratio)
    return {key: fmean(group) for key, group in values.items()}


def evaluate_baselines(path: Path = DEFAULT_INPUT) -> dict[str, object]:
    rows = load_rows(path)
    by_split = {
        split: [row for row in rows if row.dataset_split == split]
        for split in sorted(ALLOWED_SPLITS)
    }
    training = by_split["train"]
    validation = by_split["validation"]
    if not training or not validation or not by_split["test"]:
        raise BaselineEvaluationError("train, validation, and test splits must be non-empty")
    training_ratios = [
        row.target_response_ratio
        for row in training
        if row.target_response_ratio is not None
    ]
    global_mean = fmean(training_ratios)
    type_means = _training_group_means(training, ("heater_type_heat_pump",))
    type_direction_means = _training_group_means(
        training, ("heater_type_heat_pump", "flex_direction_reduce")
    )

    predictions: dict[str, list[float]] = {
        "global_train_mean": [global_mean for _ in validation],
        "heater_type_mean": [
            type_means[(row.heater_type_heat_pump,)] for row in validation
        ],
        "heater_type_direction_mean": [
            type_direction_means[(row.heater_type_heat_pump, row.flex_direction_reduce)]
            for row in validation
        ],
        "prior_resource_mean": [
            row.prior_mean
            if row.prior_mean is not None
            else type_direction_means[(row.heater_type_heat_pump, row.flex_direction_reduce)]
            for row in validation
        ],
        "prior_resource_ema": [
            row.prior_ema
            if row.prior_ema is not None
            else type_direction_means[(row.heater_type_heat_pump, row.flex_direction_reduce)]
            for row in validation
        ],
    }
    results = {
        name: {"validation": _group_metrics(validation, values)}
        for name, values in predictions.items()
    }
    selected = min(
        results,
        key=lambda name: float(results[name]["validation"]["all"]["mae_ratio"]),
    )
    global_mae = float(results["global_train_mean"]["validation"]["all"]["mae_ratio"])
    selected_mae = float(results[selected]["validation"]["all"]["mae_ratio"])
    resource_counts = {
        split: len({row.resource_id for row in split_rows})
        for split, split_rows in by_split.items()
    }
    canonical = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return {
        "evaluation_version": EVALUATION_VERSION,
        "scope": "Synthetic water-heater baseline validation; not field evidence.",
        "input": {
            "path": path.as_posix(),
            "canonical_sha256": hashlib.sha256(canonical).hexdigest(),
            "row_count": len(rows),
            "split_row_counts": dict(sorted(Counter(row.dataset_split for row in rows).items())),
            "split_resource_counts": resource_counts,
        },
        "target": "target_response_ratio",
        "training_global_mean_response_ratio": round(global_mean, 6),
        "evaluation_split": "validation",
        "baselines": results,
        "validation_comparison": {
            "selected_baseline": selected,
            "selection_metric": "lowest validation all-row mae_ratio",
            "selected_mae_ratio": selected_mae,
            "mae_improvement_percent_vs_global": round(
                100 * (global_mae - selected_mae) / global_mae, 6
            ) if global_mae else 0.0,
        },
        "test_holdout": {
            "status": "sealed",
            "row_count": len(by_split["test"]),
            "resource_count": resource_counts["test"],
            "target_columns_read": False,
            "reason": "Reserved for one final evaluation after model and safety policy are frozen.",
        },
        "leakage_boundary": {
            "training_outcomes_used_only_for_population_and_group means": True,
            "validation_outcomes_used_only_for_metrics": True,
            "test_outcomes_read": False,
            "same_event_target_columns_used_as_prediction_inputs": False,
        },
    }


def write_report(report: dict[str, object], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = evaluate_baselines(args.input)
    write_report(report, args.output)
    comparison = report["validation_comparison"]
    print(f"Water-heater baseline evaluation written to {args.output}")
    print(f"Selected baseline: {comparison['selected_baseline']}")
    print(f"Validation MAE ratio: {comparison['selected_mae_ratio']:.6f}")
    print(
        "Improvement over global mean: "
        f"{comparison['mae_improvement_percent_vs_global']:.2f}%"
    )
    print("Final test outcomes read: false")


if __name__ == "__main__":
    main()
