# DOMAIN MODEL

## Purpose

Define the domain entities, entity relationships, domain terminology, invariants, domain states, and flexibility concepts for GridFlex AI.

## Scope

This document covers the conceptual domain model. It documents currently identified entities and their conceptual fields. These are **conceptual requirements, not necessarily the final database schema** — this distinction must be preserved. Database schema design is a separate artifact derived from this document during implementation.

## Authority

This document is the authoritative source for domain entities, entity relationships, domain terminology, invariants, domain states, flexibility concepts, and the resource lifecycle. Other documents must not redefine domain terminology or entity relationships; they may reference this document.

## Current Status

DRAFT

---

## 1. Domain Glossary

| Term | Definition |
|---|---|
| **Theoretical Flexibility** | The maximum shiftable capacity implied by a resource's physical limits, ignoring reliability, constraints, and behavior. |
| **Expected Flexibility** | The expected deliverable capacity given current evidence, including operational state, constraints, and uncertainty. |
| **Trusted Flexibility** | The confidence-weighted deliverable capacity used for dispatch decisions. Derived from expected flexibility and confidence. |
| **Delivered Flexibility** | The actual flexibility delivered as measured by verification (actual response vs. dispatched instruction). |
| **FlexibilityResource** | A single coordinated flexible load with operational constraints and behavior history. |
| **Trust State** | A time-dependent computed state representing potential, expected, trusted capacity and confidence. |
| **Confidence** | A scalar measure of how much trust to place in the trust estimate at a given time. |
| **Dispatch Plan** | A schedule of flexibility dispatch across resources and time steps (x[i,t]). |
| **Dispatch Instruction** | A specific dispatch command issued to a resource for a specific time. |
| **Actual Response** | The real (simulated) flexibility delivered by a resource in response to a dispatch instruction. |
| **Verification** | Comparison of actual response against dispatched instructions. |
| **Verification Result** | Outcome of verification: delivered vs. dispatched, error, constraint adherence. |
| **Scenario** | A defined set of conditions (resources, forecasts, disruptions) under which a simulation runs. |
| **Simulation Run** | A complete execution of the simulation engine for a scenario. |
| **Opportunity** | A renewable-aligned window where dispatching flexibility would absorb renewable energy or reduce peak pressure. |
| **Renewable Forecast** | Predicted renewable generation availability over time. |
| **Override Rate** | Historical fraction of dispatch instructions not fully complied with by the resource or its operator. |
| **Availability Rate** | Historical fraction of time a resource is available for dispatch when requested. |
| **Rebound** | Demand that returns after being shifted, partially or fully negating the shift. |
| **Feeder Capacity** | Maximum power flow capacity of the distribution feeder serving a resource location. |
| **Comfort Constraint** | Operational limit related to user comfort (e.g., temperature band for water heater). |
| **Process Constraint** | Operational limit related to industrial process requirements (e.g., minimum run time, batch window). |
| **Flexibility State** | The current operational state of a resource regarding dispatchability: available, dispatched, completed, unavailable. |

---

## 2. Entity Inventory

The following entities have been identified:

| Entity | Description | Owned By |
|---|---|---|
| FlexibilityResource | Central domain entity; a flexible load with constraints and behavior | DOMAIN_MODEL.md |
| TrustState | Time-dependent trust computation result | DOMAIN_MODEL.md, ALGORITHM_SPEC.md |
| FlexibilityRepresentation | Normalized representation of resource constraints | DOMAIN_MODEL.md |
| RenewableForecast | Predicted renewable availability over time | ARCHITECTURE.md, DATA_SPEC.md |
| Opportunity | Renewable-aligned dispatch window | ARCHITECTURE.md, ALGORITHM_SPEC.md |
| DispatchPlan | Optimization solution: x[i,t] values | ALGORITHM_SPEC.md, ARCHITECTURE.md |
| DispatchInstruction | Specific dispatch command to a resource | ARCHITECTURE.md |
| ActualResponse | Simulated actual flexibility delivered | ARCHITECTURE.md |
| VerificationResult | Comparison of actual vs. dispatched | ARCHITECTURE.md, EXPERIMENT_SPEC.md |
| Scenario | Defined simulation conditions | ARCHITECTURE.md, EXPERIMENT_SPEC.md |
| SimulationRun | Complete simulation execution | ARCHITECTURE.md |
| ExperimentRun | Evaluation run comparing schedulers | EXPERIMENT_SPEC.md |
| BehaviorRecord | Historical response data | DOMAIN_MODEL.md, DATA_SPEC.md |

