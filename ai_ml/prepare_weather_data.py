"""Prepare real 2025 Ahmedabad airport weather observations for GridFlex."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


SOURCE = "Iowa Environmental Mesonet ASOS/METAR archive"
SOURCE_DOCUMENTATION = (
    "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?help="
)
SOURCE_STATION_PAGE = (
    "https://mesonet.agron.iastate.edu/sites/site.php?network=IN__ASOS&station=VAAH"
)
SOURCE_DISCLAIMER = "https://mesonet.agron.iastate.edu/disclaimer.php"
IMD_STATION_FREQUENCY_REFERENCE = "https://camd.imd.gov.in/obs_system.php"
YEAR = 2025
STATION_ID = "VAAH"
STATION_NAME = "Ahmedabad Airport"
TIME_ZONE_NAME = "Asia/Kolkata"
IST = timezone(timedelta(hours=5, minutes=30))
GENERATOR_VERSION = "gridflex-vaah-weather-v1"

SOURCE_COLUMNS = (
    "station",
    "valid",
    "lon",
    "lat",
    "elevation",
    "tmpf",
    "dwpf",
    "relh",
    "drct",
    "sknt",
    "alti",
    "mslp",
    "vsby",
    "gust",
    "wxcodes",
    "metar",
)


def _source_url(year: int) -> str:
    local_start = datetime(year, 1, 1, tzinfo=IST)
    local_end = datetime(year + 1, 1, 1, tzinfo=IST)
    start_utc = local_start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    end_utc = local_end.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    query = urllib.parse.urlencode(
        [
            ("station", STATION_ID),
            ("data", "tmpf"),
            ("data", "dwpf"),
            ("data", "relh"),
            ("data", "drct"),
            ("data", "sknt"),
            ("data", "alti"),
            ("data", "mslp"),
            ("data", "vsby"),
            ("data", "gust"),
            ("data", "wxcodes"),
            ("data", "metar"),
            ("sts", start_utc),
            ("ets", end_utc),
            ("tz", TIME_ZONE_NAME),
            ("format", "onlycomma"),
            ("latlon", "yes"),
            ("elev", "yes"),
            ("missing", "empty"),
            ("report_type", "1"),
            ("report_type", "3"),
            ("report_type", "4"),
        ]
    )
    return f"https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?{query}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, path: Path) -> None:
    temporary_path = path.with_suffix(path.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "GridFlex-AI"})
    try:
        with urllib.request.urlopen(request, timeout=180) as response, temporary_path.open(
            "wb"
        ) as handle:
            while chunk := response.read(1024 * 1024):
                handle.write(chunk)
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _number(value: str) -> float | None:
    return None if not value.strip() else float(value)


def _rounded(value: float | None, factor: float = 1.0) -> str | float:
    return "" if value is None else round(value * factor, 3)


def _metar_qnh_hpa(metar: str) -> tuple[float | None, bool]:
    """Return QNH pressure and whether an explicit source value was invalid."""
    match = re.search(r"\bQ(\d{4})\b", metar)
    if match is None:
        return None, False
    pressure = float(match.group(1))
    if not 850.0 <= pressure <= 1100.0:
        return None, True
    return pressure, False


def _all_dates(year: int) -> list[date]:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    return [start + timedelta(days=index) for index in range((end - start).days + 1)]


def prepare(output_root: Path, year: int = YEAR, refresh: bool = False) -> dict[str, object]:
    raw_dir = output_root / "raw" / "weather"
    processed_dir = output_root / "processed" / "weather_observations"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    source_url = _source_url(year)
    raw_path = raw_dir / f"iem_vaah_ahmedabad_metar_{year}.csv"
    if refresh or not raw_path.exists():
        _download(source_url, raw_path)

    with raw_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != SOURCE_COLUMNS:
            raise ValueError("The downloaded IEM weather schema is not the expected schema")
        source_rows = list(reader)

    observations: dict[datetime, dict[str, str]] = {}
    for row in source_rows:
        if row["station"] != STATION_ID:
            raise ValueError(f"Unexpected station in source: {row['station']}")
        local_timestamp = datetime.strptime(row["valid"], "%Y-%m-%d %H:%M").replace(
            tzinfo=IST
        )
        if local_timestamp.year == year:
            observations[local_timestamp] = row
    if not observations:
        raise ValueError(f"No {year} observations found in {raw_path}")

    output_path = (
        processed_dir / f"ahmedabad_vaah_weather_observations_{year}.csv"
    )
    output_fields = (
        "timestamp",
        "station_id",
        "station_name",
        "latitude",
        "longitude",
        "elevation_m",
        "temperature_c",
        "dew_point_c",
        "relative_humidity_pct",
        "wind_direction_deg",
        "wind_speed_m_s",
        "wind_gust_m_s",
        "qnh_pressure_hpa",
        "visibility_km",
        "weather_codes",
        "quality_flags",
        "raw_metar",
        "classification",
    )
    quality_flag_counts: Counter[str] = Counter()
    day_counts: Counter[str] = Counter()
    timestamps = sorted(observations)
    intervals = Counter(
        int((later - earlier).total_seconds() / 60)
        for earlier, later in zip(timestamps, timestamps[1:])
    )
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_fields)
        writer.writeheader()
        for timestamp in timestamps:
            row = observations[timestamp]
            temperature_f = _number(row["tmpf"])
            dew_point_f = _number(row["dwpf"])
            humidity = _number(row["relh"])
            wind_direction = _number(row["drct"])
            wind_knots = _number(row["sknt"])
            gust_knots = _number(row["gust"])
            pressure_hpa, pressure_source_invalid = _metar_qnh_hpa(row["metar"])
            visibility_miles = _number(row["vsby"])
            quality_flags: list[str] = []
            for label, value in (
                ("temperature_missing", temperature_f),
                ("dew_point_missing", dew_point_f),
                ("humidity_missing", humidity),
                ("wind_direction_missing", wind_direction),
                ("wind_speed_missing", wind_knots),
                ("pressure_missing", pressure_hpa),
                ("visibility_missing", visibility_miles),
            ):
                if value is None:
                    quality_flag_counts[label] += 1
                    quality_flags.append(label)
            if pressure_source_invalid:
                quality_flag_counts["pressure_source_invalid"] += 1
                quality_flags.append("pressure_source_invalid")
            if wind_knots is not None and wind_knots > 58.0:
                quality_flag_counts["wind_speed_source_outlier"] += 1
                quality_flags.append("wind_speed_source_outlier")

            day_counts[timestamp.date().isoformat()] += 1
            writer.writerow(
                {
                    "timestamp": timestamp.isoformat(),
                    "station_id": STATION_ID,
                    "station_name": STATION_NAME,
                    "latitude": row["lat"],
                    "longitude": row["lon"],
                    "elevation_m": row["elevation"],
                    "temperature_c": _rounded(
                        None
                        if temperature_f is None
                        else (temperature_f - 32.0) * 5.0 / 9.0
                    ),
                    "dew_point_c": _rounded(
                        None
                        if dew_point_f is None
                        else (dew_point_f - 32.0) * 5.0 / 9.0
                    ),
                    "relative_humidity_pct": _rounded(humidity),
                    "wind_direction_deg": _rounded(wind_direction),
                    "wind_speed_m_s": _rounded(wind_knots, 0.514444),
                    "wind_gust_m_s": _rounded(gust_knots, 0.514444),
                    "qnh_pressure_hpa": _rounded(pressure_hpa),
                    "visibility_km": _rounded(visibility_miles, 1.609344),
                    "weather_codes": row["wxcodes"],
                    "quality_flags": ";".join(quality_flags) or "none",
                    "raw_metar": row["metar"],
                    "classification": "REAL/PUBLIC station observation; units converted",
                }
            )

    present_dates = set(day_counts)
    missing_dates = [
        day.isoformat() for day in _all_dates(year) if day.isoformat() not in present_dates
    ]
    low_coverage_days = {
        day: count for day, count in sorted(day_counts.items()) if count < 40
    }
    metadata = {
        "source": SOURCE,
        "source_documentation": SOURCE_DOCUMENTATION,
        "source_station_page": SOURCE_STATION_PAGE,
        "source_disclaimer": SOURCE_DISCLAIMER,
        "imd_station_frequency_reference": IMD_STATION_FREQUENCY_REFERENCE,
        "source_download_url": source_url,
        "source_usage": "Public domain; IEM attribution requested",
        "generator_version": GENERATOR_VERSION,
        "station": {
            "id": STATION_ID,
            "name": STATION_NAME,
            "latitude": float(source_rows[0]["lat"]),
            "longitude": float(source_rows[0]["lon"]),
            "elevation_m": float(source_rows[0]["elevation"]),
            "geographic_scope": "Single Ahmedabad airport weather station",
        },
        "year": year,
        "time_standard": "Asia/Kolkata (UTC+05:30)",
        "classification": "REAL/PUBLIC station observations with unit conversions",
        "source_resolution": "Predominantly half-hourly, with irregular special reports",
        "processed_resolution": "Original observation timestamps; not resampled",
        "observation_count": len(timestamps),
        "days_present": len(day_counts),
        "days_with_exactly_48_observations": sum(
            count == 48 for count in day_counts.values()
        ),
        "missing_calendar_dates": missing_dates,
        "low_coverage_days_below_40_observations": low_coverage_days,
        "interval_counts_minutes": {
            str(minutes): count for minutes, count in sorted(intervals.items())
        },
        "quality_flag_counts": dict(sorted(quality_flag_counts.items())),
        "transformation": [
            f"select VAAH observations for local calendar year {year}",
            "retain original observation timestamps; do not interpolate or fill gaps",
            "convert Fahrenheit to Celsius, knots to metres/second, and miles to kilometres",
            "extract QNH pressure from the METAR Q-code and reject impossible source values",
            "preserve the original METAR report and label missing fields",
        ],
        "limitations": [
            "This station represents Ahmedabad airport, not all Gujarat or India.",
            "Measurements are mainly half-hourly, not every 15 minutes.",
            "Missing dates and incomplete days are preserved as gaps.",
            "Suspicious source values are preserved where possible and labelled in quality_flags.",
            "Airport observations do not include solar irradiance.",
            "IEM notes that non-US precipitation data is unavailable in this archive.",
        ],
        "files": {
            str(raw_path.relative_to(output_root)): {
                "bytes": raw_path.stat().st_size,
                "sha256": _sha256(raw_path),
                "classification": "REAL/PUBLIC source archive CSV",
            },
            str(output_path.relative_to(output_root)): {
                "bytes": output_path.stat().st_size,
                "sha256": _sha256(output_path),
                "classification": "REAL/PUBLIC observations; units converted",
            },
        },
    }
    metadata_path = output_root / "processed" / "weather_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=YEAR)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data",
    )
    args = parser.parse_args()
    print(json.dumps(prepare(args.output_root, args.year, args.refresh), indent=2))


if __name__ == "__main__":
    main()
