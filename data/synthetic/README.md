# Synthetic Data

The files in this directory are generated data for simulation-first MVP work.
They are not measurements from real people, vehicles, utilities, or locations.

## EV portfolio: ACN + synthetic hybrid

Run from the repository root:

```text
python -m ai_ml.EV_model.generate_hybrid_ev_data --output-root data/synthetic
```

The generator creates:

- `source_samples/acn_session_summaries.csv`: summary of 700 sampled real ACN sessions.
- `ev/ev_resources.csv`: 700 hybrid EVs anchored to those real session patterns.
- `behavior/ev_historical_response.csv`: 30 synthetic historical outcomes per EV,
  calibrated from its linked ACN session.
- `ev_dataset_metadata.json`: source, seed, version, field provenance, hashes,
  split rule, and limitations.

All timestamps include an explicit UTC+05:30 offset. Dataset splits are assigned
by resource, not by individual event, to prevent one EV's behaviour appearing in
multiple splits. Every generated history timestamp precedes the scenario date so
that future outcomes cannot leak into pre-dispatch estimation.

Arrival/departure patterns, delivered energy, and observed charging power come
from ACN. Battery/SOC values and repeated behaviour are synthetic because ACN
does not provide those fields. ACN observations are from US workplace sites and
must not be described as Indian residential EV behaviour.

GridFlex uses 15-minute simulation blocks. Each EV start and end time is aligned
to that grid using only complete blocks contained within the ACN-derived session
duration. Energy requirements are capped to what the charger can physically
deliver inside that aligned window. SOC values use three decimal places so small
but non-zero energy requirements do not disappear through rounding.

## Water-heater prototype dataset

Run from the repository root:

```text
python -m ai_ml.water_heater_model.generate_water_heater_data
```

This creates 700 synthetic water heaters and 30 historical 15-minute demand-
response events for each heater. The resource-level split is 70/15/15, so one
heater never appears in more than one model split.

The dataset is fully synthetic. It uses only the published heater-type mix and
CTA-2045 command vocabulary from the BPA field-study report as calibration
facts. It does not contain BPA device rows and must not be presented as real
household or Ahmedabad data. See
`water_heater/water_heater_dataset_metadata.json` for hashes, provenance, and
limitations.

Audit the generated files before feature preparation:

```text
python -m ai_ml.water_heater_model.audit_water_heater_data
```

The audit checks physical limits, duplicate events, 15-minute timestamps,
resource-level split isolation, metadata hashes, and the boundary between
pre-dispatch inputs and post-dispatch labels.

Prepare the leakage-safe model input table with:

```text
python -m ai_ml.water_heater_model.prepare_water_heater_training_data
```

The prepared table uses only static, time, command, pre-dispatch state, and
strictly earlier historical outcomes as model features. Current delivery,
availability, override, outcome, and hot-water draw values are target or
diagnostic columns and cannot be selected through the feature allow-list.
