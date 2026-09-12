# GridFlex AI — AI/ML Status and Roadmap

Last updated: 2026-09-13  
Primary owner: AI/ML and Intelligence team  
Current working branch: `water-heater-data`

## 1. Purpose of this document

This document records what the AI/ML team has actually completed, what the
current evidence supports, what remains incomplete, and the safest order for
future work. It is a handover and working plan. It does not replace the
authoritative project documents at the repository root.

The project remains a simulation-first MVP. Nothing in this repository is
approved for controlling real electrical equipment or making real grid power
commitments.

## 2. GridFlex AI in simple terms

GridFlex AI coordinates electricity-consuming devices so their demand can be
moved to more useful times, such as periods with abundant renewable energy.

For every device, the AI/ML part answers four questions:

1. How much power could the device theoretically adjust?
2. How much adjustment will it probably deliver?
3. How much adjustment is conservative enough to trust?
4. How strong is the evidence behind that conservative estimate?

The full project loop is:

```text
Observe → Represent → Estimate → Trust → Match → Dispatch → Simulate → Verify → Learn
```

AI/ML primarily owns **Estimate**, **Trust**, and **Learn**. The backend,
optimizer, and simulation teams consume the AI/ML results.

## 3. Canonical AI/ML outputs

These names must remain unchanged because other parts of the project depend on
them.

| Output | Simple meaning | Required relationship |
| --- | --- | --- |
| `potential_kw` | Maximum eligible power adjustment under the present technical constraints | Must be finite and non-negative |
| `expected_kw` | Power adjustment the model reasonably expects the device to deliver | `0 <= expected_kw <= potential_kw` |
| `trusted_kw` | More conservative power amount used for trust-aware dispatch | `0 <= trusted_kw <= expected_kw` |
| `confidence` | Strength/conservatism of the current estimate, represented from 0 to 1 | `0 <= confidence <= 1` |

In the current EV backend adapter, `confidence` is calculated as
`trusted_kw / expected_kw` when `expected_kw` is positive. A zero expected
value produces zero confidence.

## 4. Current status at a glance

| Area | Current state | Evidence level | Next action |
| --- | --- | --- | --- |
| EV data | Complete for the offline prototype | Hybrid: real ACN session structure plus synthetic behavior | Keep frozen unless a new experiment is declared |
| EV model candidate v1 | Rejected | Independent holdout failed two group safety checks | Retain as honest experiment history; do not deploy |
| EV model candidate v2 | Accepted for offline demo/MVP prototype | New source-disjoint ACN-anchored synthetic holdout | Keep artifact and acceptance report frozen |
| EV backend integration | Working | Unit, integration, and end-to-end tests | Generalize later for other resource types |
| EV disruption experiment | Working | Seeded synthetic stress test | Add replanning and more seeds later |
| Water-heater data | Generated and audited | Fully synthetic; BPA report facts used only for calibration | Prepare leakage-safe training table |
| Water-heater model | Training table prepared; prediction model not started | No model metrics exist | Validate the table, then build baselines |
| Industrial data/model | Not started | No dataset or metrics exist | Begin after the water-heater pipeline is stable |
| Demand data | Prepared | Real/public all-India 2025 SCADA snapshots | Connect to opportunity/scenario logic |
| Weather data | Prepared | Real/public Ahmedabad Airport 2025 observations | Define safe alignment with 15-minute simulation |
| Solar data | Legacy checkpoint only | Real/public 2024 hourly data repeated into computed 15-minute rows | Replace or supplement before strong forecasting claims |
| Learning loop | Partially represented through historical features | No complete verified online update loop | Implement only after resource models and contracts stabilize |

## 5. Work completed so far

### 5.1 Data source review and provenance rules

The team established the following rules:

- Real measurements, deterministic calculations, hybrid data, and synthetic
  values must be labelled accurately.
- Missing observations must not silently become invented measurements.
- Geographic scope must be stated. National Indian data cannot be described as
  Ahmedabad data, and US device behavior cannot be described as Indian behavior.
- Generated datasets must record their random seed, generator version,
  parameters, row counts, and hashes.
- Model splits must occur at resource level where repeated events exist. This
  prevents the same device from appearing in training and testing.
- Post-dispatch outcomes must not be used to predict that same event.

### 5.2 EV dataset

The EV dataset generator is located at:

