from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import pandas as pd
except Exception:  # Keep this optional feature from blocking API startup.
    pd = None


SOLAR_CSV_PATH = (
    Path(__file__).resolve().parents[3]
    / "data/processed/solar_15min/nasa_power_ahmedabad_solar_15min_2024.csv"
)
TIMESTAMP_COLUMN = "timestamp"
SOLAR_GENERATION_COLUMN = "solar_generation_kw"


def _load_solar_data():
    """Read and prepare the dataset once when this module is imported."""
    try:
        if pd is None:
            return None
        data = pd.read_csv(SOLAR_CSV_PATH)
        if TIMESTAMP_COLUMN not in data.columns or SOLAR_GENERATION_COLUMN not in data.columns:
            return None
        data = data[[TIMESTAMP_COLUMN, SOLAR_GENERATION_COLUMN]].copy()
        data["_timestamp"] = pd.to_datetime(
            data[TIMESTAMP_COLUMN], utc=True, errors="coerce"
        )
        data["_solar_generation_kw"] = pd.to_numeric(
            data[SOLAR_GENERATION_COLUMN], errors="coerce"
        )
        data = data.dropna(subset=["_timestamp", "_solar_generation_kw"])
        data["_minute_of_day"] = (
            data["_timestamp"].dt.hour * 60 + data["_timestamp"].dt.minute
        )
        return data
    except Exception:
        return None


_SOLAR_DATA = _load_solar_data()


def get_todays_peak_solar_value() -> Optional[float]:
    """Return the single maximum generation value in the full historical dataset."""
    try:
        if _SOLAR_DATA is None or _SOLAR_DATA.empty:
            return None
        return float(_SOLAR_DATA["_solar_generation_kw"].max())
    except Exception:
        return None


def compute_peak_alignment_score(current_time: datetime) -> Optional[float]:
    """Compare the typical generation at this UTC time of day with the all-time peak."""
    try:
        peak_value = get_todays_peak_solar_value()
        if peak_value is None or peak_value <= 0 or _SOLAR_DATA is None:
            return None
        current_minute = current_time.hour * 60 + current_time.minute
        matches = _SOLAR_DATA[_SOLAR_DATA["_minute_of_day"] == current_minute]
        if matches.empty:
            distances = (_SOLAR_DATA["_minute_of_day"] - current_minute).abs()
            distances = distances.where(distances <= 720, 1440 - distances)
            matches = _SOLAR_DATA[distances == distances.min()]
        if matches.empty:
            return None
        typical_value = float(matches["_solar_generation_kw"].mean())
        return round(max(0.0, min(1.0, typical_value / peak_value)), 2)
    except Exception:
        return None
