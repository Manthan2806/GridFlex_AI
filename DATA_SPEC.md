# DATA SPEC

## Purpose

Define dataset definitions, data sources, raw/processed/synthetic data, data schemas, resolution, geographic scope, units, provenance, data transformations, synthetic data generation rules, data quality requirements, leakage prevention, and train/validation/test/inference separation where applicable.

## Scope

This document is the authoritative source for all data-related specifications in GridFlex AI. It governs data sources, schemas, transformations, synthetic data generation, and data quality requirements. No other document may redefine these specifications.

## Authority

This document is the authoritative source for dataset definitions, data sources, raw/processed/synthetic data, data schemas, resolution, geographic scope, units, provenance, data transformations, synthetic data generation rules, data quality requirements, leakage prevention, and dataset separation. Other documents reference this document; they do not redefine its specifications.

## Current Status

DRAFT

---

## 1. Data Philosophy

1. **REAL/PUBLIC DATA** is used for system-level inputs (solar, weather, demand, tariff) where available.
2. **SYNTHETIC DATA** is used for device-level flexibility and behavior data (EV, water heater, industrial) because there is no real IoT integration in the MVP.
3. **COMPUTED DATA** is derived from real or synthetic data through documented transformations.
4. All data must be explicitly classified as REAL/PUBLIC, SYNTHETIC, or COMPUTED.
5. National data must not be silently described as Gujarat data. Geographic scope must be explicit.
6. Forecast information must not be available to the dispatch decision as actual future outcomes (no leakage).

---

## 2. Data Categories

### 2.1 REAL/PUBLIC Data

Public/system-level energy data used for simulation inputs.

**Storage:** `data/raw/` (immutable), `data/processed/` (derived)

| Dataset | Subdirectory | Purpose | Expected Resolution | Geographic Scope | Units | Source Status | Provenance Requirement | Consumed By |
|---|---|---|---|---|---|---|---|---|
| Solar generation | `data/raw/solar/`, `data/processed/solar_15min/` | Renewable availability for opportunity detection and optimization | 15-minute (processed) | National (India) or region-specific — must be documented | kW, kWh | To be acquired | Source, acquisition method, version, timestamp, geographic scope, transformations | Simulation, Optimization, Opportunity Detection |
| Weather | `data/raw/weather/` | Weather conditions affecting solar and load | 15-minute or hourly (processed to 15-min) | National or region-specific — must be documented | Temperature (°C), irradiance (W/m²), humidity (%) | To be acquired | Same as above | Solar processing, Simulation |
| Demand | `data/raw/demand/`, `data/processed/demand_15min/` | System demand for context and peak analysis | 15-minute (processed) | National or region-specific — must be documented | kW, kWh | To be acquired | Same as above | Simulation, Opportunity Detection |
| Tariff | `data/raw/tariff/` | Electricity tariff structures (not MVP objective but contextual) | Per tariff schedule | National or region-specific — must be documented | Currency/kWh | To be acquired | Same as above | Contextual display (not MVP objective) |

**Important:** National data must NOT be silently described as Gujarat data. Geographic scope must be recorded explicitly in provenance for every dataset.

---

### 2.2 SYNTHETIC Data

Generated device-level flexibility and behavior data for the simulation. Synthetic data must record generator version, seed, and parameters for reproducibility.

**Storage:** `data/synthetic/`

| Dataset | Subdirectory | Purpose | Expected Resolution | Geographic Scope | Units | Source Status | Provenance Requirement | Consumed By |
|---|---|---|---|---|---|---|---|---|
| EV flexibility | `data/synthetic/ev/` | EV charging resource constraints, SOC profiles, departure deadlines | 15-minute or per-event | Simulation scope — must be documented | kW, kWh, °C, SOC (%) | Generated | Generator version, seed, parameters, timestamp, geographic scope | Domain model, Simulation, AI/ML |
| Water heater flexibility | `data/synthetic/water_heater/` | Water heater resource constraints, temperature profiles, recovery times | 15-minute or per-event | Simulation scope — must be documented | kW, kWh, °C | Generated | Same as above | Domain model, Simulation, AI/ML |
| Industrial batch/process | `data/synthetic/industrial/` | Industrial resource constraints, process windows, minimum run times | 15-minute or per-event | Simulation scope — must be documented | kW, kWh | Generated | Same as above | Domain model, Simulation, AI/ML |
| Device behavior | `data/synthetic/behavior/` | Historical response data, override rates, availability rates | Per dispatch event | Simulation scope — must be documented | Various | Generated | Same as above | AI/ML estimation, Trust computation, Learning |
| Scenarios | `data/synthetic/scenarios/` | Scenario definitions, disruption specifications, random seeds | Per scenario | Simulation scope — must be documented | Various | Generated | Same as above | Simulation, Experiment |

