# Synthetic Data

The files in this directory are generated data for simulation-first MVP work.
They are not measurements from real people, vehicles, utilities, or locations.

## EV portfolio v2: ACN + synthetic hybrid

Run from the repository root:

```text
python -m ai_ml.generate_hybrid_ev_data --output-root data/synthetic
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
