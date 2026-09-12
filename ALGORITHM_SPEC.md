# ALGORITHM SPEC

## Purpose

Define the core algorithmic logic for GridFlex AI: flexibility representation, flexibility estimation, trust/reliability calculation, opportunity detection, optimization formulation, constraints, objective function, confidence calculations, scenario logic, and learning/update logic.

## Scope

This document is the authoritative source for the conceptual algorithmic flow and the structure of the optimization problem. It records what is known and clearly marks unresolved mathematical details. It does not invent final formulas, weights, or model architectures.

## Authority

This document is the authoritative source for core algorithmic logic, flexibility representation, flexibility estimation, trust/reliability calculation, opportunity detection, optimization formulation, constraints, objective function, confidence calculations, scenario logic, and learning/update logic. Final mathematical weights and coefficients that are not yet finalized are marked as TBD and must not be invented here. Other documents must reference this document for algorithmic concepts rather than redefine them.

## Current Status

PARTIALLY DEFINED

---

## 1. Conceptual Decision Flow

The core algorithmic flow follows this sequence:

```
Observe → Represent → Estimate → Trust → Match → Dispatch → Simulate → Verify → Learn
```

This ordering is authoritative: Dispatch (formulate plan) must precede Simulate (test plan). Verification follows simulation. Learning updates future estimates from verified outcomes.

| Stage | Description | Document Cross-Reference |
|---|---|---|
| **Observe** | Observe current system conditions, renewable availability, resource states, and forecasts | ARCHITECTURE.md (runtime flow) |
| **Represent** | Represent each flexible resource using its operational constraints from the domain model | DOMAIN_MODEL.md (FlexibilityResource) |
| **Estimate** | Estimate how reliably each resource can deliver flexibility given its behavior history and current uncertainty | This document section 3 |
| **Trust** | Compute a time-dependent trust state (potential_kw, expected_kw, trusted_kw, confidence) | This document section 4 |
| **Match** | Match trusted flexibility with renewable-aligned dispatch opportunities | This document section 5 |
| **Dispatch** | Formulate and solve the optimization problem; issue dispatch instructions | This document section 6 |
| **Simulate** | Simulate dispatch execution before commitment (note: occurs after dispatch plan formulation) | ARCHITECTURE.md (simulation boundary) |
| **Verify** | Compare actual response against dispatched instructions | This document section 8 |
| **Learn** | Update behavior estimates and future trust calculations from verification outcomes | This document section 9 |

**Important ordering note:** In the simulation loop, Dispatch (optimization) occurs BEFORE Simulation. The sequence in the core loop is:

```
At each time step t: Observe(t) → Represent(t) → Estimate(t) → Trust(t) → Match(t) → Dispatch(t) → Simulate(t) → Verify(t) → Learn(t)
```

Where Simulate(t) simulates the dispatch plan formulated at Dispatch(t).

---

## 2. Stage Specifications

### 2.1 Observe

| Property | Value |
|---|---|
| **Input** | System clock, scenario configuration, renewable forecasts (forecast only, NOT actual future outcomes) |
| **Processing** | Read current conditions from simulation state; load relevant forecasts |
| **Output** | System state snapshot at time t |
| **Dependencies** | Persistence (for resource/state data), DATA inflow (forecasts) |
| **Failure behavior** | Use last-known state; flag data staleness |
| **Information available** | Current time, scenario config, forecast data, resource states |
| **Information that must NOT be available** | Actual future outcomes, future verification results |

### 2.2 Represent

| Property | Value |
|---|---|
| **Input** | Resource data from persistence; scenario resource list |
| **Processing** | Load FlexibilityResource representation per DOMAIN_MODEL.md; validate invariants |
| **Output** | Resource representations with constraints, state, behavior |
| **Dependencies** | Domain model (DOMAIN_MODEL.md), Persistence |
| **Failure behavior** | Reject resource with missing critical fields; log error |
| **Information available** | Resource constraints, type, location, rated power, availability, energy, duration, behavioral parameters |
| **Information that must NOT be available** | Computed trust values (computed downstream) |

