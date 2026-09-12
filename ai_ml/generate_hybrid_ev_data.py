"""Build 700 GridFlex EVs from real ACN sessions plus explicit synthetic fields."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import random
import statistics
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


ACN_REPOSITORY = "tongxin-li/ACN-Data-Static"
ACN_COMMIT = "abb7cf15cc7108913e965d4375cc7270d532b65f"
GENERATOR_VERSION = "gridflex-acn-hybrid-ev-v1"
DEFAULT_SEED = 2806
DEFAULT_RESOURCE_COUNT = 700
DEFAULT_HISTORY_PER_RESOURCE = 30
IST = timezone(timedelta(hours=5, minutes=30))
SCENARIO_DATE = datetime(2026, 1, 15, tzinfo=IST)


@dataclass(frozen=True)
class Config:
    seed: int = DEFAULT_SEED
    resource_count: int = DEFAULT_RESOURCE_COUNT
    history_per_resource: int = DEFAULT_HISTORY_PER_RESOURCE
    generator_version: str = GENERATOR_VERSION


def _request_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "GridFlex-AI"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def _tree(sha: str) -> list[dict]:
    url = f"https://api.github.com/repos/{ACN_REPOSITORY}/git/trees/{sha}"
    return _request_json(url)["tree"]


def _entry(entries: list[dict], name: str) -> dict:
    return next(item for item in entries if item["path"] == name)


def _list_session_files() -> list[str]:
    root = _tree(ACN_COMMIT)
    time_series = _entry(root, "time series data")
    paths: list[str] = []
    for site in _tree(time_series["sha"]):
        if site["type"] != "tree":
            continue
        for garage in _tree(site["sha"]):
            if garage["type"] != "tree":
                continue
            for item in _tree(garage["sha"]):
                if item["type"] == "blob" and item["path"].endswith(".csv.gz"):
                    paths.append(
                        f"time series data/{site['path']}/{garage['path']}/{item['path']}"
                    )
    return paths


def _number(value: object) -> float | None:
    try:
        result = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return result


def _download_summary(path: str) -> dict[str, object]:
    encoded = urllib.parse.quote(path, safe="/")
    url = (
        f"https://raw.githubusercontent.com/{ACN_REPOSITORY}/"
        f"{ACN_COMMIT}/{encoded}"
    )
    request = urllib.request.Request(url, headers={"User-Agent": "GridFlex-AI"})
    with urllib.request.urlopen(request, timeout=90) as response:
        compressed = response.read()
    text = gzip.decompress(compressed).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows or not reader.fieldnames:
        raise ValueError(f"ACN session has no data: {path}")

    def find_column(fragment: str) -> str:
        for field in reader.fieldnames or ():
            if fragment in field.lower():
                return field
        raise ValueError(f"Missing {fragment!r} column in {path}")

    timestamp_column = reader.fieldnames[0]
    energy_column = find_column("energy delivered")
    power_column = find_column("power")
    pilot_column = find_column("pilot")
    powers = [value for row in rows if (value := _number(row[power_column])) is not None]
    pilots = [value for row in rows if (value := _number(row[pilot_column])) is not None]
    energies = [value for row in rows if (value := _number(row[energy_column])) is not None]
    if not powers or not energies:
        raise ValueError(f"ACN session lacks usable power/energy values: {path}")
    parts = path.split("/")
    return {
        "source_session_path": path,
        "site": parts[1],
        "garage": parts[2],
        "connection_time": rows[0][timestamp_column],
        "disconnect_time": rows[-1][timestamp_column],
        "energy_delivered_kwh": round(max(energies), 5),
        "maximum_observed_power_kw": round(max(powers), 5),
        "maximum_pilot_a": round(max(pilots), 5) if pilots else "",
        "source_compressed_bytes": len(compressed),
    }


def _safe_download_summary(path: str) -> dict[str, object] | None:
    """Return None for unusable/corrupt source sessions so they are excluded."""
    try:
        return _download_summary(path)
    except (OSError, UnicodeError, ValueError, urllib.error.URLError):
        return None


def _parse_acn_time(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(IST)


def _scenario_window(summary: dict[str, object]) -> tuple[datetime, datetime]:
    start = _parse_acn_time(str(summary["connection_time"]))
    end = _parse_acn_time(str(summary["disconnect_time"]))
    duration = max(timedelta(minutes=15), end - start)
    scenario_start = SCENARIO_DATE.replace(
        hour=start.hour, minute=(start.minute // 15) * 15
    )
    return scenario_start, scenario_start + duration


def _split(index: int, total: int) -> str:
    fraction = index / total
    return "train" if fraction < 0.70 else "validation" if fraction < 0.85 else "test"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def generate(config: Config, output_root: Path) -> dict[str, object]:
    rng = random.Random(config.seed)
    all_paths = sorted(_list_session_files())
    if len(all_paths) < config.resource_count:
        raise ValueError("ACN archive contains fewer sessions than requested")
    candidate_paths = list(all_paths)
    rng.shuffle(candidate_paths)
    summaries: list[dict[str, object]] = []
    examined_count = 0
    with ThreadPoolExecutor(max_workers=16) as executor:
        for offset in range(0, len(candidate_paths), 1_000):
            batch = candidate_paths[offset : offset + 1_000]
            examined_count += len(batch)
            valid = executor.map(_safe_download_summary, batch)
            summaries.extend(item for item in valid if item is not None)
            if len(summaries) >= config.resource_count:
                break
    summaries = summaries[: config.resource_count]
    if len(summaries) < config.resource_count:
        raise ValueError("Could not obtain enough valid ACN sessions")

    source_dir = output_root / "source_samples"
    ev_dir = output_root / "ev"
    behaviour_dir = output_root / "behavior"
    for directory in (source_dir, ev_dir, behaviour_dir):
        directory.mkdir(parents=True, exist_ok=True)

    source_fields = tuple(summaries[0])
    source_path = source_dir / "acn_session_summaries.csv"
    resource_path = ev_dir / "ev_resources.csv"
    behaviour_path = behaviour_dir / "ev_historical_response.csv"
    source_rows: list[dict[str, object]] = []
    resource_rows: list[dict[str, object]] = []
    behaviour_rows: list[dict[str, object]] = []

    for index, summary in enumerate(summaries):
        resource_id = f"ev_{index + 1:04d}"
        dataset_split = _split(index, config.resource_count)
        summary = {**summary, "resource_id": resource_id}
        source_rows.append(summary)
        start, end = _scenario_window(summary)
        duration_hours = max(0.25, (end - start).total_seconds() / 3600)
        observed_max = max(1.4, float(summary["maximum_observed_power_kw"]))
        rated_power_kw = min(22.0, round(observed_max, 2))
        delivered_kwh = float(summary["energy_delivered_kwh"])

        # ACN does not expose battery capacity or SOC; these fields are synthetic.
        battery_capacity_kwh = round(rng.uniform(max(35.0, delivered_kwh * 1.4), 100.0), 2)
        maximum_kwh = round(
            min(battery_capacity_kwh, rated_power_kw * duration_hours), 3
        )
        required_kwh = min(round(max(0.01, delivered_kwh), 3), maximum_kwh)
        soc_gain = 100.0 * required_kwh / battery_capacity_kwh
        arrival_soc_pct = round(rng.uniform(10.0, max(11.0, 90.0 - soc_gain)), 1)
        target_soc_pct = round(min(100.0, arrival_soc_pct + soc_gain), 1)

        # Priors are synthetic because ACN has no explicit override/failure labels.
        assumed_availability = rng.uniform(0.86, 0.99)
        assumed_override = rng.uniform(0.02, 0.22)
        baseline_ratio = min(1.0, delivered_kwh / max(0.001, rated_power_kw * duration_hours))
        baseline_ratio = max(0.55, baseline_ratio)

        resource_rows.append(
            {
                "id": resource_id,
                "type": "ev",
                "location_id": f"simulation_feeder_{index % 10 + 1:02d}",
                "rated_power_kw": rated_power_kw,
                "earliest_start": start.isoformat(),
                "latest_end": end.isoformat(),
                "required_kwh": required_kwh,
                "minimum_kwh": round(required_kwh * 0.8, 3),
                "maximum_kwh": maximum_kwh,
                "minimum_duration": 15,
                "maximum_duration": max(15, int(duration_hours * 60)),
                "deadline": end.isoformat(),
                "min_power": min(1.4, rated_power_kw),
                "max_power": rated_power_kw,
                "override_rate": round(assumed_override, 4),
                "availability_rate": round(assumed_availability, 4),
                "state": "available",
                "battery_capacity_kwh": battery_capacity_kwh,
                "arrival_soc_pct": arrival_soc_pct,
                "target_soc_pct": target_soc_pct,
                "dataset_split": dataset_split,
                "acn_source_session": summary["source_session_path"],
            }
        )

        for history_index in range(config.history_per_resource):
            timestamp = start - timedelta(days=config.history_per_resource - history_index)
            dispatched_kw = round(rng.uniform(0.4, 1.0) * rated_power_kw, 3)
            is_available = rng.random() < assumed_availability
            has_override = is_available and rng.random() < assumed_override
            if not is_available:
                delivered = 0.0
            else:
                ratio = min(1.0, max(0.0, rng.gauss(baseline_ratio, 0.06)))
                if has_override:
                    ratio *= rng.uniform(0.15, 0.70)
                delivered = round(dispatched_kw * ratio, 3)
            behaviour_rows.append(
                {
                    "resource_id": resource_id,
                    "timestamp": timestamp.isoformat(),
                    "dispatched_kw": dispatched_kw,
                    "delivered_kw": delivered,
                    "is_available": str(is_available).lower(),
                    "has_override": str(has_override).lower(),
                    "dataset_split": dataset_split,
                    "provenance": "synthetic outcome calibrated from linked ACN session",
                }
            )

    def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    write_csv(source_path, source_rows)
    write_csv(resource_path, resource_rows)
    write_csv(behaviour_path, behaviour_rows)
    files = {}
    for path, classification in (
        (source_path, "COMPUTED summary of REAL/PUBLIC ACN data"),
        (resource_path, "HYBRID: ACN-derived + SYNTHETIC"),
        (behaviour_path, "SYNTHETIC, calibrated from linked ACN session"),
    ):
        files[str(path.relative_to(output_root))] = {
            "rows": sum(1 for _ in path.open(encoding="utf-8")) - 1,
            "sha256": _sha256(path),
            "classification": classification,
        }

    metadata = {
        **asdict(config),
        "source": "ACN-Data Static",
        "source_url": f"https://github.com/{ACN_REPOSITORY}",
        "source_commit_reference": ACN_COMMIT,
        "available_acn_sessions": len(all_paths),
        "sampled_acn_sessions": len(summaries),
        "candidate_sessions_examined": examined_count,
        "sample_method": "sorted paths then seeded random sample without replacement",
        "geographic_scope": "ACN US workplace sites; GridFlex locations are synthetic",
        "scenario_date": SCENARIO_DATE.isoformat(),
        "split_rule": "resource-level 70/15/15",
        "files": files,
        "field_provenance": {
            "ACN-derived": [
                "arrival/departure pattern",
                "delivered energy",
                "observed charging power",
                "source site and session",
            ],
            "synthetic": [
                "battery capacity",
                "arrival/target SOC",
                "override and availability priors",
                "historical outcomes",
                "GridFlex location and state",
            ],
        },
        "limitations": [
            "ACN observations are US workplace charging sessions, not Indian residential EV data.",
            "One sampled ACN session anchors each virtual EV; it is not a persistent real vehicle identity.",
            "Overrides, failures, battery capacity, SOC, and repeated history are synthetic.",
        ],
    }
    metadata_path = output_root / "ev_dataset_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--resource-count", type=int, default=DEFAULT_RESOURCE_COUNT)
    parser.add_argument("--history-per-resource", type=int, default=DEFAULT_HISTORY_PER_RESOURCE)
    args = parser.parse_args()
    result = generate(
        Config(args.seed, args.resource_count, args.history_per_resource),
        args.output_root,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
