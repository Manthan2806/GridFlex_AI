"""Create leakage-safe water-heater training examples.

Each output row represents one dispatch event. Historical features are built
strictly from earlier events for the same heater. Current-event outcomes and
hot-water draw are retained only as target/diagnostic columns.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import fmean, pstdev
from typing import Mapping


DEFAULT_RESOURCES = Path("data/synthetic/water_heater/water_heater_resources.csv")
DEFAULT_HISTORY = Path(
    "data/synthetic/water_heater/behavior/water_heater_historical_response.csv"
)
DEFAULT_OUTPUT = Path(
    "data/processed/water_heater_training/water_heater_training_examples.csv"
)
DEFAULT_METADATA = Path(
    "data/processed/water_heater_training/water_heater_training_metadata.json"
)
DEFAULT_EMA_ALPHA = 0.35
ALLOWED_SPLITS = frozenset({"train", "validation", "test"})

RESOURCE_REQUIRED_COLUMNS = frozenset(
    {
        "id",
        "heater_type",
        "rated_power_kw",
        "tank_capacity_l",
        "minimum_comfort_temp_c",
        "maximum_temp_c",
        "recovery_rate_c_per_hour",
        "baseline_duty_cycle",
        "dataset_split",
    }
)
HISTORY_REQUIRED_COLUMNS = frozenset(
    {
        "resource_id",
        "timestamp",
        "flex_direction",
        "requested_state",
        "pre_dispatch_temp_c",
        "pre_dispatch_power_kw",
        "hot_water_draw_l",
        "potential_kw",
        "delivered_kw",
        "response_ratio",
        "is_available",
        "has_override",
        "outcome",
        "dataset_split",
    }
)

# Model-training code must select inputs only from this explicit allow-list.
MODEL_FEATURE_COLUMNS = (
    "heater_type_heat_pump",
    "rated_power_kw",
    "tank_capacity_l",
    "minimum_comfort_temp_c",
    "maximum_temp_c",
    "temperature_band_c",
    "recovery_rate_c_per_hour",
    "baseline_duty_cycle",
    "event_hour",
    "event_weekday",
    "flex_direction_reduce",
    "pre_dispatch_temp_c",
    "pre_dispatch_power_kw",
    "directional_temperature_margin_c",
    "directional_temperature_margin_fraction",
    "potential_kw",
    "prior_event_count",
    "prior_response_ratio_mean",
    "prior_response_ratio_ema",
    "prior_response_ratio_std",
    "prior_delivered_kw_mean",
    "prior_availability_rate",
    "prior_override_rate",
)

TARGET_COLUMNS = (
    "target_delivered_kw",
    "target_response_ratio",
    "target_is_available",
    "target_has_override",
    "target_outcome",
    "target_hot_water_draw_l",
)

OUTPUT_COLUMNS = (
    "resource_id",
    "event_timestamp",
    "dataset_split",
    *MODEL_FEATURE_COLUMNS,
    *TARGET_COLUMNS,
)


class TrainingDataError(ValueError):
    """Raised when source data cannot produce a safe training table."""


def _read_csv(path: Path, required: frozenset[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise TrainingDataError(f"CSV file does not exist: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = frozenset(reader.fieldnames or ())
        missing = sorted(required - columns)
        if missing:
            raise TrainingDataError(f"{path} is missing columns: {', '.join(missing)}")
        return list(reader)


def _number(row: Mapping[str, str], field: str, row_name: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise TrainingDataError(f"{row_name}: {field} must be numeric") from exc
    if not math.isfinite(value):
        raise TrainingDataError(f"{row_name}: {field} must be finite")
    return value


def _boolean(row: Mapping[str, str], field: str, row_name: str) -> bool:
    value = row[field].strip().lower()
    if value == "true":
        return True
    if value == "false":
        return False
    raise TrainingDataError(f"{row_name}: {field} must be true or false")


def _timestamp(row: Mapping[str, str], row_name: str) -> datetime:
    try:
        value = datetime.fromisoformat(row["timestamp"])
    except (KeyError, ValueError) as exc:
        raise TrainingDataError(f"{row_name}: timestamp must be ISO 8601") from exc
    if value.tzinfo is None or value.utcoffset() is None:
        raise TrainingDataError(f"{row_name}: timestamp must include a timezone")
    if value.minute not in {0, 15, 30, 45} or value.second != 0 or value.microsecond != 0:
        raise TrainingDataError(f"{row_name}: timestamp must be on the 15-minute grid")
    return value


def _optional_mean(values: list[float]) -> float | str:
    return round(fmean(values), 6) if values else ""


def build_training_rows(
    resources_path: Path,
    history_path: Path,
    *,
    ema_alpha: float = DEFAULT_EMA_ALPHA,
) -> list[dict[str, object]]:
    """Return deterministic rows with prior-only behavioral features."""
    if not 0 < ema_alpha <= 1:
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
        split = source["dataset_split"].strip()
        if split not in ALLOWED_SPLITS:
            raise TrainingDataError(f"{row_name}: invalid dataset_split {split!r}")
        heater_type = source["heater_type"].strip()
        if heater_type not in {"heat_pump", "electric_resistance"}:
            raise TrainingDataError(f"{row_name}: invalid heater_type {heater_type!r}")
        numeric = {
            field: _number(source, field, row_name)
            for field in (
                "rated_power_kw",
                "tank_capacity_l",
                "minimum_comfort_temp_c",
                "maximum_temp_c",
                "recovery_rate_c_per_hour",
                "baseline_duty_cycle",
            )
        }
        if numeric["rated_power_kw"] <= 0 or numeric["tank_capacity_l"] <= 0:
            raise TrainingDataError(f"{row_name}: power and tank capacity must be positive")
        if numeric["minimum_comfort_temp_c"] >= numeric["maximum_temp_c"]:
            raise TrainingDataError(f"{row_name}: temperature band is invalid")
        if numeric["recovery_rate_c_per_hour"] <= 0:
            raise TrainingDataError(f"{row_name}: recovery rate must be positive")
        if not 0 <= numeric["baseline_duty_cycle"] <= 1:
            raise TrainingDataError(f"{row_name}: baseline duty cycle must be within 0..1")
        resources[resource_id] = {
            "heater_type": heater_type,
            "dataset_split": split,
            **numeric,
        }

    histories: dict[str, list[dict[str, object]]] = defaultdict(list)
    seen: set[tuple[str, datetime]] = set()
    for source in history_rows:
        resource_id = source["resource_id"].strip()
        row_name = f"history event for {resource_id or '<blank>'}"
        if resource_id not in resources:
            raise TrainingDataError(f"{row_name}: resource does not exist")
        split = source["dataset_split"].strip()
        if split != resources[resource_id]["dataset_split"]:
            raise TrainingDataError(f"{row_name}: split does not match its resource")
        timestamp = _timestamp(source, row_name)
        key = (resource_id, timestamp)
        if key in seen:
            raise TrainingDataError(f"duplicate event: {resource_id} at {timestamp.isoformat()}")
        seen.add(key)
        direction = source["flex_direction"].strip()
        if direction not in {"reduce", "increase"}:
            raise TrainingDataError(f"{row_name}: invalid flex_direction {direction!r}")
        expected_request = "shed" if direction == "reduce" else "load_up"
        if source["requested_state"].strip() != expected_request:
            raise TrainingDataError(f"{row_name}: direction and request disagree")
        potential = _number(source, "potential_kw", row_name)
        delivered = _number(source, "delivered_kw", row_name)
        ratio = _number(source, "response_ratio", row_name)
        if potential <= 0 or delivered < 0 or delivered > potential + 1e-6:
            raise TrainingDataError(f"{row_name}: flexibility values are outside physical bounds")
        if not 0 <= ratio <= 1 or abs(delivered / potential - ratio) > 1e-5:
            raise TrainingDataError(f"{row_name}: response ratio is inconsistent")
        histories[resource_id].append(
            {
                "timestamp": timestamp,
                "direction": direction,
                "pre_temp": _number(source, "pre_dispatch_temp_c", row_name),
                "pre_power": _number(source, "pre_dispatch_power_kw", row_name),
                "hot_water_draw": _number(source, "hot_water_draw_l", row_name),
                "potential": potential,
                "delivered": delivered,
                "ratio": ratio,
                "available": _boolean(source, "is_available", row_name),
                "override": _boolean(source, "has_override", row_name),
                "outcome": source["outcome"].strip(),
            }
        )

    output: list[dict[str, object]] = []
    for resource_id in sorted(resources):
        resource = resources[resource_id]
        events = sorted(histories[resource_id], key=lambda event: event["timestamp"])
        prior_ratios: list[float] = []
        prior_delivered: list[float] = []
        prior_available: list[float] = []
        prior_overrides: list[float] = []
        ema: float | None = None
        low = float(resource["minimum_comfort_temp_c"])
        high = float(resource["maximum_temp_c"])
        temperature_band = high - low

        for event in events:
            timestamp = event["timestamp"]
            direction = str(event["direction"])
            pre_temp = float(event["pre_temp"])
            if direction == "reduce":
                margin = max(0.0, pre_temp - low)
            else:
                margin = max(0.0, high - pre_temp)
            output.append(
                {
                    "resource_id": resource_id,
                    "event_timestamp": timestamp.isoformat(),
                    "dataset_split": resource["dataset_split"],
                    "heater_type_heat_pump": int(resource["heater_type"] == "heat_pump"),
                    "rated_power_kw": round(float(resource["rated_power_kw"]), 6),
                    "tank_capacity_l": round(float(resource["tank_capacity_l"]), 6),
                    "minimum_comfort_temp_c": round(low, 6),
                    "maximum_temp_c": round(high, 6),
                    "temperature_band_c": round(temperature_band, 6),
                    "recovery_rate_c_per_hour": round(float(resource["recovery_rate_c_per_hour"]), 6),
                    "baseline_duty_cycle": round(float(resource["baseline_duty_cycle"]), 6),
                    "event_hour": round(timestamp.hour + timestamp.minute / 60, 6),
                    "event_weekday": timestamp.weekday(),
                    "flex_direction_reduce": int(direction == "reduce"),
                    "pre_dispatch_temp_c": round(pre_temp, 6),
                    "pre_dispatch_power_kw": round(float(event["pre_power"]), 6),
                    "directional_temperature_margin_c": round(margin, 6),
                    "directional_temperature_margin_fraction": round(
                        min(1.0, margin / temperature_band), 6
                    ),
                    "potential_kw": round(float(event["potential"]), 6),
                    "prior_event_count": len(prior_ratios),
                    "prior_response_ratio_mean": _optional_mean(prior_ratios),
                    "prior_response_ratio_ema": round(ema, 6) if ema is not None else "",
                    "prior_response_ratio_std": (
                        round(pstdev(prior_ratios), 6) if len(prior_ratios) >= 2 else ""
                    ),
                    "prior_delivered_kw_mean": _optional_mean(prior_delivered),
                    "prior_availability_rate": _optional_mean(prior_available),
                    "prior_override_rate": _optional_mean(prior_overrides),
                    "target_delivered_kw": round(float(event["delivered"]), 6),
                    "target_response_ratio": round(float(event["ratio"]), 6),
                    "target_is_available": int(bool(event["available"])),
                    "target_has_override": int(bool(event["override"])),
                    "target_outcome": event["outcome"],
                    # The current draw affected the simulated outcome and is not
                    # assumed to be known before dispatch.
                    "target_hot_water_draw_l": round(float(event["hot_water_draw"]), 6),
                }
            )
            ratio = float(event["ratio"])
            prior_ratios.append(ratio)
            prior_delivered.append(float(event["delivered"]))
            prior_available.append(float(bool(event["available"])))
            prior_overrides.append(float(bool(event["override"])))
            ema = ratio if ema is None else ema_alpha * ratio + (1 - ema_alpha) * ema
    return output


def _canonical_sha256(path: Path) -> str:
    payload = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(payload).hexdigest()


def write_training_data(
    rows: list[dict[str, object]],
    output_path: Path,
    metadata_path: Path,
    *,
    resources_path: Path,
    history_path: Path,
    ema_alpha: float,
) -> dict[str, object]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    split_counts = {
        split: sum(row["dataset_split"] == split for row in rows)
        for split in ("train", "validation", "test")
    }
    metadata: dict[str, object] = {
        "preparation_version": "gridflex-water-heater-training-v1",
        "row_count": len(rows),
        "split_counts": split_counts,
        "ema_alpha": ema_alpha,
        "split_rule": "resource-level split copied unchanged from source resources",
        "history_rule": "prior features use only earlier timestamps for the same resource",
        "feature_columns": list(MODEL_FEATURE_COLUMNS),
        "target_and_diagnostic_columns": list(TARGET_COLUMNS),
        "excluded_same_event_feature": "hot_water_draw_l is retained only as target_hot_water_draw_l",
        "source_files": {
            str(resources_path).replace("\\", "/"): _canonical_sha256(resources_path),
            str(history_path).replace("\\", "/"): _canonical_sha256(history_path),
        },
        "output_file": {
            "path": str(output_path).replace("\\", "/"),
            "canonical_sha256": _canonical_sha256(output_path),
        },
        "classification": "COMPUTED from SYNTHETIC source rows",
        "limitations": [
            "All source device attributes and outcomes are synthetic.",
            "This table supports offline prototype development, not field validation.",
            "Blank prior-history fields represent cold start and require declared model-time handling.",
        ],
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def prepare(
    resources_path: Path = DEFAULT_RESOURCES,
    history_path: Path = DEFAULT_HISTORY,
    output_path: Path = DEFAULT_OUTPUT,
    metadata_path: Path = DEFAULT_METADATA,
    *,
    ema_alpha: float = DEFAULT_EMA_ALPHA,
) -> dict[str, object]:
    rows = build_training_rows(resources_path, history_path, ema_alpha=ema_alpha)
    return write_training_data(
        rows,
        output_path,
        metadata_path,
        resources_path=resources_path,
        history_path=history_path,
        ema_alpha=ema_alpha,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resources", type=Path, default=DEFAULT_RESOURCES)
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--ema-alpha", type=float, default=DEFAULT_EMA_ALPHA)
    args = parser.parse_args()
    metadata = prepare(
        args.resources,
        args.history,
        args.output,
        args.metadata,
        ema_alpha=args.ema_alpha,
    )
    print(f"Wrote {metadata['row_count']} leakage-safe water-heater rows to {args.output}")
    print(f"Feature columns: {len(metadata['feature_columns'])}")
    print(f"Target/diagnostic columns: {len(metadata['target_and_diagnostic_columns'])}")


if __name__ == "__main__":
    main()