### 2.3 Estimate

| Property | Value |
|---|---|
| **Input** | Resource representation + behavior history + current state + forecast uncertainty |
| **Processing** | Statistical/ML computation of expected deliverable capacity from evidence |
| **Output** | Expected flexibility (expected_kw) + initial confidence estimate |
| **Dependencies** | AI/ML module, Domain model, Behavior data |
| **Failure behavior** | Flag low confidence; set expected_kw conservatively; do NOT invent precision |
| **Information available** | All fields from FlexibilityResource + historical_response + override_rate + availability_rate + forecast uncertainty |
| **Information that must NOT be available** | Actual future outcomes; trust values (computed in next stage) |

Estimation must account for:

- Historical response reliability (override rate, availability rate, response accuracy).
- Current uncertainty (renewable forecast error, demand uncertainty).
- Constraint tightness at the candidate dispatch time (how close to deadline, how tight energy requirement).

### 2.4 Trust

| Property | Value |
|---|---|
| **Input** | Expected flexibility (from Estimate) + confidence (from Estimate) + resource state |
| **Processing** | Compute time-dependent trust state: potential → expected → confidence → trusted |
| **Output** | Trust state (potential_kw, expected_kw, trusted_kw, confidence) |
| **Dependencies** | Estimate output, resource state |
| **Failure behavior** | If estimate fails, trust = 0 with confidence = 0; do NOT invent trust |
| **Information available** | potential_kw, expected_kw, confidence |
| **Information that must NOT be available** | Actual outcomes at current time step (not yet simulated) |

**Invariant:** trusted_kw ≤ expected_kw ≤ potential_kw.

**Conceptual pipeline:**

```
potential (from physical limits)
  → expected (adjusted by behavior, state, uncertainty)
    → confidence (from historical reliability, current uncertainty)
      → trusted (expected × confidence)
```

The exact formulas for each transformation are **TBD** (see section 12).

**Trust is time-dependent computed state.** It is recomputed each cycle from current evidence — including recent verification outcomes, forecast uncertainty, and resource state.

### 2.5 Match

| Property | Value |
|---|---|
| **Input** | Trust state (trusted_kw per resource per time) + renewable forecast |
| **Processing** | Identify renewable-aligned windows where trusted flexibility can be dispatched to absorb renewables or reduce peak pressure |
| **Output** | Candidate dispatch opportunities (time windows with renewable alignment) |
| **Dependencies** | Trust computation, Renewable forecast data |
| **Failure behavior** | If no opportunities found, log; do NOT force an opportunity |
| **Information available** | Trusted flexibility, renewable forecast (forecast, not actual) |
| **Information that must NOT be available** | Actual future renewable outcomes |

### 2.6 Dispatch (Optimize)

| Property | Value |
|---|---|
| **Input** | Trusted flexibility (from Trust) + opportunities (from Match) + constraints + objective configuration |
| **Processing** | Formulate and solve CP-SAT optimization problem |
| **Output** | Dispatch plan x[i,t] or infeasibility report |
| **Dependencies** | Optimization module (OR-Tools CP-SAT), trusted flexibility, opportunity set |
| **Failure behavior** | Infeasibility → return report; timeout → return partial or timeout; do NOT silently fall back to theoretical capacity |
| **Information available** | Trusted flexibility, constraints, opportunities, objective categories |
| **Information that must NOT be available** | Actual future outcomes (optimization sees forecasts, not actuals) |

Decision variable:

```
x[i,t] = amount of flexibility dispatched from resource i at time t (kW)
```

**Documentation note:** x[i,t] is the dispatch variable. It is determined by the optimization. It is NOT a preset value.

**See section 6 for constraints and objective details.**

### 2.7 Simulate