---

## 3. FlexibilityResource (Deep Dive)

FlexibilityResource is the central domain entity. The following fields are currently identified conceptual requirements, **not a final schema**.

### 3.1 Identity

| Field | Description | Type Reference |
|---|---|---|
| `id` | Unique identifier | string |
| `type` | Resource type: `ev`, `water_heater`, `industrial_batch` | enum per MVP |
| `location_id` | Geographic location identifier | string |
| `rated_power_kw` | Nameplate maximum power rating | float (kW) |

### 3.2 Availability

| Field | Description | Unit |
|---|---|---|
| `earliest_start` | Earliest time flexibility can begin | timestamp |
| `latest_end` | Latest time flexibility must end | timestamp |

### 3.3 Energy

| Field | Description | Unit |
|---|---|---|
| `required_kwh` | Energy that must be delivered | kWh |
| `minimum_kwh` | Minimum energy delivery requirement | kWh |
| `maximum_kwh` | Maximum energy that can be delivered | kWh |

### 3.4 Duration

| Field | Description | Unit |
|---|---|---|
| `minimum_duration` | Minimum continuous operating duration | minutes |
| `maximum_duration` | Maximum continuous operating duration | minutes |

### 3.5 Constraints

| Field | Description |
|---|---|
| `deadline` | Hard deadline by which energy must be delivered | timestamp |
| `min_power` | Minimum power while active | kW |
| `max_power` | Maximum power while active | kW |
| `comfort/process limits` | Type-specific limits (temperature bands, process windows, minimum run times) |

### 3.6 Behavior

| Field | Description |
|---|---|
| `historical_response` | Time series of past dispatch responses (dispatched vs. actual) |
| `override_rate` | Fraction of dispatch instructions not fully complied with |
| `availability_rate` | Fraction of time available when requested |

### 3.7 Trust (Computed)

| Field | Description |
|---|---|
| `potential_kw` | Theoretical maximum deliverable capacity |
| `expected_kw` | Expected deliverable capacity given current evidence |
| `trusted_kw` | Confidence-weighted deliverable capacity used for dispatch |
| `confidence` | Confidence level in the trust estimate |

**Invariant:** `trusted_kw` ≤ `expected_kw` ≤ `potential_kw`.

### 3.8 State

| State | Description |
|---|---|
| `available` | Resource is available for dispatch |
| `dispatched` | Resource has been given a dispatch instruction |
| `completed` | Resource has fulfilled its dispatch |
| `unavailable` | Resource is not available (offline, full, etc.) |

---

## 4. Important Distinctions

### 4.1 Conceptual Fields vs. Schema

The fields listed in section 3 are conceptual requirements identified during domain modeling. The final database schema is a separate artifact to be derived from this document during the implementation phase. Do not treat this list as frozen.

### 4.2 Trust is Time-Dependent

**Trust is a time-dependent computed state, not a permanent device property.** The trust fields (`potential_kw`, `expected_kw`, `trusted_kw`, `confidence`) are recomputed each cycle from current evidence — including recent verification outcomes, forecast uncertainty, and resource state. They must not be treated as static device attributes.

### 4.3 Flexibility Distinctions

