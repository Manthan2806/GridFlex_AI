"""Evaluate simple EV delivery-ratio baselines without training an ML model.

The training split supplies the global average. Baselines are compared on the
validation split. The test split stays sealed until the final model evaluation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from math import isfinite, sqrt
from pathlib import Path
from statistics import fmean


DEFAULT_INPUT_PATH = Path("data/processed/ev_training/ev_training_examples.csv")
DEFAULT_OUTPUT_PATH = Path("data/processed/ev_training/ev_baseline_evaluation.json")
EVALUATION_VERSION = "ev_baseline_evaluation_v1"
ALLOWED_SPLITS = frozenset({"train", "validation", "test"})

REQUIRED_COLUMNS = frozenset(
    {
        "resource_id",
        "dataset_split",
        "prior_event_count",
        "prior_delivery_ratio_mean",
        "target_dispatched_kw",
        "target_delivered_kw",
        "target_delivery_ratio",
    }
)


class BaselineEvaluationError(ValueError):
    """Raised when the prepared training table is invalid for evaluation."""


@dataclass(frozen=True)
class EvaluationRow:
    resource_id: str
    dataset_split: str
    prior_event_count: int
    prior_delivery_ratio_mean: float | None
    dispatched_kw: float | None
    delivered_kw: float | None
    delivery_ratio: float | None


def _finite_float(value: str, column: str, row_number: int) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise BaselineEvaluationError(
            f"row {row_number}: {column} must be numeric"
        ) from exc
    if not isfinite(parsed):
        raise BaselineEvaluationError(f"row {row_number}: {column} must be finite")
    return parsed


def load_evaluation_rows(input_path: Path) -> list[EvaluationRow]:
    if not input_path.is_file():
        raise BaselineEvaluationError(f"training table does not exist: {input_path}")

    rows: list[EvaluationRow] = []
    resource_splits: dict[str, str] = {}
    with input_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = frozenset(reader.fieldnames or ())
        missing = sorted(REQUIRED_COLUMNS - columns)
        if missing:
            raise BaselineEvaluationError(
                f"{input_path} is missing columns: {', '.join(missing)}"
            )

        for row_number, source in enumerate(reader, start=2):
            resource_id = source["resource_id"].strip()
            if not resource_id:
                raise BaselineEvaluationError(f"row {row_number}: resource_id is blank")
            dataset_split = source["dataset_split"].strip()
            if dataset_split not in ALLOWED_SPLITS:
                raise BaselineEvaluationError(
                    f"row {row_number}: invalid dataset_split {dataset_split!r}"
                )
            previous_split = resource_splits.setdefault(resource_id, dataset_split)
            if previous_split != dataset_split:
                raise BaselineEvaluationError(
                    f"resource {resource_id} appears in multiple dataset splits"
                )

            try:
                prior_event_count = int(source["prior_event_count"])
            except ValueError as exc:
                raise BaselineEvaluationError(
                    f"row {row_number}: prior_event_count must be an integer"
                ) from exc
            if prior_event_count < 0:
                raise BaselineEvaluationError(
                    f"row {row_number}: prior_event_count cannot be negative"
                )

            prior_text = source["prior_delivery_ratio_mean"].strip()
            prior_mean = (
                None
                if prior_text == ""
                else _finite_float(prior_text, "prior_delivery_ratio_mean", row_number)
            )
            if prior_event_count == 0 and prior_mean is not None:
                raise BaselineEvaluationError(
                    f"row {row_number}: cold-start row cannot have a prior mean"
                )
            if prior_event_count > 0 and prior_mean is None:
                raise BaselineEvaluationError(
                    f"row {row_number}: prior mean is required when history exists"
                )
            if prior_mean is not None and not 0.0 <= prior_mean <= 1.0:
                raise BaselineEvaluationError(
                    f"row {row_number}: prior delivery ratio must be between 0 and 1"
                )

            # Do not parse test outcomes here. They remain genuinely sealed until
            # the final model evaluation, rather than merely omitted from output.
            dispatched_kw: float | None = None
            delivered_kw: float | None = None
            delivery_ratio: float | None = None
            if dataset_split != "test":
                dispatched_kw = _finite_float(
                    source["target_dispatched_kw"], "target_dispatched_kw", row_number
                )
                delivered_kw = _finite_float(
                    source["target_delivered_kw"], "target_delivered_kw", row_number
                )
                delivery_ratio = _finite_float(
                    source["target_delivery_ratio"], "target_delivery_ratio", row_number
                )
                if dispatched_kw <= 0:
                    raise BaselineEvaluationError(
                        f"row {row_number}: target_dispatched_kw must be positive"
                    )
                if delivered_kw < 0:
                    raise BaselineEvaluationError(
                        f"row {row_number}: target_delivered_kw cannot be negative"
                    )
                if not 0.0 <= delivery_ratio <= 1.0:
                    raise BaselineEvaluationError(
                        f"row {row_number}: target_delivery_ratio must be between 0 and 1"
                    )

            rows.append(
                EvaluationRow(
                    resource_id=resource_id,
                    dataset_split=dataset_split,
                    prior_event_count=prior_event_count,
                    prior_delivery_ratio_mean=prior_mean,
                    dispatched_kw=dispatched_kw,
                    delivered_kw=delivered_kw,
                    delivery_ratio=delivery_ratio,
                )
            )

    if not rows:
        raise BaselineEvaluationError("training table contains no rows")
    return rows


def _round(value: float) -> float:
    return round(value, 6)


def calculate_metrics(
    rows: list[EvaluationRow], predicted_ratios: list[float]
) -> dict[str, int | float]:
    if not rows or len(rows) != len(predicted_ratios):
        raise BaselineEvaluationError(
            "rows and predicted_ratios must have the same non-zero length"
        )
    if any(not isfinite(value) for value in predicted_ratios):
        raise BaselineEvaluationError("predicted ratios must be finite")

    ratio_errors: list[float] = []
    kw_errors: list[float] = []
    bound_violations = 0
    for row, prediction in zip(rows, predicted_ratios):
        if (
            row.delivery_ratio is None
            or row.dispatched_kw is None
            or row.delivered_kw is None
        ):
            raise BaselineEvaluationError("cannot calculate metrics for sealed outcomes")
        if not 0.0 <= prediction <= 1.0:
            bound_violations += 1
        bounded_prediction = min(1.0, max(0.0, prediction))
        ratio_errors.append(bounded_prediction - row.delivery_ratio)
        predicted_delivered_kw = row.dispatched_kw * bounded_prediction
        kw_errors.append(predicted_delivered_kw - row.delivered_kw)

    count = len(rows)
    return {
        "row_count": count,
        "mae_ratio": _round(sum(abs(error) for error in ratio_errors) / count),
        "rmse_ratio": _round(sqrt(sum(error * error for error in ratio_errors) / count)),
        "bias_ratio": _round(sum(ratio_errors) / count),
        "mean_overestimation_ratio": _round(
            sum(max(0.0, error) for error in ratio_errors) / count
        ),
        "mae_kw": _round(sum(abs(error) for error in kw_errors) / count),
        "rmse_kw": _round(sqrt(sum(error * error for error in kw_errors) / count)),
        "bias_kw": _round(sum(kw_errors) / count),
        "mean_overestimation_kw": _round(
            sum(max(0.0, error) for error in kw_errors) / count
        ),
        "prediction_bound_violations": bound_violations,
    }


def _evaluate_groups(
    rows: list[EvaluationRow], predicted_ratios: list[float]
) -> dict[str, dict[str, int | float]]:
    groups = {
        "all": [index for index in range(len(rows))],
        "cold_start": [
            index for index, row in enumerate(rows) if row.prior_event_count == 0
        ],
        "with_history": [
            index for index, row in enumerate(rows) if row.prior_event_count > 0
        ],
    }
    return {
        name: calculate_metrics(
            [rows[index] for index in indices],
            [predicted_ratios[index] for index in indices],
        )
        for name, indices in groups.items()
        if indices
    }


def evaluate_baselines(input_path: Path = DEFAULT_INPUT_PATH) -> dict[str, object]:
    rows = load_evaluation_rows(input_path)
    rows_by_split = {
        split: [row for row in rows if row.dataset_split == split]
        for split in sorted(ALLOWED_SPLITS)
    }
    if not rows_by_split["train"] or not rows_by_split["validation"]:
        raise BaselineEvaluationError("training and validation splits must be non-empty")

    training_ratios = [
        row.delivery_ratio
        for row in rows_by_split["train"]
        if row.delivery_ratio is not None
    ]
    global_train_mean = fmean(training_ratios)
    validation_rows = rows_by_split["validation"]
    global_predictions = [global_train_mean] * len(validation_rows)
    rolling_predictions = [
        global_train_mean
        if row.prior_delivery_ratio_mean is None
        else row.prior_delivery_ratio_mean
        for row in validation_rows
    ]

    global_metrics = _evaluate_groups(validation_rows, global_predictions)
    rolling_metrics = _evaluate_groups(validation_rows, rolling_predictions)
    global_mae = float(global_metrics["all"]["mae_ratio"])
    rolling_mae = float(rolling_metrics["all"]["mae_ratio"])
    improvement = 0.0 if global_mae == 0 else 100.0 * (global_mae - rolling_mae) / global_mae

    split_counts = Counter(row.dataset_split for row in rows)
    split_resource_counts = {
        split: len({row.resource_id for row in split_rows})
        for split, split_rows in rows_by_split.items()
    }
    selected = (
        "rolling_history" if rolling_mae < global_mae else "global_train_mean"
    )

    return {
        "evaluation_version": EVALUATION_VERSION,
        "scope": "Offline baseline evaluation on hybrid/synthetic EV behaviour; not real-world validation.",
        "input": {
            "path": input_path.as_posix(),
            "sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
            "row_count": len(rows),
            "split_row_counts": dict(sorted(split_counts.items())),
            "split_resource_counts": split_resource_counts,
        },
        "target": "target_delivery_ratio",
        "global_train_mean_ratio": _round(global_train_mean),
        "evaluation_split": "validation",
        "baselines": {
            "global_train_mean": {
                "description": "Predict the average delivery ratio observed in training rows.",
                "validation": global_metrics,
            },
            "rolling_history": {
                "description": (
                    "Predict each EV's prior mean delivery ratio; use the training "
                    "average for cold-start rows."
                ),
                "validation": rolling_metrics,
            },
        },
        "validation_comparison": {
            "selected_baseline": selected,
            "mae_ratio_improvement_percent_vs_global": _round(improvement),
        },
        "test_holdout": {
            "status": "sealed",
            "row_count": len(rows_by_split["test"]),
            "resource_count": split_resource_counts["test"],
            "target_columns_read": False,
            "reason": "Test outcomes are reserved for the final selected ML model comparison.",
        },
        "leakage_boundary": {
            "prediction_inputs": [
                "global_train_mean_ratio",
                "prior_delivery_ratio_mean for the same EV from earlier events only",
            ],
            "current_outcome_columns_are_inputs": False,
            "target_dispatched_kw_usage": (
                "Used only after ratio prediction to express evaluation error in kW; "
                "never used to choose the predicted ratio."
            ),
        },
    }


def write_evaluation_report(report: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()
    report = evaluate_baselines(args.input)
    write_evaluation_report(report, args.output)
    selected = report["validation_comparison"]["selected_baseline"]
    print(f"Wrote EV baseline evaluation to {args.output}")
    print(f"Validation baseline selected by MAE ratio: {selected}")


if __name__ == "__main__":
    main()
