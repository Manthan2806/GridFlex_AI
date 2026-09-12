# Water-Heater Dataset Audit

Status: source selected; synthetic prototype dataset prepared; raw BPA data not
yet downloaded or transformed.

## Decision

Use the Bonneville Power Administration (BPA) CTA-2045 Water Heater
Demonstration as the primary behavioral-response source.

- Official page: https://www.bpa.gov/energy-and-services/conservation/emerging-technologies/portfolio/cta-2045-water-heaters
- Official final report: https://www.bpa.gov/-/media/Aep/energy-efficiency/demand-response/20181118-cta-2045-final-report.pdf
- Period exposed by the downloadable files: January-August 2018.
- Resolution: one minute; GridFlex will aggregate it to canonical 15-minute
  intervals.
- Population analyzed by the report: 145 heat-pump water heaters and 86
  electric-resistance water heaters (231 field units total).
- Measured fields described by BPA: operating state, curtailment type,
  curtailment message, instantaneous watts, and cumulative watt-hours.
- Important behavioral label: the curtailment type explicitly includes
  customer override.

This source directly observes real residential devices responding to grid
commands. It is therefore a stronger anchor for expected and trusted
flexibility than a simulated building-stock profile.

## Secondary thermal source

Use the NIST Net-Zero Energy Residential Test Facility Year 2 dataset only for
thermal and hot-water-use context that the BPA telemetry does not contain.

- Official page: https://pages.nist.gov/netzero/data.html
- Official DOI: https://doi.org/10.18434/T46W2X
- Period: 2015-02-01 through 2016-01-31.
- Resolution: one minute.
- Relevant measurements: water-heater and fixture temperatures, water flow,
  circuit electrical power, and appliance/activity status.

NIST describes this as real instrumented test-house measurement, but the house
used a scheduled virtual family rather than real occupants. It represents one
house and must not be used to claim population-level performance.

## Why a 2025 or 2026 source was not selected

The audit found newer catalogs and modeled datasets, but not a more suitable,
immediately reproducible public source containing device-level water-heater
commands, power, and observed response at 15-minute-or-finer resolution.
Publication date alone is less important here than having labeled dispatch and
override outcomes. Any newer source can be added later as an external holdout.

## Planned data classifications

Every output field must be labelled as one of:

- `REAL`: copied or aggregated from the public measurement.
- `COMPUTED`: deterministically derived from real measurements.
- `SYNTHETIC`: generated because the public source does not provide it.

No synthetic value may be described as measured field data.

## Planned 15-minute response table

The primary processed table will contain one row per anonymized heater and
15-minute interval. Exact source column names will be confirmed from the BPA
readme before implementation.

| GridFlex field | Classification | Intended derivation |
|---|---|---|
| `timestamp` | REAL/COMPUTED | Source timestamp rounded to a 15-minute slot |
| `source_resource_id` | REAL | Anonymized device identifier |
| `heater_type` | REAL | Heat pump or electric resistance, if exposed |
| `requested_state` | REAL | CTA-2045 curtailment command |
| `operating_state` | REAL | Reported heater state |
| `customer_override` | REAL/COMPUTED | Override command/outcome indicator |
| `mean_power_kw` | COMPUTED | Mean instantaneous watts divided by 1000 |
| `energy_kwh` | COMPUTED | Interval energy from cumulative Wh or power integration |
| `available_fraction` | COMPUTED | Fraction of valid source minutes in an available state |
| `response_ratio` | COMPUTED | Delivered response divided by an eligible power bound |
| `source_valid_minutes` | COMPUTED | Valid one-minute observations in the slot |
| `quality_flags` | COMPUTED | Missingness, gaps, impossible values, or incomplete slot |

## Leakage boundary

Pre-dispatch features may include only data known before a command:

- heater type and eligible/rated power;
- time-of-day and day-of-week;
- current operating state when available;
- the current CTA-2045 request;
- historical performance calculated strictly from earlier timestamps.

The following are post-dispatch labels and must never be features for the same
row:

- actual interval power or energy;
- customer response observed after the command;
- completion or verification result;
- response ratio for the current interval;
- future temperature, flow, power, or override values.

Splits will be chronological and resource-aware. Model selection will not read
the final holdout.

## Scope and limitations

- BPA data are from the US Pacific Northwest, not Ahmedabad or India.
- The study period is 2017-2018-era field operation, not 2025/2026.
- The public files are larger than 1 GB each; raw seasonal files should not be
  committed to Git. A reproducible streaming extractor will retain only needed
  columns and produce compact 15-minute CSV files with hashes and metadata.
- BPA telemetry is strong for behavioral response but does not provide the full
  tank-temperature state needed for a general thermal model.
- NIST can support thermal feature engineering, but its single virtual-occupant
  test house cannot fill the population-level gap.
- Ahmedabad resource identities, installation attributes, comfort bands, and
  any fleet expansion would be synthetic and must be kept separate from real
  response measurements.

## Next implementation stage

The current 700-resource prototype dataset is fully synthetic and is generated
by `generate_water_heater_data.py`. It is intentionally separate from the
planned real-data pipeline.

1. Obtain the BPA readme and one seasonal archive.
2. Verify source hashes where published.
3. Inspect exact schema and device count before writing transformations.
4. Implement a streaming one-minute to 15-minute extractor.
5. Replace or augment the synthetic outcomes with an audited real-data sample.
