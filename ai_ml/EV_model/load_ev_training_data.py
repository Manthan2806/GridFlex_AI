"""Load leakage-safe EV data splits for classical model training.

Feature values are read from the shared allow-list. Missing history features are
filled with medians learned from training rows only. Validation targets are
available for model selection, while test targets remain sealed.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from statistics import median
from typing import Iterable, Mapping, Sequence

from ai_ml.EV_model.prepare_ev_training_data import MODEL_FEATURE_COLUMNS


DEFAULT_INPUT_PATH = Path("data/processed/ev_training/ev_training_examples.csv")
TARGET_COLUMN = "target_delivery_ratio"
EVALUATION_DISPATCH_COLUMN = "target_dispatched_kw"
ALLOWED_SPLITS = ("train", "validation", "test")
IMPUTABLE_FEATURE_COLUMNS = frozenset(
    {
        "prior_delivery_ratio_mean",
        "prior_delivery_ratio_ema",
        "prior_delivery_ratio_std",
        "prior_availability_rate",
        "prior_override_rate",
    }
)


class EVDataLoadingError(ValueError):
    """Raised when the prepared EV table is unsafe or invalid."""


@dataclass(frozen=True)
class EVSplit:
    """One model split after training-only missing-value handling."""

    resource_ids: tuple[str, ...]
    features: tuple[tuple[float, ...], ...]
    targets: tuple[float, ...] | None
    evaluation_dispatched_kw: tuple[float, ...] | None

    @property
    def row_count(self) -> int:
        return len(self.resource_ids)


@dataclass(frozen=True)
class EVTrainingData:
    """Prepared train, validation, and sealed test splits."""

    feature_names: tuple[str, ...]
    imputation_medians: tuple[float, ...]
    train: EVSplit
    validation: EVSplit
    test: EVSplit


@dataclass(frozen=True)
class _RawSplit:
    resource_ids: tuple[str, ...]
    features: tuple[tuple[float | None, ...], ...]
    targets: tuple[float, ...] | None
    evaluation_dispatched_kw: tuple[float, ...] | None


def _parse_optional_feature(value: str, *, row_name: str, column: str) -> float | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        number = float(cleaned)
    except ValueError as exc:
        raise EVDataLoadingError(f"{row_name}: {column} must be numeric or blank") from exc
    if not isfinite(number):
        raise EVDataLoadingError(f"{row_name}: {column} must be finite")
    return number


def _parse_required_number(value: str, *, row_name: str, column: str) -> float:
    parsed = _parse_optional_feature(value, row_name=row_name, column=column)
    if parsed is None:
        raise EVDataLoadingError(f"{row_name}: {column} cannot be blank")
    return parsed


def _training_medians(rows: Sequence[Sequence[float | None]]) -> tuple[float, ...]:
    if not rows:
        raise EVDataLoadingError("training split is empty")

    medians: list[float] = []
    for column_index, column_name in enumerate(MODEL_FEATURE_COLUMNS):
        observed = [row[column_index] for row in rows if row[column_index] is not None]
        if not observed:
            raise EVDataLoadingError(
                f"training split has no usable values for feature {column_name!r}"
            )
        medians.append(float(median(observed)))
    return tuple(medians)


def _fill_missing(
    rows: Iterable[Sequence[float | None]], medians: Sequence[float]
) -> tuple[tuple[float, ...], ...]:
    return tuple(
        tuple(medians[index] if value is None else value for index, value in enumerate(row))
        for row in rows
    )


def _finalize_split(raw: _RawSplit, medians: Sequence[float]) -> EVSplit:
    return EVSplit(
        resource_ids=raw.resource_ids,
        features=_fill_missing(raw.features, medians),
        targets=raw.targets,
        evaluation_dispatched_kw=raw.evaluation_dispatched_kw,
    )


def load_ev_training_data(input_path: Path = DEFAULT_INPUT_PATH) -> EVTrainingData:
    """Load model inputs while keeping the test answers sealed."""

    required_columns = {
        "resource_id",
        "dataset_split",
        TARGET_COLUMN,
        EVALUATION_DISPATCH_COLUMN,
        *MODEL_FEATURE_COLUMNS,
    }
    buffers: dict[str, dict[str, list]] = {
        split: {"resource_ids": [], "features": [], "targets": [], "dispatch": []}
        for split in ALLOWED_SPLITS
    }

    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or ())
        missing_columns = sorted(required_columns - columns)
        if missing_columns:
            raise EVDataLoadingError(f"missing required columns: {missing_columns}")

        for row_number, source in enumerate(reader, start=2):
            row_name = f"row {row_number}"
            split = source["dataset_split"].strip()
            if split not in buffers:
                raise EVDataLoadingError(f"{row_name}: invalid dataset_split {split!r}")

            resource_id = source["resource_id"].strip()
            if not resource_id:
                raise EVDataLoadingError(f"{row_name}: resource_id cannot be blank")

            feature_row = tuple(
                _parse_optional_feature(source[column], row_name=row_name, column=column)
                for column in MODEL_FEATURE_COLUMNS
            )
            for column, value in zip(MODEL_FEATURE_COLUMNS, feature_row):
                if value is None and column not in IMPUTABLE_FEATURE_COLUMNS:
                    raise EVDataLoadingError(
                        f"{row_name}: required feature {column!r} cannot be blank"
                    )
            buffers[split]["resource_ids"].append(resource_id)
            buffers[split]["features"].append(feature_row)

            # Never access test outcome strings. They may be deliberately sealed.
            if split != "test":
                target = _parse_required_number(
                    source[TARGET_COLUMN], row_name=row_name, column=TARGET_COLUMN
                )
                if not 0.0 <= target <= 1.0:
                    raise EVDataLoadingError(
                        f"{row_name}: {TARGET_COLUMN} must be between 0 and 1"
                    )
                dispatch = _parse_required_number(
                    source[EVALUATION_DISPATCH_COLUMN],
                    row_name=row_name,
                    column=EVALUATION_DISPATCH_COLUMN,
                )
                if dispatch < 0.0:
                    raise EVDataLoadingError(
                        f"{row_name}: {EVALUATION_DISPATCH_COLUMN} cannot be negative"
                    )
                buffers[split]["targets"].append(target)
                buffers[split]["dispatch"].append(dispatch)

    raw_splits: dict[str, _RawSplit] = {}
    for split, values in buffers.items():
        if not values["resource_ids"]:
            raise EVDataLoadingError(f"{split} split is empty")
        is_test = split == "test"
        raw_splits[split] = _RawSplit(
            resource_ids=tuple(values["resource_ids"]),
            features=tuple(values["features"]),
            targets=None if is_test else tuple(values["targets"]),
            evaluation_dispatched_kw=None if is_test else tuple(values["dispatch"]),
        )

    medians = _training_medians(raw_splits["train"].features)
    return EVTrainingData(
        feature_names=tuple(MODEL_FEATURE_COLUMNS),
        imputation_medians=medians,
        train=_finalize_split(raw_splits["train"], medians),
        validation=_finalize_split(raw_splits["validation"], medians),
        test=_finalize_split(raw_splits["test"], medians),
    )