```text
ai_ml/EV_model/generate_hybrid_ev_data.py
```

The main prototype dataset contains:

- 700 virtual EV resources;
- 30 historical response events per EV;
- 21,000 historical rows;
- real/public ACN charging-session structure;
- synthetic battery, state-of-charge, availability, override, and repeated
  response fields;
- resource-level 70/15/15 train, validation, and test splits;
- timezone-aware timestamps aligned to the 15-minute GridFlex time grid.

The source is ACN workplace charging data from the United States. It is useful
for anchoring charging durations, timing, energy, and observed power, but it is
not Ahmedabad residential EV evidence.

The EV data-preparation module creates leakage-safe examples. Historical
statistics for an event use only earlier events for the same EV. Current-event
delivery, availability, and override outcomes remain targets rather than
features.

### 5.3 EV baseline and candidate v1

The first classical model used a tuned `RandomForestRegressor`. It predicted the
fraction of requested EV power likely to be delivered.

Candidate v1 was evaluated honestly and rejected. Its overall trusted
overprediction rate was below 15%, but its small and medium dispatch groups were
above the predeclared 15% limit:

| Candidate v1 safety result | Value |
| --- | ---: |
| Overall trusted overprediction | 14.41% |
| Small dispatch | 15.79% — fail |
| Medium dispatch | 15.96% — fail |
| Large dispatch | 11.98% — pass |
| Trusted power retained | 58.44% |

No deployable artifact was released from candidate v1. Its reports remain in
the repository as experiment history and must not be confused with v2.

### 5.4 EV candidate v2

Candidate v2 was developed without using candidate v1's consumed final test
outcomes. It uses:

- a Histogram Gradient Boosting model for the expected delivery ratio;
- a conditional quantile model for a lower estimate;
- group-specific conformal adjustments for small, medium, and large dispatches;
- a frozen feature order and preprocessing configuration;
- a saved offline artifact loaded without request-time retraining.

Its evidence boundary is:

| Evidence partition | Size |
| --- | ---: |
| Development fit data | 14,700 rows |
| Disjoint model-selection data | 1,740 rows |
| Disjoint safety-calibration data | 1,410 rows |
| Final holdout | 210 new resources / 6,300 rows |
| ACN source overlap with original 700-resource data | 0 |
| Candidate v1 test outcomes reused | 0 |

Final v2 results:

| Metric | Result |
| --- | ---: |
| Baseline delivery-ratio MAE | 0.160162 |
| Candidate v2 delivery-ratio MAE | 0.153383 |
| Baseline power MAE | 0.707230 kW |
| Candidate v2 power MAE | 0.683852 kW |
| Overall trusted overprediction | 13.17% |
| Small-dispatch overprediction | 13.02% — pass |
| Medium-dispatch overprediction | 14.83% — pass |
| Large-dispatch overprediction | 11.67% — pass |
| Trusted power retained | 50.09% |

Every predeclared offline gate passed. Candidate v2 is therefore accepted for
the offline hackathon demo and MVP prototype. It is **not approved for real
deployment** because the response behavior, availability, overrides, battery,
and state-of-charge fields remain synthetic.

The key evidence files are:

```text
ai_ml/EV_model/MODEL_CARD_V2.md
ai_ml/EV_model/artifacts/ev_candidate_v2_demo_bundle.joblib
data/processed/ev_training/v2/ev_candidate_v2_config.json
data/processed/ev_training/v2/ev_candidate_v2_final_evaluation.json
```

### 5.5 EV-to-backend integration

The backend integration currently performs this flow:

```text
EV resource
    ↓
OfflineDemoEVModelClientV2
    ↓
potential_kw, expected_kw, trusted_kw, confidence
    ↓
TrustState for each resource
    ↓
MVP optimizer
    ↓
15-minute dispatch plan
    ↓
simulation
    ↓
verification
```

The v2 client:

- requires explicit demo mode;
- verifies the saved model artifact hash;
- loads the locked model rather than retraining during an API request;
- limits requested power using the resource's rated and maximum power;
- creates the canonical `TrustState` output;
- records fallback fields used when the backend resource does not provide EV
  battery and state-of-charge details.

The integrated FastAPI demo is exposed through `POST /simulate/full`. The
integration works for EV resources; it is not yet a generic water-heater or
industrial model router.