**Synthetic data generation rules (per DATA_SPEC.md):**

- Record generator version, seed, and parameters for every generated dataset.
- Produce realistic device behavior consistent with the domain model in DOMAIN_MODEL.md.
- Support scenario variation through parameterized generation.
- Avoid leakage between train/validation/test splits and between scenario runs.

---

### 2.3 COMPUTED Data

Derived from raw or synthetic data through documented transformations.

| Dataset | Subdirectory | Source | Transformation | Produced By |
|---|---|---|---|---|
| Solar at 15-min | `data/processed/solar_15min/` | `data/raw/solar/` | Temporal resampling/aggregation | Data pipeline |
| Demand at 15-min | `data/processed/demand_15min/` | `data/raw/demand/` | Temporal resampling/aggregation | Data pipeline |
| Opportunities | `data/processed/opportunities/` | Solar forecasts, demand data | Opportunity detection logic | Simulation / Backend |
| Trust states | (persisted) | Domain model + behavior + forecasts | Estimation and trust computation | AI/ML |
| Dispatch plans | (persisted) | Trust states + opportunities + constraints | Optimization | Optimization |
| Simulation outputs | (persisted) | Scenarios + dispatch plans | Simulation engine | Simulation |
| Verification results | (persisted) | Dispatch plans + simulation outputs | Verification | Verification |
| Experiment results | `experiments/results/` | Baseline + trust-aware simulation runs | Aggregation and comparison | Experiment framework |

**Computed data rules:**

- All transformations must be documented, reproducible, and versioned alongside the data they produce.
- Computed data must reference its source datasets and transformation logic.

---

## 3. Time Resolution

**The simulation operates on a 15-minute system time resolution** unless later changed through an explicit documented decision.

### 3.1 Why 15-Minute Resolution Is Currently Appropriate

- 15-minute intervals are the standard settlement and metering interval in many electricity markets.
- Sufficient granularity for EV charging, water heater, and industrial batch processes at the MVP scale.
- Balances simulation fidelity with computational tractability for a small team.
- Finer resolution (e.g., 1-minute) is unnecessary for the MVP's resource types and use cases.
- Coarser resolution (e.g., hourly) would miss short-duration events and dispatch opportunities.

---

## 4. Geographic Scope

- Geographic scope must be explicitly recorded in provenance for every dataset.
- National data must not be silently described as Gujarat data.
- Gujarat-specific data requires documented evidence that the dataset covers Gujarat specifically.
- Simulation scope is not inherently Gujarat-specific unless datasets say otherwise.
- The India-specific context from RESEARCH.md is contextual; it does not mandate Gujarat-specific data.

---

## 5. Units

| Quantity | Unit | Notes |
|---|---|---|
| Power | kW | Instantaneous power |
| Energy | kWh | Energy over time |
| Temperature | °C | For water heater, industrial process |
| State of Charge | % | For EV batteries |
| Duration | minutes | Minimum/maximum operating duration |
| Time | ISO 8601 timestamp | UTC or specified timezone — must be documented |
| Confidence | 0.0 - 1.0 | Fraction |
| Force | N/A | Not modeled (no power flow) |
| Voltage | N/A | Not modeled (no power flow) |

All datasets must use consistent units. Mixed units within a dataset require documentation of conversion.

---

## 6. Transformation Pipeline

```
REAL/PUBLIC Data:
  data/raw/{solar,weather,demand,tariff}/
    ↓ (documented, reproducible transformation)
  data/processed/{solar_15min,demand_15min,opportunities}/

Synthetic Data:
  Generator (versioned, seeded, parameterized)
    ↓
  data/synthetic/{ev,water_heater,industrial,behavior,scenarios}/

Combined Input (for simulation):
  data/processed/{solar_15min,demand_15min}/
  + data/synthetic/{ev,water_heater,industrial,behavior,scenarios}/
    ↓
  Simulation Engine Input

Persistence:
  Simulation, Optimization, AI/ML outputs
    ↓
  PostgreSQL (per ARCHITECTURE.md persistence boundary)
    ↓
  Experiment Results (experiments/results/)
```

