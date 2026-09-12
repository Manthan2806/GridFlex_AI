"""Generate a transparent synthetic water-heater flexibility dataset.

The BPA CTA-2045 field study informs only the heat-pump/resistance population
mix and the set of demand-response commands. Every generated device attribute
and event outcome is synthetic and is labelled as such in the metadata.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


GENERATOR_VERSION = "gridflex-water-heater-synthetic-v1"
DEFAULT_SEED = 2806
DEFAULT_RESOURCE_COUNT = 700
DEFAULT_HISTORY_PER_RESOURCE = 30
IST = timezone(timedelta(hours=5, minutes=30))
SCENARIO_DATE = datetime(2026, 1, 15, tzinfo=IST)

RESOURCE_COLUMNS = (
    "id", "heater_type", "rated_power_kw", "tank_capacity_l",
    "minimum_comfort_temp_c", "maximum_temp_c", "recovery_rate_c_per_hour",
    "baseline_duty_cycle", "dataset_split", "data_classification",
)
HISTORY_COLUMNS = (
    "resource_id", "timestamp", "flex_direction", "requested_state",
    "pre_dispatch_temp_c", "pre_dispatch_power_kw", "hot_water_draw_l",
    "potential_kw", "delivered_kw", "response_ratio", "is_available",
    "has_override", "outcome", "dataset_split", "data_classification",
)


@dataclass(frozen=True)
class Config:
    seed: int = DEFAULT_SEED
    resource_count: int = DEFAULT_RESOURCE_COUNT
    history_per_resource: int = DEFAULT_HISTORY_PER_RESOURCE


def _split(index: int, total: int) -> str:
    fraction = index / total
    if fraction < 0.70:
        return "train"
    if fraction < 0.85:
        return "validation"
    return "test"


def _positive(value: float) -> float:
    return round(max(0.0, value), 6)


def _resource(rng: random.Random, index: int, count: int) -> dict[str, object]:
    # BPA reported 145 heat-pump and 86 electric-resistance units. This ratio,
    # not an individual BPA device record, calibrates the synthetic fleet mix.
    heater_type = "heat_pump" if rng.random() < 145 / 231 else "electric_resistance"
    if heater_type == "heat_pump":
        rated_power = rng.uniform(3.8, 5.0)
        recovery_rate = rng.uniform(4.0, 7.0)
        duty_cycle = rng.uniform(0.18, 0.38)
    else:
        rated_power = rng.uniform(4.0, 5.5)
        recovery_rate = rng.uniform(7.0, 12.0)
        duty_cycle = rng.uniform(0.12, 0.30)
    minimum_temp = rng.uniform(48.0, 51.0)
    maximum_temp = rng.uniform(57.0, 61.0)
    return {
        "id": f"wh-{index + 1:04d}",
        "heater_type": heater_type,
        "rated_power_kw": _positive(rated_power),
        "tank_capacity_l": round(rng.uniform(150.0, 300.0), 3),
        "minimum_comfort_temp_c": round(minimum_temp, 3),
        "maximum_temp_c": round(maximum_temp, 3),
        "recovery_rate_c_per_hour": round(recovery_rate, 3),
        "baseline_duty_cycle": round(duty_cycle, 6),
        "dataset_split": _split(index, count),
        "data_classification": "SYNTHETIC",
    }


def _event_timestamp(rng: random.Random, event_index: int) -> datetime:
    day_offset = 210 - event_index * 6 - rng.randint(0, 4)
    hour = rng.choices(
        (6, 7, 8, 12, 17, 18, 19, 20, 21),
        weights=(5, 8, 7, 2, 4, 8, 9, 7, 4),
        k=1,
    )[0]
    minute = rng.choice((0, 15, 30, 45))
    return (SCENARIO_DATE - timedelta(days=day_offset)).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )


def _history_event(
    rng: random.Random, resource: dict[str, object], event_index: int
) -> dict[str, object]:
    rated_power = float(resource["rated_power_kw"])
    minimum_temp = float(resource["minimum_comfort_temp_c"])
    maximum_temp = float(resource["maximum_temp_c"])
    temp_span = maximum_temp - minimum_temp
    direction = "reduce" if rng.random() < 0.78 else "increase"
    requested_state = "shed" if direction == "reduce" else "load_up"
    pre_temp = rng.triangular(
        minimum_temp - 2.0, maximum_temp, minimum_temp + temp_span * 0.58
    )
    hot_water_draw = max(0.0, rng.gauss(13.0 if event_index % 5 else 32.0, 10.0))

    if direction == "reduce":
        pre_power = rated_power * rng.uniform(0.55, 1.0)
        potential = pre_power
        thermal_margin = (pre_temp - minimum_temp) / max(temp_span, 0.1)
    else:
        pre_power = rated_power * rng.uniform(0.0, 0.25)
        potential = rated_power - pre_power
        thermal_margin = (maximum_temp - pre_temp) / max(temp_span, 0.1)

    thermal_margin = min(1.0, max(0.0, thermal_margin))
    availability_probability = min(
        0.98,
        max(0.20, 0.58 + 0.38 * thermal_margin - min(hot_water_draw / 180.0, 0.25)),
    )
    is_available = rng.random() < availability_probability
    override_probability = min(
        0.80,
        max(0.01, 0.04 + 0.42 * (1.0 - thermal_margin) + hot_water_draw / 240.0),
    )
    has_override = rng.random() < override_probability

    if not is_available:
        ratio = rng.uniform(0.0, 0.08)
        outcome = "unavailable"
    elif has_override:
        ratio = rng.uniform(0.0, 0.30)
        outcome = "override"
    else:
        ratio = min(1.0, max(0.0, rng.gauss(0.68 + 0.27 * thermal_margin, 0.10)))
        outcome = "delivered" if ratio >= 0.80 else "partial"

    return {
        "resource_id": resource["id"],
        "timestamp": _event_timestamp(rng, event_index).isoformat(),
        "flex_direction": direction,
        "requested_state": requested_state,
        "pre_dispatch_temp_c": round(pre_temp, 3),
        "pre_dispatch_power_kw": _positive(pre_power),
        "hot_water_draw_l": round(hot_water_draw, 3),
        "potential_kw": _positive(potential),
        "delivered_kw": _positive(potential * ratio),
        "response_ratio": round(ratio, 6),
        "is_available": str(is_available).lower(),
        "has_override": str(has_override).lower(),
        "outcome": outcome,
        "dataset_split": resource["dataset_split"],
        "data_classification": "SYNTHETIC",
    }


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    # Git may check CSV files out with CRLF on Windows. Normalize line endings
    # so the provenance hash represents the CSV content on every platform.
    payload = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(payload).hexdigest()


def generate(output_root: Path, config: Config = Config()) -> dict[str, object]:
    if config.resource_count < 1 or config.history_per_resource < 1:
        raise ValueError("resource_count and history_per_resource must be positive")
    rng = random.Random(config.seed)
    resources = [_resource(rng, index, config.resource_count) for index in range(config.resource_count)]
    history = [
        _history_event(rng, resource, event_index)
        for resource in resources
        for event_index in range(config.history_per_resource)
    ]
    history.sort(key=lambda row: (str(row["resource_id"]), str(row["timestamp"])))

    resources_path = output_root / "water_heater_resources.csv"
    history_path = output_root / "behavior" / "water_heater_historical_response.csv"
    metadata_path = output_root / "water_heater_dataset_metadata.json"
    _write_csv(resources_path, RESOURCE_COLUMNS, resources)
    _write_csv(history_path, HISTORY_COLUMNS, history)

    type_counts = {
        heater_type: sum(row["heater_type"] == heater_type for row in resources)
        for heater_type in ("heat_pump", "electric_resistance")
    }
    split_counts = {
        split: sum(row["dataset_split"] == split for row in resources)
        for split in ("train", "validation", "test")
    }
    metadata: dict[str, object] = {
        **asdict(config),
        "generator_version": GENERATOR_VERSION,
        "scenario_date": SCENARIO_DATE.isoformat(),
        "time_grid_minutes": 15,
        "resource_count": len(resources),
        "history_row_count": len(history),
        "heater_type_counts": type_counts,
        "resource_split_counts": split_counts,
        "split_rule": "resource-level 70/15/15",
        "classification": "SYNTHETIC",
        "hash_normalization": "CSV line endings normalized to LF before SHA-256",
        "calibration_source": {
            "name": "BPA CTA-2045 Water Heater Demonstration Final Report",
            "url": "https://www.bpa.gov/-/media/Aep/energy-efficiency/demand-response/20181118-cta-2045-final-report.pdf",
            "facts_used": [
                "145 heat-pump and 86 electric-resistance heaters",
                "CTA-2045 command categories include shed, load up, and customer override",
            ],
        },
        "field_provenance": {
            "REAL": [],
            "COMPUTED_FROM_REAL": [],
            "SYNTHETIC": [
                "all resource attributes",
                "all event timestamps, states, temperatures, draws, availability, overrides, and outcomes",
                "potential_kw, delivered_kw, and response_ratio",
            ],
        },
        "files": {
            str(resources_path.relative_to(output_root)).replace("\\", "/"): {
                "rows": len(resources), "sha256": _sha256(resources_path),
            },
            str(history_path.relative_to(output_root)).replace("\\", "/"): {
                "rows": len(history), "sha256": _sha256(history_path),
            },
        },
        "limitations": [
            "This is not BPA device-level telemetry and is not real household data.",
            "Only the published BPA heater-type mix and command vocabulary calibrate the generator.",
            "Temperature, hot-water draw, availability, overrides, and response outcomes are synthetic.",
            "The data supports prototype development only; it is not field validation evidence.",
        ],
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path("data/synthetic/water_heater"))
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--resource-count", type=int, default=DEFAULT_RESOURCE_COUNT)
    parser.add_argument("--history-per-resource", type=int, default=DEFAULT_HISTORY_PER_RESOURCE)
    args = parser.parse_args()
    metadata = generate(
        args.output_root,
        Config(args.seed, args.resource_count, args.history_per_resource),
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