### 5.6 EV deterministic and disruption experiments

The deterministic control experiment checks that all components connect and
that dispatch obeys the current constraints. Because the basic simulation
delivers every instruction perfectly, both baseline and trust-aware strategies
show perfect reliability in that control. This is integration evidence, not a
realism claim.

A separate seeded disruption adapter applies the same synthetic availability
and override outcomes to both strategies. For seed 42:

| Seeded stress-test metric | Baseline | Trust-aware |
| --- | ---: | ---: |
| Overcommitment energy | 17.65 kWh | 9.93 kWh |
| Reliability | 0.412 | 0.669 |
| Deadline violations | 4 | 4 |

Trust-aware dispatch reduced overcommitment energy by 43.76% and improved
reliability by 25.75 percentage points for this seed. Neither strategy met every
deadline because dynamic replanning is not implemented. This is one controlled
synthetic example, not statistically sufficient field evidence.

### 5.7 Demand data

The demand checkpoint uses public 2025 GRID-INDIA/NLDC data obtained through
the Grid-Sentinel dataset:

- all-India scope, not Ahmedabad or Gujarat;
- real operational SCADA snapshots at 15-minute timestamps;
- 33,024 retained rows from 344 complete days;
- incomplete days excluded rather than filled;
- known telemetry warnings retained as quality flags;
- small negative solar telemetry values preserved and labelled rather than
  silently corrected.

This dataset is useful for system-level scenario context. It is not yet wired
into a complete renewable-opportunity forecasting model.

### 5.8 Ahmedabad weather data

The weather checkpoint uses real/public 2025 Ahmedabad Airport observations:

- station VAAH;
- 16,465 observations;
- mostly 30-minute resolution with irregular special reports;
- original timestamps retained;
- no invented 15-minute measurements;
- missing dates and incomplete coverage documented.

When used in a 15-minute model, only information already observed at that time
may be carried forward. A carried-forward value must not be described as a new
measurement.

### 5.9 Solar data

The local Ahmedabad solar checkpoint currently remains a legacy source:

- NASA POWER data for 2024;
- original resolution is hourly;
- each hourly average is repeated into four computed 15-minute rows;
- the 15-minute rows are not new 15-minute measurements;
- the PV conversion is simplified.

The 2025 national SCADA dataset also contains measured national solar generation,
but it is not local Ahmedabad rooftop output. These two sources serve different
purposes and must not be presented as interchangeable.

### 5.10 Water-heater source audit

The selected primary real-data source is the BPA CTA-2045 Water Heater
Demonstration. Its report describes one-minute telemetry from 145 heat-pump and
86 electric-resistance field units, including operating state, grid commands,
instantaneous power, cumulative energy, and customer override information.

The raw seasonal archives are larger than 1 GB and have not been downloaded or
transformed in this repository. Therefore, the current water-heater rows are
not presented as BPA measurements.

NIST Net-Zero Energy Residential Test Facility data was identified as a possible
secondary source for temperature, water flow, and thermal context. It represents
one instrumented test house with scheduled virtual occupants, so it cannot
provide population-level customer behavior evidence.

### 5.11 Water-heater synthetic dataset

The current water-heater generator creates:

- 700 synthetic resources;
- 450 heat-pump units and 250 electric-resistance units;
- 30 events per resource;
- 21,000 total historical events;
- 490 training, 105 validation, and 105 test resources;
- positive flexibility magnitudes for both `reduce` and `increase` directions;
- temperatures, tank limits, recovery characteristics, hot-water draws,
  availability, overrides, and response outcomes;
- 15-minute, timezone-aware timestamps;
- reproducible output using seed 2806.

The BPA report contributes only the published heater-type proportion and CTA-2045
command vocabulary. Every device attribute and event outcome is synthetic.

The resource table is:

```text
data/synthetic/water_heater/water_heater_resources.csv
```

The event table is:

```text
data/synthetic/water_heater/behavior/water_heater_historical_response.csv
```

The dataset audit passed with:

- 700 unique resources;
- 21,000 events;
- zero duplicate resource/timestamp events;
- zero physical or schema failures;
- verified canonical CSV hashes;
- mean potential flexibility of 3.590010 kW per event;
- mean delivered flexibility of 1.513546 kW per event;
- mean response ratio of 0.421872.

The audit also declares these current-event fields as labels that must not be
used as features for the same event:

