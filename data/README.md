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

No datasets have been downloaded. Datasets will be acquired or generated during the data acquisition phase.