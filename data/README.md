# Data

This directory contains datasets used by GridFlex AI. The authoritative data specification is `DATA_SPEC.md` at the repository root.

## Data Categories

### Raw Data (`data/raw/`)
Public/system-level energy data. **Raw data must never be modified in place.**

- `data/raw/solar/` — solar generation data
- `data/raw/weather/` — weather data
- `data/raw/demand/` — system demand data
- `data/raw/tariff/` — tariff data

### Processed Data (`data/processed/`)
Derived from raw data through documented transformations. **Processed data must be reproducible from raw data.**

- `data/processed/solar_15min/` — solar data at 15-minute resolution
- `data/processed/demand_15min/` — demand data at 15-minute resolution
- `data/processed/opportunities/` — detected renewable-aligned dispatch opportunities

### Synthetic Data (`data/synthetic/`)
Generated device-level flexibility and behavior data. **Synthetic data must record generator/version/seed/parameters.**

- `data/synthetic/ev/` — EV charging flexibility data
- `data/synthetic/water_heater/` — water heater flexibility data
- `data/synthetic/industrial/` — industrial batch/process flexibility data
- `data/synthetic/behavior/` — device behavior and response data
- `data/synthetic/scenarios/` — scenario definitions and conditions

## Data Rules

- Data provenance is mandatory for every dataset.
- Datasets must not be silently treated as Gujarat-specific unless their geographic scope actually supports that claim.
- Public system-level data and synthetic device-level behavior will be combined where appropriate.
- The simulation operates on a 15-minute system time resolution unless later changed through an explicit documented decision.

## Current Status

<<<<<<< HEAD
- EV data: 700 ACN-anchored synthetic resource profiles and 21,000 behavior rows.
- Solar data: legacy NASA POWER hourly data for an Ahmedabad demonstration point,
  expanded to clearly labelled 15-minute computed rows for 2024.
- Weather data: real Ahmedabad Airport (VAAH) station observations for 2025,
  predominantly recorded every 30 minutes and retained at their original times.
  No weather readings are interpolated or invented.
- Demand data: real all-India operational SCADA snapshots at 15-minute timestamps
  for 344 complete days in 2025. The same source also provides national solar,
  wind, hydro, thermal, and total generation readings.

The processed demand data contains measured snapshots, not calculated 15-minute
profiles. Missing or incomplete days are excluded rather than filled with invented
values. Known source warnings are recorded in the `quality_flags` column. This is
national data and must not be presented as Gujarat- or Ahmedabad-only data. See
`data/processed/demand_metadata.json` for provenance and validation details.

Rebuild the demand checkpoint from the repository root with:

```text
python -m ai_ml.prepare_demand_data
```

Rebuild the real weather checkpoint with:

```text
python -m ai_ml.prepare_weather_data
```

Weather observations do not occur at every 15-minute simulation timestamp. The
model should use the most recent known observation and must not describe the
carried-forward value as a new measurement.
=======
No datasets have been downloaded. Datasets will be acquired or generated during the data acquisition phase.
>>>>>>> 1ef4f81fafd2ee185875a14dca5e40f604f18f08