| Category | Definition | Use |
|---|---|---|
| Theoretical Flexibility | Maximum shiftable capacity from physical limits | Baseline comparison; upper bound |
| Expected Flexibility | Expected deliverable given evidence | Input to trust computation |
| Trusted Flexibility | Confidence-weighted expected for dispatch | Dispatch decision input |
| Delivered Flexibility | Actual flexibility delivered per verification | Verification and learning input |

The gap between Theoretical and Trusted flexibility is the core insight of the project. The gap between Trusted and Delivered flexibility is what verification measures and learning addresses.

### 4.4 What Is Domain vs. What Is Computed

| Category | Examples |
|---|---|
| Domain entities (representation) | FlexibilityResource, FlexibilityRepresentation, Opportunity, Scenario |
| Computed states | TrustState, VerificationResult |
| Records | DispatchPlan, DispatchInstruction, ActualResponse, SimulationRun, ExperimentRun |

---

## 5. Entity Relationships

| Relationship | Cardinality | Description |
|---|---|---|
| FlexibilityResource → Location | Many-to-One | A FlexibilityResource belongs to one location |
| FlexibilityResource → FlexibilityState | One-to-One (current) | A FlexibilityResource has one current state at any time |
| FlexibilityResource → TrustState | One-to-Many | A FlexibilityResource produces many trust-state observations over time |
| FlexibilityResource → DispatchEvent | One-to-Many | A FlexibilityResource participates in many dispatch events |
| DispatchEvent → VerificationResult | One-to-One | A dispatch event produces one verification outcome |
| VerificationResult → Learning | One-to-Many | A verification outcome feeds learning, which updates future trust estimates |
| Scenario → SimulationRun | One-to-Many | A scenario can have multiple simulation runs |
| Scenario → DispatchPlan | One-to-Many | A scenario produces dispatch plans per scheduler |
| Resource → BehaviorRecord | One-to-Many | A resource has historical behavior records |

---

## 6. Invariants (Conceptual)

The following invariants must hold at all times:

1. **Availability window:** A resource cannot deliver flexibility outside its availability window (`earliest_start` to `latest_end`).
2. **Power limits:** A resource cannot deliver more than its `max_power` or less than its `min_power` while active.
3. **Energy requirement:** A resource must meet its `required_kwh` within its `deadline` if dispatched.
4. **Trust ordering:** `trusted_kw` ≤ `expected_kw` ≤ `potential_kw`. Trusted flexibility must never exceed theoretical (potential) flexibility.
5. **State consistency:** A dispatched resource must transition to a terminal state (`completed` or `unavailable`) after its active window.
6. **Duration constraint:** A dispatched resource must operate for at least `minimum_duration` and at most `maximum_duration`.
7. **Feeder capacity:** Total dispatch at any location must not exceed `feeder_capacity`.
8. **Deadline compliance:** Dispatch plan must not schedule beyond resource `deadline`.
9. **Simulation information boundary:** The simulation receives forecasts as input; it does not receive actual future outcomes. The optimizer sees forecasts; it must not receive actual future outcomes.

See CONTRACTS.md for validation against these invariants at the interface level.

---

## 7. Resource Lifecycle

### 7.1 State Transitions

```
available → dispatched → completed
available → unavailable
unavailable → available (when conditions permit)
```

Additional notes:

- Resources may also transition from `unavailable` back to `available` when conditions permit (e.g., SOC replenished for EV, temperature restored for water heater).
- `dispatched` → `unavailable` is possible if a resource becomes unavailable mid-dispatch (failure, override to full stop).
- The state is a per-resource, per-time-step value during simulation.

### 7.2 Lifecycle per Simulation Time Step

For each 15-minute time step:

1. Resource state is observed (`available`, `dispatched`, `completed`, `unavailable`).
2. If `available` and matched to an opportunity, trust is computed.
3. If selected for dispatch, resource transitions to `dispatched`.
4. Simulation models actual response; resource may transition to `completed` or remain `dispatched` or transition to `unavailable`.
5. Trust state for the next time step is informed by this step's verification.