```text
delivered_kw
response_ratio
is_available
has_override
outcome
```

### 5.12 Water-heater training table

The leakage-safe preparation stage now produces 21,000 model examples with:

- 23 explicitly allowed input features;
- 6 target or diagnostic columns;
- 14,700 training rows;
- 3,150 validation rows;
- 3,150 test rows;
- 700 cold-start rows, one for each heater;
- strictly prior history for means, variability, availability, overrides, and
  exponential moving response;
- unchanged resource-level splits.

Current delivery, response ratio, availability, override, outcome, and
hot-water draw are not allowed as same-event model inputs. The hot-water draw
is deliberately retained as `target_hot_water_draw_l`, because the synthetic
generator uses it to influence the current outcome and the real system may not
know the interval's full draw before dispatch.

The prepared table is:

```text
data/processed/water_heater_training/water_heater_training_examples.csv
```

The preparation method, feature allow-list, hashes, split counts, and
limitations are recorded in:

```text
data/processed/water_heater_training/water_heater_training_metadata.json
```

### 5.13 Test evidence

The last repository-wide test run before adding the water-heater files reported
139 passing tests.

After generation, the user ran the five water-heater generator tests and all
five passed. The formal water-heater audit command then reported `PASS` with
zero failures. Three audit tests and five training-preparation tests were also
added. All 13 water-heater test functions passed through direct execution in the
development environment. A normal `pytest` run for the new audit and preparation
tests, followed by a full repository run, is still required before committing
this branch.

The recurring `.pytest_cache` permission warning does not indicate a failed
test. It only means pytest cannot write its optional cache directory.

## 6. Current Git and branch state

At the time of this update:

- `ai-ml`, `origin/ai-ml`, and `submission-integration` point to commit
  `25cbb42` (`Add seeded EV disruption comparison`).
- The active branch is `water-heater-data`.
- `water-heater-data` was created from the integrated AI/ML state.
- The water-heater generator, dataset, audit, tests, and documentation are
  currently working-tree changes and do not yet have their own commit.

Do not describe uncommitted files as published on GitHub until they are committed
and pushed.

## 7. What is not complete

### 7.1 Water-heater model

The water-heater prediction model does not exist yet. The following are still
missing:

- simple baselines;
- model selection;
- safety calibration;
- untouched final holdout evaluation;
- model artifact and model card;
- canonical `TrustState` adapter;
- backend and simulator integration.

### 7.2 Real water-heater validation

The current 700-resource dataset is synthetic. BPA raw device telemetry has not
been transformed, and no Indian residential water-heater behavior source has
been validated. Water-heater results from the current dataset can support a
prototype method, not real-world performance claims.

### 7.3 Industrial resource work

No industrial dataset, generator, training table, model, evaluation, or adapter
has been completed.

### 7.4 Generic resource-model interface

The current backend hydration path is named and implemented for EV prediction.
A shared model-client interface or resource-type router is needed before water
heaters and industrial loads can use the same integration flow cleanly.

### 7.5 Learning after verification

Historical EV features are computed, but the complete closed-loop behavior is
not implemented. Verification results do not yet update persistent reliability
state and trigger a new forecast or dispatch plan.

### 7.6 Dynamic replanning

The seeded EV stress test shows that conservative estimates reduce
overcommitment, but both strategies still miss deadlines. The system currently
does not re-estimate and re-optimize after an override, failure, or unexpected
delivery result.

### 7.7 Renewable opportunity intelligence

Demand, weather, and solar checkpoints exist, but there is no complete model
that converts them into a validated future renewable-excess signal used by the
optimizer. Renewable absorption and rebound metrics remain incomplete or null
in the current MVP experiment.

### 7.8 Production readiness

The following production requirements are outside the present evidence:

- live device telemetry;
- Ahmedabad/India device-level validation;
- real dispatch trials;
- monitoring and drift detection;
- secure model deployment and rollback;
- production database persistence;
- regulatory measurement and verification;
- operational latency and communications-failure testing.

## 8. Recommended next work, in order

Only one stage should be completed and reviewed at a time.

### Stage WH-1 — Run the complete water-heater checks

Run:

```powershell
python -m pytest tests/unit/water_heater_model -q
python -m ai_ml.water_heater_model.audit_water_heater_data
python -m pytest -q
```