---

## 7. Leakage Prevention

Leakage must be prevented at multiple levels:

### 7.1 Data Leakage (between splits)

- Synthetic device behavior must not leak between scenarios.
- Train/validation/test splits must be separated at the resource or scenario level where appropriate, not at the time-step level, to prevent temporal leakage (per DATA_SPEC.md).
- Each scenario run uses independent random seeds.

### 7.2 Information Leakage (in the decision loop)

This is the most critical type of leakage for GridFlex AI:

**The optimizer may see forecasts.**
**The optimizer must NOT receive actual future outcomes.**
**The simulator reveals actual outcomes.**
**Verification evaluates them.**
**Learning updates future estimates.**

This boundary is explicit and must be enforced:

| Stage | Sees Forecasts? | Sees Actual Future Outcomes? |
|---|---|---|
| Optimization | YES | NO |
| Simulation | YES (as input) | NO (reveals them via modeling) |
| Verification | NO (compares plan vs actual) | NO (produces the comparison) |
| Learning | NO (uses verification results) | NO (updates model parameters) |

Violation of this boundary constitutes a critical architecture breach and must be documented in ENGINEERING_LOG.md and DECISION_LOG.md.

### 7.3 Train/Validation/Test/Inference Separation

Where applicable, datasets must be separated:

- **Training data** — for learning/trust estimation
- **Validation data** — for tuning and evaluation
- **Test data** — for final evaluation
- **Inference data** — for runtime dispatch decisions

Separation must be documented and reproducible per DATA_SPEC.md.

---

## 8. Provenance Requirements

Every dataset must record:

| Field | Description | Required For |
|---|---|---|
| Source | Original source (public dataset name, or "synthetic") | All |
| Generator | Generator name/version (if synthetic) or acquisition method | Synthetic; Real |
| Version | Dataset version | All |
| Seed | Random seed (if synthetic) | Synthetic |
| Parameters | Generation parameters (if synthetic) | Synthetic |
| Timestamp | When generated or acquired | All |
| Geographic scope | National, regional, Gujarat-specific, or simulation scope | All |
| Units | Units used | All |
| Transformations | Transformations applied (for computed data) | Computed |
| Classification | REAL/PUBLIC, SYNTHETIC, or COMPUTED | All |

---

## 9. Data Quality Requirements

| Rule | Description |
|---|---|
| Consistent units | All datasets use consistent units within their domain (kW, kWh, °C, etc.) |
| Consistent time resolution | Simulation inputs at 15-minute resolution unless documented otherwise |
| No missing critical fields | Critical fields (resource ID, type, power, time) must not be missing without documented imputation |
| Geographic scope recorded | Every dataset has explicit geographic scope |
| Classification labeled | Every dataset labeled REAL/PUBLIC, SYNTHETIC, or COMPUTED |
| Synthetic reproducibility | Generator version, seed, and parameters recorded for synthetic data |
| No silent Gujarat-ification | National data is never treated as Gujarat-specific without evidence |

---

## 10. Reproducibility

Reproducibility requirements per EXPERIMENT_SPEC.md and DATA_SPEC.md:

- All experiments use fixed seeds for synthetic data generation and scenario parameters.
- Scenario configurations are versioned and stored.
- Scheduler versions and algorithm parameters are recorded with each run.
- Results are stored with full provenance.
- Transformation logic is documented and versioned.
- Random number generator states are recordable for each simulation step.

---

## 11. Dataset Limitations

| Dataset | Limitation |
|---|---|
| Solar | Forecast accuracy limited; real data availability may be limited for simulation horizon |
| Weather | Correlation with solar data must be documented; spatial resolution may be coarse |
| Demand | System demand does not equal individual resource demand; aggregate only |
| Tariff | Not used for MVP optimization (renewable absorption is primary objective) |
| EV synthetic | May not capture all real-world EV charging behaviors and driver patterns |
| Water heater synthetic | May not capture all thermal dynamics and occupant behaviors |
| Industrial synthetic | May not capture all process dependencies and production schedules |
| Behavior synthetic | May not capture all failure modes, override patterns, and non-compliance scenarios |

---

## 12. Current Status

DRAFT