| Property | Value |
|---|---|
| **Input** | Scenario configuration + dispatch plan (x[i,t]) + renewable forecasts |
| **Processing** | Time-stepped simulation of device behavior, including overrides, failures, rebound, thermal dynamics, process dynamics |
| **Output** | Actual response (what actually happened), system state, renewable conditions |
| **Dependencies** | Simulation engine, Resource models (per resource type profiles in DOMAIN_MODEL.md) |
| **Failure behavior** | Divergence recorded; continue simulation; flag divergence for learning |
| **Information available** | Dispatch plan, scenario config, forecast data, device models |
| **Information that must NOT be available** | Actual future outcomes are modeled (simulated), not known a priori |

**Critical boundary:** The simulator receives forecasts as input. It does NOT receive actual future outcomes. It models/deduces them based on device physics and behavior models.

### 2.8 Verify

| Property | Value |
|---|---|
| **Input** | Dispatch plan (what was dispatched) + actual response (what was delivered in simulation) |
| **Processing** | Compare delivered vs. dispatched at resource and time-step granularity |
| **Output** | Verification result (delivered, dispatched, error, constraint adherence, override events) |
| **Dependencies** | Simulation output, dispatch plan |
| **Failure behavior** | Mismatched data → partial verification with annotation |
| **Information available** | Dispatch amounts, actual delivered amounts, resource states |
| **Information that must NOT be available** | Future verification results |

### 2.9 Learn

| Property | Value |
|---|---|
| **Input** | Verification results (errors, overrides, failures, adherence) |
| **Processing** | Update trust estimation parameters (override rates, availability rates, confidence calibration) |
| **Output** | Updated parameters for future trust estimates |
| **Dependencies** | Verification module, AI/ML learning logic |
| **Failure behavior** | Skip update for invalid verification data; log skip |
| **Information available** | Verification outcomes from current and past time steps |
| **Information that must NOT be available** | Future outcomes |

Learning must:

- Update future trust estimates based on verification outcomes.
- NOT alter resource physical constraints.
- NOT alter forecasts.
- NOT affect past trust estimates.

The specific update rule is **TBD** (see section 12).

---

## 3. Flexibility Representation

Each FlexibilityResource is represented for algorithmic purposes with (per DOMAIN_MODEL.md):

- Operational constraints: power limits, availability windows, energy requirements, deadlines, minimum duration, process/comfort limits.
- Behavior characteristics: historical response, override rate, availability rate.
- A time-dependent trust state.

The same representation must be usable by estimation, optimization, simulation, and learning stages without re-derivation.

### 3.1 Potential Flexibility

- **Definition:** Maximum shiftable capacity implied by physical limits.
- **Source:** Resource specifications (rated_power_kw, max_power, availability windows).
- **Status:** Deterministic from resource data; no uncertainty.
- **Relationship:** Upper bound for Expected and Trusted flexibility.

### 3.2 Expected Flexibility

- **Definition:** Expected deliverable capacity given current evidence.
- **Source:** Resource constraints + current state + behavior + forecast uncertainty.
- **Status:** Estimated; subject to uncertainty.
- **Relationship:** Bounded by potential; input to trust computation.

### 3.3 Trusted Flexibility

- **Definition:** Confidence-weighted expected deliverable capacity used for dispatch decisions.
- **Source:** Expected flexibility × confidence.
- **Status:** Computed per time step; time-dependent.
- **Relationship:** Bounded by expected; input to optimization.

### 3.4 Delivered Flexibility

- **Definition:** Actual flexibility delivered as measured by verification.
- **Source:** Simulation of actual response vs. dispatched plan.
- **Status:** Observed after dispatch simulation.
- **Relationship:** Compared against dispatched amount; feeds learning.

---

## 4. Trust Calculation (Conceptual)

### 4.1 Trust State Fields

| Field | Description | Bounds |
|---|---|---|
| `potential_kw` | Theoretical maximum deliverable capacity | ≥ expected_kw |
| `expected_kw` | Expected deliverable capacity given current evidence | ≥ trusted_kw; ≤ potential_kw |
| `trusted_kw` | Confidence-weighted deliverable capacity used for dispatch | ≤ expected_kw |
| `confidence` | Confidence level in the trust estimate | [0.0, 1.0] |