Expected outcome:

- eight water-heater tests pass;
- the audit reports `PASS` and zero failures;
- the complete suite passes apart from documented warnings.

Do not proceed if a data or regression test fails.

### Stage WH-2 — Commit the dataset checkpoint

After reviewing the diff, commit the following as one data checkpoint:

```text
ai_ml/water_heater_model/__init__.py
ai_ml/water_heater_model/DATASET_AUDIT.md
ai_ml/water_heater_model/generate_water_heater_data.py
ai_ml/water_heater_model/audit_water_heater_data.py
data/synthetic/water_heater/
data/processed/water_heater/water_heater_dataset_audit.json
data/synthetic/README.md
tests/unit/water_heater_model/
ai_ml/AI_ML_STATUS_AND_ROADMAP.md
```

This preserves a clean point before feature engineering and training.

### Stage WH-3 — Prepare a leakage-safe training table

Status: implemented on the working branch. The table contains 21,000 rows and
uses an explicit 23-column feature allow-list. Normal pytest validation and
review are required before this stage is committed.

Create a separate preparation module. One row should represent one historical
water-heater dispatch event.

Permitted same-event inputs include:

- heater type;
- rated power;
- tank capacity;
- comfort temperature limits;
- recovery rate;
- baseline duty cycle;
- event hour and weekday;
- flexibility direction and requested command;
- pre-dispatch temperature;
- pre-dispatch power;
- pre-dispatch hot-water draw information, only if genuinely known before the
  decision;
- potential flexibility;
- statistics calculated strictly from earlier events.

Targets should include delivery ratio and delivered power. Current-event
availability, override, outcome, response ratio, and delivered power must not
be same-event model features.

The preparation stage must verify chronological order per heater and preserve
the resource-level train/validation/test assignment.

### Stage WH-4 — Evaluate simple baselines

Before classical ML, compare transparent baselines such as:

1. global mean delivery ratio from training data;
2. heater-type mean;
3. direction plus heater-type mean;
4. historical mean using only earlier events;
5. historical exponentially weighted mean.

Evaluate prediction accuracy and unsafe overprediction separately. Useful
metrics include ratio MAE, power MAE, bias, overprediction rate, and retained
power.

### Stage WH-5 — Train a small classical model

Use a reproducible classical model only if it beats the strongest baseline on
validation data. Candidate families may include Random Forest or Histogram
Gradient Boosting. Do not open the test split while selecting features,
hyperparameters, or safety settings.

### Stage WH-6 — Calibrate trusted flexibility

Convert expected power into a conservative trusted amount. Declare the safety
target and minimum usefulness floor before final testing. Check at least:

- overall overprediction;
- heat-pump group;
- resistance-heater group;
- increase and reduce directions;
- small, medium, and large flexibility magnitudes;
- trusted power retained.

No group should be hidden behind a good overall average.

### Stage WH-7 — Evaluate once on the untouched holdout

Freeze the selected model, features, imputation, and safety calibration. Then
evaluate the final test resources once. If a required gate fails, reject the
candidate and create a genuinely new experiment instead of changing the rules
after seeing the test result.

Because the present outcomes are synthetic, even a passing candidate may be
labelled only for offline prototype use.

### Stage WH-8 — Package and document the model

If the offline gate passes:

- save an immutable model bundle;
- record its SHA-256 hash;
- create a model card;
- record library versions and seed;
- store the feature order and imputation values;
- state the exact allowed use and limitations.

### Stage WH-9 — Add a resource-specific adapter

Create the water-heater prediction adapter inside `ai_ml/` first. It should
accept water-heater state and produce the canonical four outputs. Integration
with backend-owned routing should be coordinated with the backend team rather
than silently changing frozen interfaces.

### Stage IND-1 onward — Repeat for industrial loads

After the water-heater pipeline is stable, repeat the same disciplined sequence:

1. source and schema audit;
2. honest synthetic/real classification;
3. reproducible generator or extractor;
4. data-quality audit;
5. leakage-safe training preparation;
6. baselines;
7. classical model selection;
8. conservative trust calibration;
9. untouched holdout;
10. model card, artifact, and adapter.

Industrial constraints must include process windows, minimum run times,
interruptibility, deadlines, restart behavior, and any thermal or inventory
limits actually supported by the data.

