"""Build leakage-safe EV delivery-ratio training examples.

Each output row represents one historical dispatch event. Features describing
past behaviour are calculated strictly from earlier events for the same EV.
The current event outcome is retained only in columns prefixed with ``target_``.
No model is trained by this module.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime
from math import isfinite
from pathlib import Path
from statistics import fmean, pstdev
from typing import Iterable, Mapping


DEFAULT_RESOURCES_PATH = Path("data/synthetic/ev/ev_resources.csv")
DEFAULT_HISTORY_PATH = Path("data/synthetic/behavior/ev_historical_response.csv")
DEFAULT_OUTPUT_PATH = Path("data/processed/ev_training/ev_training_examples.csv")
DEFAULT_EMA_ALPHA = 0.35
ALLOWED_SPLITS = frozenset({"train", "validation", "test"})

RESOURCE_REQUIRED_COLUMNS = frozenset(
    {
        "id",
        "rated_power_kw",
        "earliest_start",
        "latest_end",
        "required_kwh",
        "maximum_kwh",
        "max_power",
        "battery_capacity_kwh",
        "arrival_soc_pct",
        "target_soc_pct",
        "dataset_split",
    }
)

HISTORY_REQUIRED_COLUMNS = frozenset(
    {
        "resource_id",
        "timestamp",
        "dispatched_kw",
        "delivered_kw",
        "is_available",
        "has_override",
        "dataset_split",
    }
)

# Training code must select features from this allow-list. Identifier, split,
# and target columns stay in the table for traceability but are not features.
MODEL_FEATURE_COLUMNS = (
    "rated_power_kw",
    "max_power_kw",
    "required_kwh",
    "battery_capacity_kwh",
    "arrival_soc_pct",
    "target_soc_pct",
    "soc_gap_pct",
    "connection_window_hours",
    "required_energy_share",
    "average_required_power_kw",
    "event_hour",
    "event_weekday",
    "prior_event_count",
    "prior_delivery_ratio_mean",
    "prior_delivery_ratio_ema",
    "prior_delivery_ratio_std",
    "prior_availability_rate",
    "prior_override_rate",
)

TARGET_COLUMNS = (
    "target_dispatched_kw",
    "target_delivered_kw",
    "target_delivery_ratio",
    "target_is_available",
    "target_has_override",
)

OUTPUT_COLUMNS = (
    "resource_id",
    "event_timestamp",
    "dataset_split",
    *MODEL_FEATURE_COLUMNS,
    *TARGET_COLUMNS,
)


class TrainingDataError(ValueError):
    """Raised when source rows cannot form a safe training table."""


def _read_csv(path: Path, required_columns: frozenset[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise TrainingDataError(f"CSV file does not exist: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = frozenset(reader.fieldnames or ())
        missing = sorted(required_columns - columns)
        if missing:
            raise TrainingDataError(f"{path} is missing columns: {', '.join(missing)}")
        return list(reader)


def _finite_float(row: Mapping[str, str], column: str, row_name: str) -> float:
    try:
        value = float(row[column])
    except (KeyError, TypeError, ValueError) as exc:
        raise TrainingDataError(f"{row_name}: {column} must be numeric") from exc
    if not isfinite(value):
        raise TrainingDataError(f"{row_name}: {column} must be finite")
    return value


def _aware_datetime(value: str, field_name: str, row_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TrainingDataError(f"{row_name}: {field_name} must be ISO 8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise TrainingDataError(f"{row_name}: {field_name} must include a timezone")
    return parsed


def _boolean(value: str, field_name: str, row_name: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise TrainingDataError(f"{row_name}: {field_name} must be true or false")


def _optional_stat(values: list[float], minimum_count: int = 1) -> float | str:
    if len(values) < minimum_count:
        return ""
    return round(fmean(values), 6)


def build_training_rows(
    resources_path: Path,
    history_path: Path,
    *,
    ema_alpha: float = DEFAULT_EMA_ALPHA,
) -> list[dict[str, object]]:
    """Return deterministic, leakage-safe EV training rows."""
    if not 0.0 < ema_alpha <= 1.0:
        raise TrainingDataError("ema_alpha must be greater than 0 and at most 1")

    resource_rows = _read_csv(resources_path, RESOURCE_REQUIRED_COLUMNS)
    history_rows = _read_csv(history_path, HISTORY_REQUIRED_COLUMNS)

    resources: dict[str, dict[str, object]] = {}
    for source in resource_rows:
        resource_id = source["id"].strip()
        row_name = f"resource {resource_id or '<blank>'}"
        if not resource_id:
            raise TrainingDataError("resource id cannot be blank")
        if resource_id in resources:
            raise TrainingDataError(f"duplicate resource id: {resource_id}")
        dataset_split = source["dataset_split"].strip()
        if dataset_split not in ALLOWED_SPLITS:
            raise TrainingDataError(f"{row_name}: invalid dataset_split {dataset_split!r}")

        earliest_start = _aware_datetime(source["earliest_start"], "earliest_start", row_name)
        latest_end = _aware_datetime(source["latest_end"], "latest_end", row_name)
        connection_window_hours = (latest_end - earliest_start).total_seconds() / 3600.0
        if connection_window_hours <= 0:
            raise TrainingDataError(f"{row_name}: connection window must be positive")

        numeric = {
            column: _finite_float(source, column, row_name)
            for column in (
                "rated_power_kw",
                "required_kwh",
                "maximum_kwh",
                "max_power",
                "battery_capacity_kwh",
                "arrival_soc_pct",
                "target_soc_pct",
            )
        }
        if numeric["rated_power_kw"] <= 0 or numeric["max_power"] <= 0:
            raise TrainingDataError(f"{row_name}: charging power must be positive")
        if numeric["required_kwh"] < 0 or numeric["maximum_kwh"] <= 0:
            raise TrainingDataError(f"{row_name}: energy values are invalid")
        if numeric["required_kwh"] > numeric["maximum_kwh"]:
            raise TrainingDataError(f"{row_name}: required_kwh exceeds maximum_kwh")
        if numeric["target_soc_pct"] < numeric["arrival_soc_pct"]:
            raise TrainingDataError(f"{row_name}: target SOC is below arrival SOC")

        resources[resource_id] = {
            "dataset_split": dataset_split,
            **numeric,
            "connection_window_hours": connection_window_hours,
        }

    histories: dict[str, list[dict[str, object]]] = defaultdict(list)
    seen_events: set[tuple[str, datetime]] = set()
    for source in history_rows:
        resource_id = source["resource_id"].strip()
        row_name = f"history event for {resource_id or '<blank>'}"
        if resource_id not in resources:
            raise TrainingDataError(f"{row_name}: resource does not exist")
        dataset_split = source["dataset_split"].strip()
        expected_split = str(resources[resource_id]["dataset_split"])
        if dataset_split != expected_split:
            raise TrainingDataError(
                f"{row_name}: split {dataset_split!r} does not match resource split "
                f"{expected_split!r}"
            )
        timestamp = _aware_datetime(source["timestamp"], "timestamp", row_name)
        event_key = (resource_id, timestamp)
        if event_key in seen_events:
            raise TrainingDataError(f"duplicate history event: {resource_id} at {timestamp.isoformat()}")
        seen_events.add(event_key)

        dispatched_kw = _finite_float(source, "dispatched_kw", row_name)
        delivered_kw = _finite_float(source, "delivered_kw", row_name)
        if dispatched_kw <= 0:
            raise TrainingDataError(f"{row_name}: dispatched_kw must be positive")
        if delivered_kw < 0:
            raise TrainingDataError(f"{row_name}: delivered_kw cannot be negative")

        histories[resource_id].append(
            {
                "timestamp": timestamp,
                "dispatched_kw": dispatched_kw,
                "delivered_kw": delivered_kw,
                "is_available": _boolean(source["is_available"], "is_available", row_name),
                "has_override": _boolean(source["has_override"], "has_override", row_name),
            }
        )

    missing_history = sorted(set(resources) - set(histories))
    if missing_history:
        raise TrainingDataError(
            "resources without historical events: " + ", ".join(missing_history[:5])
        )

    output: list[dict[str, object]] = []
    for resource_id in sorted(resources):
        resource = resources[resource_id]
        previous_ratios: list[float] = []
        previous_availability: list[float] = []
        previous_overrides: list[float] = []
        previous_ema: float | None = None

        for event in sorted(histories[resource_id], key=lambda item: item["timestamp"]):
            timestamp = event["timestamp"]
            if not isinstance(timestamp, datetime):
                raise AssertionError("validated timestamp lost its datetime type")
            delivered_kw = float(event["delivered_kw"])
            dispatched_kw = float(event["dispatched_kw"])
            target_ratio = min(1.0, max(0.0, delivered_kw / dispatched_kw))

            maximum_kwh = float(resource["maximum_kwh"])
            required_kwh = float(resource["required_kwh"])
            window_hours = float(resource["connection_window_hours"])
            arrival_soc = float(resource["arrival_soc_pct"])
            target_soc = float(resource["target_soc_pct"])

            output.append(
                {
                    "resource_id": resource_id,
                    "event_timestamp": timestamp.isoformat(),
                    "dataset_split": resource["dataset_split"],
                    "rated_power_kw": resource["rated_power_kw"],
                    "max_power_kw": resource["max_power"],
                    "required_kwh": required_kwh,
                    "battery_capacity_kwh": resource["battery_capacity_kwh"],
                    "arrival_soc_pct": arrival_soc,
                    "target_soc_pct": target_soc,
                    "soc_gap_pct": round(target_soc - arrival_soc, 6),
                    "connection_window_hours": round(window_hours, 6),
                    "required_energy_share": round(required_kwh / maximum_kwh, 6),
                    "average_required_power_kw": round(required_kwh / window_hours, 6),
                    "event_hour": round(timestamp.hour + timestamp.minute / 60.0, 6),
                    "event_weekday": timestamp.weekday(),
                    "prior_event_count": len(previous_ratios),
                    "prior_delivery_ratio_mean": _optional_stat(previous_ratios),
                    "prior_delivery_ratio_ema": "" if previous_ema is None else round(previous_ema, 6),
                    "prior_delivery_ratio_std": (
                        "" if len(previous_ratios) < 2 else round(pstdev(previous_ratios), 6)
                    ),
                    "prior_availability_rate": _optional_stat(previous_availability),
                    "prior_override_rate": _optional_stat(previous_overrides),
                    "target_dispatched_kw": dispatched_kw,
                    "target_delivered_kw": delivered_kw,
                    "target_delivery_ratio": round(target_ratio, 6),
                    "target_is_available": bool(event["is_available"]),
                    "target_has_override": bool(event["has_override"]),
                }
            )

            previous_ratios.append(target_ratio)
            previous_availability.append(float(bool(event["is_available"])))
            previous_overrides.append(float(bool(event["has_override"])))
            previous_ema = (
                target_ratio
                if previous_ema is None
                else ema_alpha * target_ratio + (1.0 - ema_alpha) * previous_ema
            )

    return output


def write_training_table(rows: Iterable[Mapping[str, object]], output_path: Path) -> int:
    """Write rows with a stable schema and return the number written."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            count += 1
    return count


def prepare_ev_training_data(
    resources_path: Path = DEFAULT_RESOURCES_PATH,
    history_path: Path = DEFAULT_HISTORY_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    *,
    ema_alpha: float = DEFAULT_EMA_ALPHA,
) -> int:
    rows = build_training_rows(resources_path, history_path, ema_alpha=ema_alpha)
    return write_training_table(rows, output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resources", type=Path, default=DEFAULT_RESOURCES_PATH)
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--ema-alpha", type=float, default=DEFAULT_EMA_ALPHA)
    args = parser.parse_args()
    row_count = prepare_ev_training_data(
        args.resources,
        args.history,
        args.output,
        ema_alpha=args.ema_alpha,
    )
    print(f"Wrote {row_count} leakage-safe EV training rows to {args.output}")


if __name__ == "__main__":
    main()