---

## 8. Temporal Concepts

### 8.1 Time Resolution

The simulation operates on a **15-minute system time resolution**. This is documented in PROJECT.md, DATA_SPEC.md, and ARCHITECTURE.md.

### 8.2 Time-Indexed Entities

Several entities are time-indexed:

- TrustState (per resource, per time step)
- DispatchPlan x[i,t] (per resource i, per time step t)
- RenewableForecast (per time step)
- ActualResponse (per resource, per time step)
- VerificationResult (per dispatch event, per time step)

### 8.3 Temporal Ordering

The core loop progresses through temporal stages:

```
Observe(t) → Represent(t) → Estimate(t) → Trust(t) → Match(t) → Dispatch(t) → Simulate(t) → Verify(t) → Learn(t)
```

Where `t` is the current 15-minute time step.

Learning at time `t` influences trust estimates at time `t+1` and beyond.

---

## 9. Flexibility Concepts

### 9.1 Flexibility Representation

Each FlexibilityResource is represented for algorithmic purposes with:

- Operational constraints (power limits, availability windows, energy requirements, deadlines, minimum duration, process/comfort limits).
- Behavior characteristics (historical response, override rate, availability rate).
- A time-dependent trust state.

The same representation must be usable by estimation, optimization, simulation, and learning stages without re-derivation (per ALGORITHM_SPEC.md).

### 9.2 Potential Flexibility

- Definition: Maximum shiftable capacity implied by physical limits.
- Source: Resource specifications, rated power, availability windows.
- Status: Deterministic from resource data; no uncertainty.
- Relationship: Upper bound for all other flexibility categories.

### 9.3 Expected Flexibility

- definition: Expected deliverable capacity given current evidence.
- Source: Resource constraints + current state + behavior + forecast uncertainty.
- Status: Estimated; subject to uncertainty.
- Relationship: Bounded by potential; input to trust computation.

### 9.4 Trusted Flexibility

- Definition: Confidence-weighted expected deliverable capacity used for dispatch decisions.
- Source: Expected flexibility × confidence.
- Status: Computed per time step; time-dependent.
- Relationship: Bounded by expected; input to optimization.

### 9.5 Delivered Flexibility

- Definition: Actual flexibility delivered as measured by verification.
- Source: Simulation of actual response vs. dispatched plan.
- Status: Observed after dispatch simulation.
- Relationship: Compared against dispatched amount; feeds learning.

---

## 10. Trust Concepts

### 10.1 Trust is Computed, Not Stored

Trust is a time-dependent state derived from evidence each cycle. It is not a static device attribute. See DOMAIN_MODEL.md section 4.2.

### 10.2 Trust Computation Pipeline (Conceptual)

```
potential → expected → confidence → trusted
```

- **Potential:** From physical limits (domain model).
- **Expected:** From potential, adjusted by behavior, state, uncertainty (estimation).
- **Confidence:** From historical reliability, current uncertainty (AI/ML).
- **Trusted:** Expected × confidence (AI/ML / optimization input).

The exact formulas for each step are TBD per ALGORITHM_SPEC.md.

### 10.3 What Affects Confidence

- Historical response accuracy (override rate, availability rate)
- Current resource state (SOC, temperature, process stage)
- Forecast uncertainty (renewable, demand)
- Constraint tightness at the candidate time
- Recent verification outcomes (learning)

### 10.4 Trust Decay and Recovery

- Trust may degrade after a verification shows under-delivery or override.
- Trust may recover as recent behavior shows improved reliability.
- The specific recovery/degradation mechanism is TBD.

---

## 11. Dispatch Concepts

### 11.1 Dispatch Plan

