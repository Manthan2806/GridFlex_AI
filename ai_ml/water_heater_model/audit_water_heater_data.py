"""Audit the water-heater resource and historical-response CSV files.

This module checks data quality only. It does not alter rows, create model
features, select a model, or train a model.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import fmean
from typing import Iterable


DEFAULT_ROOT = Path("data/synthetic/water_heater")
DEFAULT_OUTPUT = Path("data/processed/water_heater/water_heater_dataset_audit.json")

RESOURCE_COLUMNS = frozenset(
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
        "data_classification",
    }
)
HISTORY_COLUMNS = frozenset(
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
        "data_classification",
    }
)
ALLOWED_SPLITS = frozenset({"train", "validation", "test"})
ALLOWED_HEATER_TYPES = frozenset({"heat_pump", "electric_resistance"})
ALLOWED_DIRECTIONS = frozenset({"reduce", "increase"})
ALLOWED_REQUESTS = frozenset({"shed", "load_up"})
ALLOWED_OUTCOMES = frozenset({"delivered", "partial", "unavailable", "override"})
LABEL_COLUMNS = (
    "delivered_kw",
    "response_ratio",
    "is_available",
    "has_override",
    "outcome",
)
PRE_DISPATCH_CANDIDATE_COLUMNS = (
    "heater_type",
    "rated_power_kw",
    "tank_capacity_l",
    "minimum_comfort_temp_c",
    "maximum_temp_c",
    "recovery_rate_c_per_hour",
    "baseline_duty_cycle",
    "timestamp-derived hour and weekday",
    "flex_direction",
    "requested_state",
    "pre_dispatch_temp_c",
    "pre_dispatch_power_kw",
    "hot_water_draw_l",
    "potential_kw",
    "strictly prior historical response features",
)


class DatasetAuditError(ValueError):
    """Raised when the audit cannot read the dataset structure."""


def _read_csv(path: Path, required: frozenset[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise DatasetAuditError(f"CSV file does not exist: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = frozenset(reader.fieldnames or ())
        missing = sorted(required - columns)
        if missing:
            raise DatasetAuditError(f"{path} is missing columns: {', '.join(missing)}")
        return list(reader)


def _number(value: str, field: str, row_name: str, failures: list[str]) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        failures.append(f"{row_name}: {field} is not numeric")
        return None
    if not math.isfinite(parsed):
        failures.append(f"{row_name}: {field} is not finite")
        return None
    return parsed


def _sha256(path: Path) -> str:
    payload = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(payload).hexdigest()


def _counts(values: Iterable[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def audit_dataset(
    resources_path: Path,
    history_path: Path,
    metadata_path: Path,
) -> dict[str, object]:
    resources = _read_csv(resources_path, RESOURCE_COLUMNS)
    history = _read_csv(history_path, HISTORY_COLUMNS)
    if not metadata_path.is_file():
        raise DatasetAuditError(f"metadata file does not exist: {metadata_path}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    failures: list[str] = []

    resource_by_id: dict[str, dict[str, str]] = {}
    for index, row in enumerate(resources, start=2):
        row_name = f"resource CSV row {index}"
        resource_id = row["id"].strip()
        if not resource_id:
            failures.append(f"{row_name}: id is blank")
        elif resource_id in resource_by_id:
            failures.append(f"{row_name}: duplicate id {resource_id}")
        else:
            resource_by_id[resource_id] = row
        if row["heater_type"] not in ALLOWED_HEATER_TYPES:
            failures.append(f"{row_name}: invalid heater_type {row['heater_type']!r}")
        if row["dataset_split"] not in ALLOWED_SPLITS:
            failures.append(f"{row_name}: invalid dataset_split {row['dataset_split']!r}")
        if row["data_classification"] != "SYNTHETIC":
            failures.append(f"{row_name}: data_classification must be SYNTHETIC")
        rated = _number(row["rated_power_kw"], "rated_power_kw", row_name, failures)
        tank = _number(row["tank_capacity_l"], "tank_capacity_l", row_name, failures)
        low = _number(row["minimum_comfort_temp_c"], "minimum_comfort_temp_c", row_name, failures)
        high = _number(row["maximum_temp_c"], "maximum_temp_c", row_name, failures)
        recovery = _number(row["recovery_rate_c_per_hour"], "recovery_rate_c_per_hour", row_name, failures)
        duty = _number(row["baseline_duty_cycle"], "baseline_duty_cycle", row_name, failures)
        if rated is not None and rated <= 0:
            failures.append(f"{row_name}: rated_power_kw must be positive")
        if tank is not None and tank <= 0:
            failures.append(f"{row_name}: tank_capacity_l must be positive")
        if low is not None and high is not None and low >= high:
            failures.append(f"{row_name}: comfort minimum must be below maximum")
        if recovery is not None and recovery <= 0:
            failures.append(f"{row_name}: recovery rate must be positive")
        if duty is not None and not 0 <= duty <= 1:
            failures.append(f"{row_name}: baseline duty cycle must be between 0 and 1")

    events_per_resource: Counter[str] = Counter()
    seen_events: set[tuple[str, str]] = set()
    timestamps: list[datetime] = []
    potentials: list[float] = []
    delivered_values: list[float] = []
    ratios: list[float] = []
    for index, row in enumerate(history, start=2):
        row_name = f"history CSV row {index}"
        resource_id = row["resource_id"].strip()
        resource = resource_by_id.get(resource_id)
        if resource is None:
            failures.append(f"{row_name}: unknown resource_id {resource_id!r}")
        else:
            events_per_resource[resource_id] += 1
            if row["dataset_split"] != resource["dataset_split"]:
                failures.append(f"{row_name}: dataset split differs from its resource")
        event_key = (resource_id, row["timestamp"])
        if event_key in seen_events:
            failures.append(f"{row_name}: duplicate resource/timestamp event")
        seen_events.add(event_key)

        if row["flex_direction"] not in ALLOWED_DIRECTIONS:
            failures.append(f"{row_name}: invalid flex_direction {row['flex_direction']!r}")
        if row["requested_state"] not in ALLOWED_REQUESTS:
            failures.append(f"{row_name}: invalid requested_state {row['requested_state']!r}")
        expected_request = "shed" if row["flex_direction"] == "reduce" else "load_up"
        if row["flex_direction"] in ALLOWED_DIRECTIONS and row["requested_state"] != expected_request:
            failures.append(f"{row_name}: direction and requested state disagree")
        if row["outcome"] not in ALLOWED_OUTCOMES:
            failures.append(f"{row_name}: invalid outcome {row['outcome']!r}")
        if row["is_available"] not in {"true", "false"}:
            failures.append(f"{row_name}: is_available must be true or false")
        if row["has_override"] not in {"true", "false"}:
            failures.append(f"{row_name}: has_override must be true or false")
        if row["data_classification"] != "SYNTHETIC":
            failures.append(f"{row_name}: data_classification must be SYNTHETIC")

        try:
            timestamp = datetime.fromisoformat(row["timestamp"])
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                failures.append(f"{row_name}: timestamp lacks timezone")
            elif timestamp.minute not in {0, 15, 30, 45} or timestamp.second != 0:
                failures.append(f"{row_name}: timestamp is not on the 15-minute grid")
            else:
                timestamps.append(timestamp)
        except ValueError:
            failures.append(f"{row_name}: timestamp is not ISO 8601")

        pre_power = _number(row["pre_dispatch_power_kw"], "pre_dispatch_power_kw", row_name, failures)
        draw = _number(row["hot_water_draw_l"], "hot_water_draw_l", row_name, failures)
        potential = _number(row["potential_kw"], "potential_kw", row_name, failures)
        delivered = _number(row["delivered_kw"], "delivered_kw", row_name, failures)
        ratio = _number(row["response_ratio"], "response_ratio", row_name, failures)
        _number(row["pre_dispatch_temp_c"], "pre_dispatch_temp_c", row_name, failures)
        if pre_power is not None and pre_power < 0:
            failures.append(f"{row_name}: pre_dispatch_power_kw cannot be negative")
        if draw is not None and draw < 0:
            failures.append(f"{row_name}: hot_water_draw_l cannot be negative")
        if potential is not None:
            potentials.append(potential)
            if potential <= 0:
                failures.append(f"{row_name}: potential_kw must be positive")
        if delivered is not None:
            delivered_values.append(delivered)
        if ratio is not None:
            ratios.append(ratio)
            if not 0 <= ratio <= 1:
                failures.append(f"{row_name}: response_ratio must be between 0 and 1")
        if potential is not None and delivered is not None:
            if delivered < 0 or delivered > potential + 1e-6:
                failures.append(f"{row_name}: delivered_kw is outside 0..potential_kw")
            if ratio is not None and abs(delivered / potential - ratio) > 1e-5:
                failures.append(f"{row_name}: response_ratio disagrees with delivered/potential")
        if resource is not None and potential is not None:
            rated = float(resource["rated_power_kw"])
            if potential > rated + 1e-6:
                failures.append(f"{row_name}: potential_kw exceeds rated power")

    expected_events = metadata.get("history_per_resource")
    if isinstance(expected_events, int):
        wrong_counts = sorted(
            resource_id
            for resource_id in resource_by_id
            if events_per_resource[resource_id] != expected_events
        )
        if wrong_counts:
            failures.append(
                f"{len(wrong_counts)} resources do not have {expected_events} history rows"
            )

    metadata_files = metadata.get("files", {})
    actual_hashes = {
        "water_heater_resources.csv": _sha256(resources_path),
        "behavior/water_heater_historical_response.csv": _sha256(history_path),
    }
    for name, actual_hash in actual_hashes.items():
        recorded = metadata_files.get(name, {}).get("sha256") if isinstance(metadata_files, dict) else None
        if recorded != actual_hash:
            failures.append(f"metadata hash does not match {name}")

    report: dict[str, object] = {
        "status": "PASS" if not failures else "FAIL",
        "dataset_classification": metadata.get("classification", "unknown"),
        "resource_rows": len(resources),
        "history_rows": len(history),
        "unique_resources_in_history": len(events_per_resource),
        "duplicate_resource_timestamp_events": len(history) - len(seen_events),
        "heater_type_counts": _counts(row["heater_type"] for row in resources),
        "resource_split_counts": _counts(row["dataset_split"] for row in resources),
        "history_split_counts": _counts(row["dataset_split"] for row in history),
        "flex_direction_counts": _counts(row["flex_direction"] for row in history),
        "outcome_counts": _counts(row["outcome"] for row in history),
        "availability_counts": _counts(row["is_available"] for row in history),
        "override_counts": _counts(row["has_override"] for row in history),
        "timestamp_start": min(timestamps).isoformat() if timestamps else None,
        "timestamp_end": max(timestamps).isoformat() if timestamps else None,
        "mean_potential_kw": round(fmean(potentials), 6) if potentials else None,
        "mean_delivered_kw": round(fmean(delivered_values), 6) if delivered_values else None,
        "mean_response_ratio": round(fmean(ratios), 6) if ratios else None,
        "label_columns_do_not_use_as_same_event_features": list(LABEL_COLUMNS),
        "candidate_pre_dispatch_inputs": list(PRE_DISPATCH_CANDIDATE_COLUMNS),
        "source_hashes_verified": all(
            metadata_files.get(name, {}).get("sha256") == value
            for name, value in actual_hashes.items()
        ) if isinstance(metadata_files, dict) else False,
        "failure_count": len(failures),
        "failures": failures[:100],
        "failure_output_truncated": len(failures) > 100,
        "limitations": metadata.get("limitations", []),
    }
    return report


def write_audit(report: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resources", type=Path, default=DEFAULT_ROOT / "water_heater_resources.csv")
    parser.add_argument(
        "--history",
        type=Path,
        default=DEFAULT_ROOT / "behavior" / "water_heater_historical_response.csv",
    )
    parser.add_argument("--metadata", type=Path, default=DEFAULT_ROOT / "water_heater_dataset_metadata.json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = audit_dataset(args.resources, args.history, args.metadata)
    write_audit(report, args.output)
    print(f"Water-heater dataset audit: {report['status']}")
    print(f"Resources: {report['resource_rows']}")
    print(f"Historical events: {report['history_rows']}")
    print(f"Failures: {report['failure_count']}")
    print(f"Wrote: {args.output}")
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
