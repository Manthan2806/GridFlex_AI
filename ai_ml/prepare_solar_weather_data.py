"""Prepare the existing 2024 NASA POWER solar demonstration data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


SOURCE = "NASA POWER Hourly API"
SOURCE_URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"
LOCATION_NAME = "Ahmedabad demonstration point"
LATITUDE = 23.0225
LONGITUDE = 72.5714
START_DATE = "20240101"
END_DATE = "20241231"
REFERENCE_PV_CAPACITY_KW = 1000.0
GENERATOR_VERSION = "gridflex-nasa-power-solar-v2"


def _url() -> str:
    query = urllib.parse.urlencode(
        {
            "parameters": "ALLSKY_SFC_SW_DWN",
            "community": "RE",
            "longitude": LONGITUDE,
            "latitude": LATITUDE,
            "start": START_DATE,
            "end": END_DATE,
            "format": "JSON",
            "time-standard": "UTC",
        }
    )
    return f"{SOURCE_URL}?{query}"


def _download(url: str, path: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "GridFlex-AI"})
    with urllib.request.urlopen(request, timeout=120) as response:
        path.write_bytes(response.read())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(output_root: Path, refresh: bool = False) -> dict[str, object]:
    source_url = _url()
    raw_dir = output_root / "raw" / "solar"
    processed_dir = output_root / "processed" / "solar_15min"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "nasa_power_ahmedabad_solar_2024.json"
    if refresh or not raw_path.exists():
        _download(source_url, raw_path)

    solar = json.loads(raw_path.read_bytes())
    values = solar["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
    fill_value = float(solar["header"]["fill_value"])
    output_path = processed_dir / "nasa_power_ahmedabad_solar_15min_2024.csv"
    missing_hours = 0
    row_count = 0
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "timestamp",
                "solar_irradiance_wh_m2",
                "reference_pv_capacity_kw",
                "solar_generation_kw",
                "classification",
            ),
        )
        writer.writeheader()
        for hour_key in sorted(values):
            hour = datetime.strptime(hour_key, "%Y%m%d%H").replace(
                tzinfo=timezone.utc
            )
            raw_value = float(values[hour_key])
            irradiance = None if raw_value == fill_value else raw_value
            if irradiance is None:
                missing_hours += 1
            for minute in (0, 15, 30, 45):
                generation_kw: str | float = ""
                if irradiance is not None:
                    capacity_factor = min(1.0, max(0.0, irradiance / 1000.0))
                    generation_kw = round(
                        REFERENCE_PV_CAPACITY_KW * capacity_factor, 4
                    )
                writer.writerow(
                    {
                        "timestamp": (hour + timedelta(minutes=minute)).isoformat(),
                        "solar_irradiance_wh_m2": "" if irradiance is None else irradiance,
                        "reference_pv_capacity_kw": REFERENCE_PV_CAPACITY_KW,
                        "solar_generation_kw": generation_kw,
                        "classification": "COMPUTED from REAL/PUBLIC hourly data",
                    }
                )
                row_count += 1

    metadata = {
        "source": SOURCE,
        "source_documentation": "https://power.larc.nasa.gov/docs/services/api/temporal/hourly/",
        "source_download_url": source_url,
        "generator_version": GENERATOR_VERSION,
        "location": {
            "name": LOCATION_NAME,
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "scope_note": "Single demonstration point; not representative of all Gujarat or India.",
        },
        "period": {"start": START_DATE, "end": END_DATE},
        "time_standard": "UTC",
        "source_resolution": "hourly",
        "processed_resolution": "15 minutes",
        "resampling": "repeat each hourly average for its four 15-minute intervals",
        "classification": "COMPUTED from REAL/PUBLIC hourly data",
        "reference_pv_capacity_kw": REFERENCE_PV_CAPACITY_KW,
        "solar_15min_rows": row_count,
        "missing_solar_hours": missing_hours,
        "limitations": [
            "This legacy demonstration solar series is for 2024, not 2025.",
            "The 15-minute rows repeat hourly irradiance rather than adding observations.",
            "The PV conversion is simplified and excludes orientation, shading, inverter, temperature, and loss modelling.",
        ],
        "files": {
            str(raw_path.relative_to(output_root)): {
                "bytes": raw_path.stat().st_size,
                "sha256": _sha256(raw_path),
                "classification": "REAL/PUBLIC raw provider response",
            },
            str(output_path.relative_to(output_root)): {
                "bytes": output_path.stat().st_size,
                "sha256": _sha256(output_path),
                "classification": "COMPUTED from REAL/PUBLIC hourly data",
            },
        },
    }
    metadata_path = output_root / "processed" / "solar_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data",
    )
    args = parser.parse_args()
    print(json.dumps(prepare(args.output_root, args.refresh), indent=2))


if __name__ == "__main__":
    main()
