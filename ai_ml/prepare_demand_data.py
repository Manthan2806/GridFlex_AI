"""Prepare real 15-minute all-India demand and generation data for GridFlex."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


SOURCE_NAME = "India Power Grid - NLDC Daily PSP Reports"
SOURCE_REPOSITORY = "https://github.com/HalcyonVector/Grid-Sentinel"
SOURCE_DATASET_PAGE = (
    "https://www.kaggle.com/datasets/halcyonvector/"
    "india-power-grid-nldc-daily-psp-reports"
)
UPSTREAM_PROVIDER = "GRID-INDIA National Load Despatch Centre daily PSP reports"
UPSTREAM_REPORT_PAGE = "https://grid-india.in/en/reports/daily-psp-report"
SOURCE_COMMIT = "9b6ffc0f5f47fff1f86845e3a84f71aa12d45c94"
SOURCE_COMMIT_DATE_UTC = "2026-09-11T06:40:55Z"
SOURCE_FILENAME = "grid_sentinel_study2_scada.csv"
SOURCE_URL = (
    "https://raw.githubusercontent.com/HalcyonVector/Grid-Sentinel/"
    f"{SOURCE_COMMIT}/Dataset/study2_scada.csv"
)
SOURCE_SHA256 = "963d8b861ff4584c886ace27af2dd83aa909b17bf750f0805ee1900ac2dec2c8"
SOURCE_LICENSE = "CC BY-SA 4.0"
YEAR = 2025
IST = timezone(timedelta(hours=5, minutes=30))
GENERATOR_VERSION = "gridflex-nldc-scada-v2"

CORE_SOURCE_COLUMNS = (
    "demand_met_mw",
    "net_demand_met_mw",
    "solar_mw",
    "wind_mw",
    "hydro_mw",
    "thermal_mw",
    "total_gen_mw",
)
EXPECTED_TIMES = tuple(
    f"{hour:02d}:{minute:02d}"
    for hour in range(24)
    for minute in (0, 15, 30, 45)
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_source(path: Path) -> None:
    if path.exists() and _sha256(path) == SOURCE_SHA256:
        return

    temporary_path = path.with_suffix(path.suffix + ".part")
    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "GridFlex-AI"})
    try:
        with urllib.request.urlopen(request, timeout=180) as response, temporary_path.open(
            "wb"
        ) as handle:
            while chunk := response.read(1024 * 1024):
                handle.write(chunk)
        actual_sha256 = _sha256(temporary_path)
        if actual_sha256 != SOURCE_SHA256:
            raise ValueError(
                f"Source checksum mismatch: {actual_sha256} != {SOURCE_SHA256}"
            )
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _source_rows(path: Path, year: int) -> dict[date, list[dict[str, str]]]:
    rows_by_day: dict[date, list[dict[str, str]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required_columns = {"date", "time", "freq_hz", *CORE_SOURCE_COLUMNS}
        missing_columns = required_columns - set(reader.fieldnames or ())
        if missing_columns:
            raise ValueError(f"Source columns missing: {sorted(missing_columns)}")
        for row in reader:
            day = date.fromisoformat(row["date"])
            if day.year == year:
                rows_by_day[day].append(row)
    return rows_by_day


def _is_complete_day(rows: list[dict[str, str]]) -> bool:
    if len(rows) != 96:
        return False
    if tuple(sorted(row["time"] for row in rows)) != EXPECTED_TIMES:
        return False
    return all(row[column].strip() for row in rows for column in CORE_SOURCE_COLUMNS)


def _all_dates(year: int) -> list[date]:
    first = date(year, 1, 1)
    last = date(year, 12, 31)
    return [first + timedelta(days=offset) for offset in range((last - first).days + 1)]


def prepare(output_root: Path, year: int = YEAR) -> dict[str, object]:
    raw_dir = output_root / "raw" / "demand"
    processed_dir = output_root / "processed" / "demand_15min"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    raw_path = raw_dir / SOURCE_FILENAME
    _download_source(raw_path)
    rows_by_day = _source_rows(raw_path, year)
    complete_days = sorted(
        day for day, rows in rows_by_day.items() if _is_complete_day(rows)
    )
    if not complete_days:
        raise ValueError(f"No complete {year} days found in {raw_path}")

    missing_dates = sorted(set(_all_dates(year)) - set(rows_by_day))
    incomplete_days = {
        day.isoformat(): len(rows)
        for day, rows in sorted(rows_by_day.items())
        if day not in complete_days
    }
    output_path = processed_dir / f"india_nldc_scada_15min_{year}.csv"
    output_fields = (
        "timestamp",
        "block_index",
        "demand_met_mw",
        "net_demand_met_mw",
        "solar_generation_mw",
        "wind_generation_mw",
        "hydro_generation_mw",
        "thermal_generation_mw",
        "total_generation_mw",
        "frequency_hz",
        "quality_flags",
        "classification",
    )
    missing_frequency = 0
    negative_solar_rows = 0
    demand_values: list[float] = []
    solar_values: list[float] = []
    row_count = 0
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_fields)
        writer.writeheader()
        for day in complete_days:
            rows = sorted(rows_by_day[day], key=lambda row: row["time"])
            for block_index, row in enumerate(rows, start=1):
                local_time = datetime.strptime(row["time"], "%H:%M").time()
                timestamp = datetime.combine(day, local_time, tzinfo=IST).isoformat()
                quality_flags: list[str] = []
                if not row["freq_hz"].strip():
                    missing_frequency += 1
                    quality_flags.append("frequency_missing")
                if float(row["solar_mw"]) < 0:
                    negative_solar_rows += 1
                    quality_flags.append("negative_solar_source_value")
                demand_values.append(float(row["demand_met_mw"]))
                solar_values.append(float(row["solar_mw"]))
                writer.writerow(
                    {
                        "timestamp": timestamp,
                        "block_index": block_index,
                        "demand_met_mw": row["demand_met_mw"],
                        "net_demand_met_mw": row["net_demand_met_mw"],
                        "solar_generation_mw": row["solar_mw"],
                        "wind_generation_mw": row["wind_mw"],
                        "hydro_generation_mw": row["hydro_mw"],
                        "thermal_generation_mw": row["thermal_mw"],
                        "total_generation_mw": row["total_gen_mw"],
                        "frequency_hz": row["freq_hz"],
                        "quality_flags": ";".join(quality_flags) or "none",
                        "classification": "REAL/PUBLIC operational SCADA",
                    }
                )
                row_count += 1

    metadata = {
        "source": SOURCE_NAME,
        "source_repository": SOURCE_REPOSITORY,
        "source_dataset_page": SOURCE_DATASET_PAGE,
        "upstream_provider": UPSTREAM_PROVIDER,
        "upstream_report_page": UPSTREAM_REPORT_PAGE,
        "source_commit": SOURCE_COMMIT,
        "source_commit_date_utc": SOURCE_COMMIT_DATE_UTC,
        "source_download_url": SOURCE_URL,
        "source_license": SOURCE_LICENSE,
        "source_sha256": SOURCE_SHA256,
        "generator_version": GENERATOR_VERSION,
        "geographic_scope": "All-India electricity system",
        "scope_note": "National system data; it must not be described as Gujarat-only demand.",
        "year": year,
        "time_standard": "Asia/Kolkata (UTC+05:30)",
        "source_resolution": "15-minute instantaneous operational SCADA snapshots",
        "processed_resolution": "15 minutes",
        "measurement_note": (
            "Values are observed SCADA snapshots at quarter-hour timestamps, not "
            "energy averaged across each 15-minute interval."
        ),
        "classification": "REAL/PUBLIC operational SCADA",
        "transformation": [
            f"select source rows for {year}",
            "retain only days containing all 96 unique quarter-hour timestamps",
            "require demand and generation fields; do not impute missing values",
            "preserve source measurements and label known quality warnings",
            "construct timezone-aware ISO 8601 timestamps and rename selected columns",
        ],
        "source_year_rows": sum(len(rows) for rows in rows_by_day.values()),
        "source_year_days_present": len(rows_by_day),
        "retained_complete_days": len(complete_days),
        "retained_rows": row_count,
        "missing_calendar_dates": [day.isoformat() for day in missing_dates],
        "excluded_incomplete_days_and_row_counts": incomplete_days,
        "optional_frequency_missing_rows": missing_frequency,
        "negative_solar_source_rows": negative_solar_rows,
        "value_ranges": {
            "demand_met_mw": {
                "minimum": min(demand_values),
                "maximum": max(demand_values),
            },
            "solar_generation_mw": {
                "minimum": min(solar_values),
                "maximum": max(solar_values),
            },
        },
        "limitations": [
            "The data is national, not Gujarat- or Ahmedabad-specific.",
            "Source gaps and incomplete days are excluded rather than invented or imputed.",
            "Operational telemetry can contain freezes, dropouts, or erroneous values.",
            (
                "Small negative solar readings are preserved exactly as published and "
                "marked negative_solar_source_value; treat them as telemetry offsets."
            ),
            "Frequency is optional and remains blank in a small number of otherwise complete rows.",
        ],
        "files": {
            str(raw_path.relative_to(output_root)): {
                "bytes": raw_path.stat().st_size,
                "sha256": _sha256(raw_path),
                "classification": "REAL/PUBLIC source CSV derived from GRID-INDIA reports",
            },
            str(output_path.relative_to(output_root)): {
                "bytes": output_path.stat().st_size,
                "sha256": _sha256(output_path),
                "classification": "REAL/PUBLIC measurements; filtered and renamed",
            },
        },
    }
    metadata_path = output_root / "processed" / "demand_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=YEAR)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data",
    )
    args = parser.parse_args()
    print(json.dumps(prepare(args.output_root, args.year), indent=2))


if __name__ == "__main__":
    main()