- Represented as `x[i,t]` = amount of flexibility dispatched from resource `i` at time `t`.
- Units: kW.
- Must satisfy hard constraints (per ALGORITHM_SPEC.md): power limits, availability, energy requirements, deadlines, minimum duration, feeder capacity, process constraints.
- Optimized for objective categories (per ALGORITHM_SPEC.md): renewable absorption, trusted flexibility value, discomfort/process cost, rebound, risk/uncertainty, peak pressure.

### 11.2 Dispatch Instruction

- A specific, actionable instruction derived from the dispatch plan.
- Addressed to a specific resource at a specific time.
- Specifies the dispatched amount `x[i,t]`.

### 11.3 Baseline vs. Trust-Aware Dispatch

| Category | Input to Scheduler |
|---|---|
| Baseline (theoretical) | Potential flexibility (theoretical maximum) |
| Trust-aware (MVP experiment) | Trusted flexibility (confidence-weighted) |

Both schedulers run on identical scenarios. See EXPERIMENT_SPEC.md for comparison methodology.

---

## 12. Verification Concepts

### 12.1 Verification Inputs

- Dispatch plan (what was requested)
- Actual response (what was delivered in simulation)

### 12.2 Verification Outputs

- Delivered flexibility per resource per time step
- Dispatched flexibility per resource per time step
- Error (delivered - dispatched)
- Constraint adherence (was the dispatched plan feasible given actual conditions?)
- Override events (where actual differed from dispatched due to override/failure)

### 12.3 Verification vs. M&V

Verification in the MVP is simulation-based and is not required to comply with regulatory M&V protocols (per PROJECT.md). It is conceptually related to M&V but serves a different purpose: updating trust estimates rather than settling payments.

---

## 13. Learning Concepts

### 13.1 Learning Input

Verification outcomes (actual vs. dispatched, errors, override events).

### 13.2 Learning Output

Updated parameters for future trust estimation (e.g., adjusted override rates, availability rates, confidence calibration).

### 13.3 Learning Scope

- Learning updates trust estimates, not domain model constraints.
- Learning operates at the AI/ML boundary (per ARCHITECTURE.md).
- Learning is part of the core loop (Verify → Learn).
- The specific update rule is TBD per ALGORITHM_SPEC.md.

### 13.4 What Learning Must NOT Do

- Learning must not alter resource physical constraints.
- Learning must not alter forecast data.
- Learning must not affect past trust estimates (only future ones).

---

## 14. Scenario and Simulation Concepts

### 14.1 Scenario

A defined set of conditions under which a simulation runs, including:

- Resource set and their constraints
- Renewable forecasts
- Disruption scenarios (forecast errors, non-compliance, failures, rebound)
- Random seeds for reproducibility

### 14.2 Simulation Run

A complete execution of the simulation engine for a scenario, producing:

- Time-stepped actual responses
- System state evolution
- Renewable availability evolution

### 14.3 Experiment Run

A simulation run comparing baseline and trust-aware schedulers on equivalent scenarios. See EXPERIMENT_SPEC.md.

---

## 15. Resource Type Profiles

### 15.1 EV Charging

- Specific constraints: departure deadline, SOC target/range, charging power limits, charge rate curve.
- Specific behavior: arrival patterns, dwell time, override tendency on departure deadline pressure.
- Specific flexibility: Can shift charging to off-peak or renewable-rich windows; limited by departure time.

### 15.2 Water Heaters

- Specific constraints: temperature band, recovery time, draw profile, thermostat setpoint.
- Specific behavior: thermal inertia, recovery after draw, override on comfort dissatisfaction.
- Specific flexibility: Can shift heating to renewable-rich windows; limited by reheat time and comfort band.

### 15.3 Flexible Industrial Batch/Process

- Specific constraints: process window, minimum run time, batch sequence, thermal storage, process continuity requirements.
- Specific behavior: Process stage dependency, override on production pressure, minimum batch sizes.
- Specific flexibility: Can shift batch timing; limited by process windows and minimum run times.

---

## 16. Current Status

DRAFT