**Invariant:** trusted_kw ≤ expected_kw ≤ potential_kw; confidence ∈ [0.0, 1.0].

### 4.2 Conceptual Trust Pipeline

```
potential (from physical limits, deterministic)
  ↓ adjust for: behavior, state, uncertainty
expected (estimated deliverable)
  ↓ weight by: confidence
trusted (used for dispatch)

confidence (from historical reliability, current uncertainty)
```

### 4.3 What Affects Confidence

- Historical response accuracy (override rate, availability rate, response accuracy).
- Current resource state (SOC for EV, temperature for water heater, process stage for industrial).
- Forecast uncertainty (renewable forecast error, demand uncertainty).
- Constraint tightness at the candidate time (proximity to deadline, energy requirement pressure).
- Recent verification outcomes (learning).

### 4.4 Exact Formulas

**TBD — requires algorithm specification phase.**

The following exact formulas are NOT defined and must not be invented at this phase:

- Exact formula for expected_kw given potential, behavior, and uncertainty.
- Exact formula for confidence given evidence.
- Exact formula for trusted_kw given expected and confidence.
- How uncertainty is propagated through the trust computation.
- How learning updates parameters over time.

**Proposed options for future consideration:**

1. Bayesian updating of confidence from historical data.
2. Weighted historical average of response accuracy.
3. Probabilistic model of resource availability.
4. Statistical regression on features derived from resource state and history.

These are PROPOSED OPTIONS, not decisions.

---

## 5. Renewable Opportunity Detection

Opportunities are renewable-aligned windows where dispatching flexibility would absorb renewable energy or reduce peak pressure.

### 5.1 Detection Inputs

- Renewable forecast (solar generation forecast at 15-minute resolution).
- Demand forecast (system demand at 15-minute resolution).
- Trusted flexibility availability per resource per time step.

### 5.2 Opportunity Criteria (Conceptual)

An opportunity exists at time t when:

- Renewable generation exceeds a baseline threshold (TBD: specific threshold is TBD).
- Flexible resources have non-zero trusted flexibility at time t.
- No hard constraint prevents dispatch at time t.

### 5.3 Exact Criteria

**TBD** — threshold values, detection logic, and opportunity scoring are TBD.

---

## 6. Dispatch Formulation

### 6.1 Decision Variable

```
x[i,t] = amount of flexibility dispatched from resource i at time t (kW)
```

Where:
- i indexes resources (1 to N).
- t indexes 15-minute time steps (1 to T).
- x[i,t] ≥ 0 (non-negative dispatch).

### 6.2 Hard Constraints

The following constraints must be enforced:

| Category | Constraint | Source |
|---|---|---|
| **Power limits** | x[i,t] ≤ max_power[i]; x[i,t] ≥ min_power[i] when active | DOMAIN_MODEL.md |
| **Availability** | x[i,t] = 0 outside [earliest_start, latest_end] | DOMAIN_MODEL.md |
| **Energy requirements** | Σ_t x[i,t] × 0.25 ≥ required_kwh[i] (at 15-min resolution, 0.25 = 15min in hours) | DOMAIN_MODEL.md |
| **Deadline** | Energy delivered by deadline | DOMAIN_MODEL.md |
| **Minimum duration** | If x[i,t] > 0, then x[i,t'] > 0 for at least minimum_duration[i] consecutive steps | DOMAIN_MODEL.md |
| **Feeder capacity** | Σ_i x[i,t] ≤ feeder_capacity[location] | DOMAIN_MODEL.md |
| **Process constraints** | Type-specific constraints (e.g., industrial minimum run time, batch windows) | DOMAIN_MODEL.md |
| **Trust bounds** | x[i,t] ≤ trusted_kw[i,t] (dispatch cannot exceed trusted flexibility) | ALGORITHM_SPEC.md |

### 6.3 Objective Categories

The objective function includes multiple categories. Individual weights and exact formulation are **TBD**.

| Category | Description | Direction |
|---|---|---|
| **Renewable absorption** | Maximize renewable energy absorbed by dispatched flexibility | Maximize |
| **Trusted flexibility value** | Maximize utilization of trusted flexibility | Maximize |
| **Discomfort/process cost** | Minimize comfort violations or process disruptions | Minimize |
| **Rebound** | Minimize demand rebound after shifting | Minimize |
| **Risk/uncertainty** | Minimize risk of non-delivery under uncertainty | Minimize |
| **Peak pressure** | Minimize peak demand pressure | Minimize |

**Current formulation status:**

| Aspect | Status |
|---|---|
| Variable x[i,t] | DEFINED |
| Hard constraint categories | DEFINED |
| Objective categories | DEFINED |
| Objective formula | TBD |
| Weights between categories | TBD |
| Risk/uncertainty integration | TBD |
| Rebound modeling in objective | TBD |

### 6.4 Baseline vs. Trust-Aware Dispatch

**BASELINE:** Dispatch against theoretical flexibility (potential_kw).

- Input to optimization: potential_kw as the capacity bound.
- Does NOT account for reliability, behavior, or uncertainty.
- Represents current practice (static ratings).

**TRUST-AWARE:** Dispatch against trusted flexibility (trusted_kw).

- Input to optimization: trusted_kw as the capacity bound.
- Accounts for reliability, behavior, and uncertainty.
- Represents GridFlex AI's approach.

**Both must use equivalent scenarios.** Identical resource sets, forecasts, conditions, and time horizons. The only difference is the capacity input to the scheduler (potential vs. trusted).

**Why this comparison exists:** To empirically determine whether trust-aware dispatch produces more reliable decisions under uncertainty, even if raw renewable absorption is not always higher. Per EXPERIMENT_SPEC.md hypotheses.

### 6.5 Infeasibility

When the optimization cannot find a feasible solution:

1. Return an infeasibility report identifying which constraints are binding.
2. Do NOT silently degrade to theoretical capacity.
3. Do NOT force a suboptimal solution.
4. Log the infeasibility for analysis.
5. Per ARCHITECTURE.md: "fall back to a deterministic heuristic or report infeasibility; do not silently degrade to theoretical capacity."

---

## 7. Simulation Behavior

### 7.1 Input

Scenario + dispatch plan x[i,t] + renewable forecasts.

### 7.2 Behavior Modeling

For each resource type, the simulator models:

- **EV Charging:** SOC dynamics, charge rate limits, departure deadline enforcement, override on deadline pressure, recovery after full charge.
- **Water Heaters:** Thermal dynamics, temperature band maintenance, recovery time after draw, thermostat behavior, override on comfort dissatisfaction.
- **Flexible Industrial Batch/Process:** Process stage progression, minimum run time enforcement, batch window constraints, thermal storage dynamics, override on production pressure.

### 7.3 Disruption Modeling

The simulator models:

- **Override:** Resource operator overrides dispatch command; actual response < dispatched.
- **Device failure:** Resource becomes unavailable mid-dispatch; actual response = 0 for affected period.
- **Rebound:** Demand returns after being shifted; net reduction is less than shift amount.

### 7.4 Simulation Information Boundary

- The simulator receives forecasts as input (known at time t).
- The simulator does NOT receive actual future outcomes.
- The simulator models actual outcomes based on physics, behavior, and stochastic elements.
- This boundary is critical to prevent information leakage from the decision loop.

---

## 8. Verification

### 8.1 Input

Dispatch plan (x[i,t]) + actual response (from simulation).

### 8.2 Output

| Field | Description |
|---|---|
| `delivered` | Actual flexibility delivered per resource per time step |
| `dispatched` | Dispatched flexibility per resource per time step |
| `error` | Delivered - dispatched (kW) |
| `constraint_adherence` | Whether dispatched plan was feasible given actual conditions |
| `override_events` | Override occurrences (actual < dispatched due to override) |
| `failure_events` | Device failure occurrences |
| `rebound_events` | Rebound occurrences |
| `overall_reliability` | Ratio of total delivered to total dispatched |

### 8.3 Key Metrics Derived

- **Delivered flexibility error** = |dispatched - delivered|
- **Actual/committed reliability** = total_delivered / total_dispatched
- **Overcommitment** = dispatched > potential (should not occur but is monitored)

---

## 9. Learning Update

### 9.1 Conceptual Purpose

Learning updates trust estimation parameters based on verification outcomes, closing the loop from Delivered Flexibility back to Expected/Trusted Flexibility.

### 9.2 What Changes

- Override rate: Adjusted based on observed override frequency.
- Availability rate: Adjusted based on observed availability vs. requested.
- Confidence calibration: Adjusted based on historical prediction accuracy (e.g., if confidence was 0.8 and reliability was 0.7, calibration shifts).

### 9.3 What Does NOT Change

- Resource physical constraints (rated_power_kw, max_power, min_power, deadlines, etc.).
- Forecast data.
- Past trust estimates (only future estimates are updated).
- Domain model definitions.

### 9.4 Learning Rule

**TBD** — the specific update rule (e.g., exponential moving average, Bayesian update, etc.) is not defined at this phase.

**Proposed options:**

1. Exponential moving average of historical response rate.
2. Bayesian update of availability probability.
3. Calibration layer on confidence outputs.
4. Sliding window of recent verification outcomes.

These are PROPOSED OPTIONS, not decisions.

---

## 10. Stage Dependency Graph

```
Observe
  ↓
Represent
  ↓
Estimate
  ↓
Trust
  ↓
Match
  ↓ (opportunity detection feeds into)
Dispatch (Optimize)
  ↓ (dispatch plan flows to)
Simulate
  ↓ (actual response flows to)
Verify
  ↓ (verification outcomes flow to)
Learn
  ↓ (updated parameters feed into)
Estimate (next cycle)
```

Learning feeds back into Estimate for the next time step and future time steps, closing the loop.

---

## 11. Algorithm Classification

### CURRENTLY DEFINED

- Decision variable: x[i,t]
- Hard constraint categories: power limits, availability, energy requirements, deadlines, minimum duration, feeder capacity, process constraints
- Objective categories: renewable absorption, trusted flexibility value, discomfort/process cost, rebound, risk/uncertainty, peak pressure
- Trust pipeline: potential → expected → confidence → trusted
- Core flow: Observe → Represent → Estimate → Trust → Match → Dispatch → Simulate → Verify → Learn
- Simulation resolution: 15 minutes
- Baseline vs. trust-aware comparison

### PROPOSED OPTIONS (not decided)

- Trust computation formula (Bayesian, weighted average, regression, probabilistic model)
- Learning update rule (EMA, Bayesian, calibration layer, sliding window)
- Opportunity detection criteria (threshold values, scoring method)
- Specific ML model for confidence estimation

### TBD / REQUIRES DECISION

- Exact objective function formula
- Objective category weights
- Renewable absorption threshold for opportunity detection
- Risk/uncertainty integration method
- Rebound quantification in objective
- Forecast uncertainty quantification method
- Infeasibility fallback heuristic

---

## 12. Unresolved Mathematical Details

The following are TBD — requires algorithm specification phase:

| Item | Status |
|---|---|
| Exact mathematical formulation of the objective function | TBD |
| Final weights and coefficients for objective categories | TBD |
| Exact formula for expected_kw given potential, behavior, and uncertainty | TBD |
| Exact formula for confidence given evidence | TBD |
| Exact formula for trusted_kw given expected and confidence | TBD |
| How uncertainty is propagated through the optimization | TBD |
| Renewable opportunity detection criteria | TBD |
| Scenario logic details | TBD |
| Learning/update rule specifics | TBD |
| Infeasibility fallback heuristic | TBD |
| Confidence calibration method | TBD |

These must not be invented at this phase. They will be defined during the algorithm specification phase.

---

## 13. Current Status

PARTIALLY DEFINED
