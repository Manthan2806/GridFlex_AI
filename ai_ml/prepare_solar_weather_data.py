"""Download and prepare NASA POWER solar/weather data for the MVP demo."""

from __future__ import annotations

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
GENERATOR_VERSION = "gridflex-nasa-power-v1"


def _url(parameters: str) -> str:
    query = urllib.parse.urlencode(
        {
            "parameters": parameters,
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


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "GridFlex-AI"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _timestamp(key: str) -> datetime:
    return datetime.strptime(key, "%Y%m%d%H").replace(tzinfo=timezone.utc)


def _valid(value: float, fill_value: float) -> float | None:
    return None if value == fill_value else float(value)


def prepare(output_root: Path) -> dict[str, object]:
    solar_url = _url("ALLSKY_SFC_SW_DWN")
    weather_url = _url("T2M,RH2M")
    solar_bytes = _download(solar_url)
    weather_bytes = _download(weather_url)

    raw_solar_dir = output_root / "raw" / "solar"
    raw_weather_dir = output_root / "raw" / "weather"
    processed_solar_dir = output_root / "processed" / "solar_15min"
    processed_weather_dir = output_root / "processed" / "weather_15min"
    for directory in (
        raw_solar_dir,
        raw_weather_dir,
        processed_solar_dir,
        processed_weather_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    raw_solar_path = raw_solar_dir / "nasa_power_ahmedabad_solar_2024.json"
    raw_weather_path = raw_weather_dir / "nasa_power_ahmedabad_weather_2024.json"
    raw_solar_path.write_bytes(solar_bytes)
    raw_weather_path.write_bytes(weather_bytes)

    solar = json.loads(solar_bytes)
    weather = json.loads(weather_bytes)
    solar_values = solar["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
    temperature_values = weather["properties"]["parameter"]["T2M"]
    humidity_values = weather["properties"]["parameter"]["RH2M"]
    solar_fill = float(solar["header"]["fill_value"])
    weather_fill = float(weather["header"]["fill_value"])
    common_hours = sorted(
        set(solar_values) & set(temperature_values) & set(humidity_values)
    )

    solar_path = processed_solar_dir / "nasa_power_ahmedabad_solar_15min_2024.csv"
    weather_path = (
        processed_weather_dir / "nasa_power_ahmedabad_weather_15min_2024.csv"
    )
    missing_solar = 0
    missing_weather = 0
    solar_rows = 0
    weather_rows = 0
    with solar_path.open("w", newline="", encoding="utf-8") as solar_handle, (
        weather_path.open("w", newline="", encoding="utf-8")
    ) as weather_handle:
        solar_writer = csv.DictWriter(
            solar_handle,
            fieldnames=(
                "timestamp",
                "solar_irradiance_wh_m2",
                "reference_pv_capacity_kw",
                "solar_generation_kw",
                "classification",
            ),
        )
        weather_writer = csv.DictWriter(
            weather_handle,
            fieldnames=(
                "timestamp",
                "temperature_c",
                "relative_humidity_pct",
                "classification",
            ),
        )
        solar_writer.writeheader()
        weather_writer.writeheader()
        for hour_key in common_hours:
            hour = _timestamp(hour_key)
            irradiance = _valid(float(solar_values[hour_key]), solar_fill)
            temperature = _valid(float(temperature_values[hour_key]), weather_fill)
            humidity = _valid(float(humidity_values[hour_key]), weather_fill)
            if irradiance is None:
                missing_solar += 1
            if temperature is None or humidity is None:
                missing_weather += 1
            for minute in (0, 15, 30, 45):
                timestamp = (hour + timedelta(minutes=minute)).isoformat()
                generation_kw = None
                if irradiance is not None:
                    # Hourly Wh/m2 is numerically the hour-average W/m2. Scale a
                    # 1 MW reference plant against 1000 W/m2 and clamp at nameplate.
                    capacity_factor = min(1.0, max(0.0, irradiance / 1000.0))
                    generation_kw = round(
                        REFERENCE_PV_CAPACITY_KW * capacity_factor, 4
                    )
                solar_writer.writerow(
                    {
                        "timestamp": timestamp,
                        "solar_irradiance_wh_m2": "" if irradiance is None else irradiance,
                        "reference_pv_capacity_kw": REFERENCE_PV_CAPACITY_KW,
                        "solar_generation_kw": "" if generation_kw is None else generation_kw,
                        "classification": "COMPUTED from REAL/PUBLIC hourly data",
                    }
                )
                weather_writer.writerow(
                    {
                        "timestamp": timestamp,
                        "temperature_c": "" if temperature is None else temperature,
                        "relative_humidity_pct": "" if humidity is None else humidity,
                        "classification": "COMPUTED from REAL/PUBLIC hourly data",
                    }
                )
                solar_rows += 1
                weather_rows += 1

    files = {}
    for path, classification in (
        (raw_solar_path, "REAL/PUBLIC raw provider response"),
        (raw_weather_path, "REAL/PUBLIC raw provider response"),
        (solar_path, "COMPUTED from REAL/PUBLIC"),
        (weather_path, "COMPUTED from REAL/PUBLIC"),
    ):
        files[str(path.relative_to(output_root))] = {
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
            "classification": classification,
        }

    metadata = {
        "source": SOURCE,
        "source_documentation": "https://power.larc.nasa.gov/docs/services/api/temporal/hourly/",
        "requests": {"solar": solar_url, "weather": weather_url},
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
        "solar_conversion": {
            "reference_pv_capacity_kw": REFERENCE_PV_CAPACITY_KW,
            "formula": "capacity_factor = clamp(irradiance_wh_m2 / 1000, 0, 1); solar_generation_kw = reference capacity * capacity_factor",
            "limitations": "Simplified MVP estimate; no panel orientation, temperature, inverter, shading, or system-loss model.",
        },
        "hourly_observations": len(common_hours),
        "solar_15min_rows": solar_rows,
        "weather_15min_rows": weather_rows,
        "missing_solar_hours": missing_solar,
        "missing_weather_hours": missing_weather,
        "files": files,
    }
    metadata_path = output_root / "processed" / "solar_weather_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[1]
    print(json.dumps(prepare(repository_root / "data"), indent=2))