### Stage CROSS-1 — Generalize the AI/ML interface

Once at least two resource models exist, define a minimal common predictor
interface that returns `TrustState` without exposing model-specific details.
Keep feature construction inside the relevant resource model. The backend should
select the correct model by canonical resource type.

### Stage CROSS-2 — Implement the learning loop

Accept verified outcomes only after simulation or real verification. Update
historical reliability summaries for future events. Ensure the outcome at time
`t` can affect time `t+1`, but never the estimate that existed at time `t`.

Start with deterministic incremental statistics or an exponential moving
average. Avoid a complex online-learning platform for the MVP.

### Stage CROSS-3 — Add dynamic replanning

When a device becomes unavailable, overrides a command, or under-delivers:

1. record the verified outcome;
2. update reliability evidence;
3. rebuild trust estimates;
4. re-run dispatch for the remaining time window;
5. verify deadlines and feeder limits again.

### Stage CROSS-4 — Connect renewable opportunity data

Define a time-aligned input table for demand, renewable generation, and known
weather observations. Build a simple baseline opportunity detector before a
forecasting model. Measure whether dispatch moves consumption into periods with
more renewable availability.

### Stage CROSS-5 — Run multi-scenario evaluation

Run more than one seed and more than one hand-picked scenario. Include:

- normal operation;
- high override rates;
- low availability;
- high renewable supply;
- tight feeder capacity;
- tight deadlines;
- mixed EV, water-heater, and industrial portfolios.

Report distributions and confidence intervals where meaningful. One favorable
seed must not become the overall performance claim.

## 9. Information needed from other teams

### Backend team

The AI/ML team needs:

- a stable resource-type routing point;
- water-heater and industrial state fields supported by canonical schemas;
- a way to supply event time and historical verified outcomes;
- explicit demo/deployment gating;
- no request-time retraining;
- clear error handling when a model or required state is unavailable.

### Simulation team

The AI/ML team needs:

- resource-specific actual-response behavior;
- water-temperature and comfort-bound evolution for heaters;
- hot-water draw events;
- availability, overrides, failures, and rebound;
- verified delivered power per 15-minute interval;
- deterministic seeds for comparable experiments.

### Experiment team

The AI/ML team needs:

- identical scenarios and disruptions for baseline and trust-aware strategies;
- separate accuracy, safety, and usefulness metrics;
- multiple seeds and resource sizes;
- structured results with provenance;
- no claims stronger than the supplied evidence.

## 10. Important claim boundaries

Acceptable statements:

- “EV candidate v2 passed its predeclared offline prototype gate.”
- “The EV structure is anchored to public ACN charging sessions.”
- “The water-heater dataset is synthetic and reproducible.”
- “For seed 42, trust-aware EV dispatch reduced synthetic overcommitment energy
  by 43.76%.”
- “The current system is a simulation-first MVP.”

Statements that are not supported:

- “The EV model is production ready.”
- “The model is validated for Ahmedabad drivers.”
- “The water-heater data contains 700 real homes.”
- “The 2024 solar file contains measured 15-minute observations.”
- “The system guarantees grid safety.”
- “Trust-aware dispatch always prevents missed deadlines.”

## 11. Definition of done

### Offline hackathon/MVP prototype

The AI/ML part can be considered complete for the broader MVP when:

- all three resource types produce the canonical trust outputs;
- every dataset has provenance and reproducibility metadata;
- leakage-safe baselines and model evaluations exist;
- each released candidate passes predeclared offline gates;
- all resource models connect to the same backend flow;
- deterministic and disrupted multi-resource scenarios run end to end;
- verification outcomes can update future trust;
- the complete test suite passes;
- all limitations are visible in the presentation and repository.

### Real deployment

Real deployment would additionally require real local device data, field trials,
live telemetry validation, monitoring, drift handling, secure operational
controls, regulatory review, rollback procedures, and utility approval. The
current repository does not meet this definition.

## 12. Immediate next action

Run the new preparation tests and the full suite:

```powershell
python -m pytest tests/unit/water_heater_model -q
python -m ai_ml.water_heater_model.audit_water_heater_data
python -m pytest -q
```

If they pass, review and commit the water-heater dataset, audit, and training-table
checkpoint. The next implementation stage after that is **Stage WH-4**, simple
baseline evaluation. Do not train a classical model before comparing it with
those baselines.
