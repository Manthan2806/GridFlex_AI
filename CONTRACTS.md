# CONTRACTS

## Purpose

Define the internal interfaces, API contracts, request/response structures, domain-to-service interfaces, service boundaries, event contracts, model I/O contracts, validation expectations, and error contracts for GridFlex AI.

## Scope

This document is the authoritative source for interface contracts at the current phase. Machine-readable contract files (OpenAPI, JSON schemas, model I/O schemas, event schemas) will be created in the `contracts/schemas/` directory during the contract design phase.

## Authority

This document is the authoritative source for internal interfaces, API contracts, request/response structures, domain-to-service interfaces, service boundaries, event contracts, model I/O contracts, validation expectations, and error contracts. Implementation must conform to these contracts.

## Current Status

DRAFT

---

## 1. Contract Status

Machine-readable contract files do not exist yet. The `contracts/schemas/` directory is reserved for:

- OpenAPI specification
- JSON schemas
- Model I/O schemas
- Event schemas

These will be created during the contract design phase, after the architecture stabilizes. This document defines the conceptual contract boundaries that those files will formalize.

---

## 2. Service Boundary Contracts

### 2.1 Frontend ↔ Backend

| Property | Value |
|---|---|
| **Purpose** | Scenario configuration, simulation execution, results retrieval, dispatch review |
| **Caller** | Frontend (React + TypeScript) |
| **Provider** | Backend (Python + FastAPI) |
| **Protocol** | REST-first |
| **Direction** | Frontend initiates; backend responds |
| **Content** | Scenario configuration requests, simulation run requests, result queries, dispatch review data |
| **Validation** | Request body validated against contract schemas; response validated against defined shape |
| **Failure behavior** | Frontend displays error messages from standardized error responses; no silent degradation |
| **Ownership** | Backend owns API design; Frontend owns UI that consumes it |
| **Versioning** | Version prefix on API paths (e.g., `/v1/`); breaking changes require version bump |

### 2.2 Backend ↔ Domain

| Property | Value |
|---|---|
| **Purpose** | Access and manipulation of domain entities (FlexibilityResource, TrustState, Opportunity, DispatchPlan, Scenario) |
| **Caller** | Backend services (orchestration, simulation, optimization coordination) |
| **Provider** | Domain Layer |
| **Protocol** | In-process function calls / domain model interfaces |
| **Direction** | Backend calls domain; domain does not call backend |
| **Content** | Domain entity creation, query, and state updates; invariant enforcement |
| **Validation** | All inputs validated against domain invariants (per DOMAIN_MODEL.md) |
| **Failure behavior** | Invariant violation raises domain exception; backend handles and translates |
| **Ownership** | Domain layer owns entity definitions and invariants; backend owns orchestration |
| **Versioning** | Domain model changes require coordination across all teams |

### 2.3 Backend ↔ AI/ML

| Property | Value |
|---|---|
| **Purpose** | Flexibility estimation, trust computation, forecasting, learning updates |
| **Caller** | Backend (orchestration) |
| **Provider** | AI/ML module |
| **Protocol** | In-process function calls (within Python monolith) |
| **Direction** | Backend invokes; AI/ML responds |
| **Content** | See Model I/O Contract section below |
| **Validation** | Inputs validated against model I/O contract; outputs validated before use |
| **Failure behavior** | Low confidence flag returned; backend continues with degraded trust; does not halt loop |
| **Ownership** | AI/ML team owns estimation and trust logic; backend owns invocation and orchestration |
| **Versioning** | Model I/O schema changes require coordination with backend and domain teams |

### 2.4 Backend ↔ Optimization

| Property | Value |
|---|---|
| **Purpose** | Dispatch problem formulation and solving |
| **Caller** | Backend (orchestration) |
| **Provider** | Optimization module (OR-Tools CP-SAT) |
| **Protocol** | In-process library invocation |
| **Direction** | Backend formulates and invokes; optimization solves and returns |
| **Content** | See Model I/O Contract section below |
| **Validation** | Problem formulation validated for CP-SAT compatibility; solution validated against invariants |
| **Failure behavior** | Infeasibility reported explicitly; solver timeout handled; fallback to deterministic heuristic (TBD) |
| **Ownership** | Backend owns problem formulation; optimization module owns solving |
| **Versioning** | Problem formulation schema changes require coordination with backend and AI/ML |

### 2.5 Backend ↔ Simulation

| Property | Value |
|---|---|
| **Purpose** | Time-stepped simulation of device behavior and system conditions |
| **Caller** | Backend (orchestration) |
| **Provider** | Simulation engine |
| **Protocol** | In-process function calls |
| **Direction** | Backend orchestrates; simulation executes |
| **Content** | Scenario configuration in; time-stepped actual outcomes out |
| **Validation** | Scenario validated before simulation starts; intermediate results validated per step |
| **Failure behavior** | Divergence recorded; does not halt loop; verification flags issues |
| **Ownership** | Backend owns orchestration; simulation engine team owns engine |
| **Versioning** | Simulation input/output schema changes require coordination with backend and verification |

### 2.6 Backend ↔ Persistence

| Property | Value |
|---|---|
| **Purpose** | Durable storage and retrieval of all system data |
| **Caller** | Backend |
| **Provider** | PostgreSQL |
| **Protocol** | Database queries via data access layer |
| **Direction** | Backend reads and writes; no other component accesses directly |
| **Content** | Resources, scenarios, forecasts, dispatch plans, trust states, results, experiment data |
| **Validation** | Data validated against schema before persistence; retrieved data validated before use |
| **Failure behavior** | Connection failure → retry with fallback; data corruption → alert, use last-known good |
| **Ownership** | Backend owns data access patterns; persistence layer owns storage engine |
| **Versioning** | Schema migrations require coordination across all teams |

### 2.7 Simulation → Verification

| Property | Value |
|---|---|
| **Purpose** | Pass actual outcomes from simulation to verification |
| **Caller** | Simulation engine |
| **Provider** | Verification module |
| **Protocol** | In-process function calls |
| **Direction** | Simulation produces; verification consumes |
| **Content** | Actual response data, dispatched plan data |
| **Validation** | Actual response validated for plausibility; dispatched plan validated for completeness |
| **Failure behavior** | Invalid data flagged; verification returns partial result with error annotation |
| **Ownership** | Simulation produces data; verification defines comparison logic |

### 2.8 Verification → Learning

| Property | Value |
|---|---|
| **Purpose** | Pass verification outcomes to learning for trust update |
| **Caller** | Verification module |
| **Provider** | Learning module |
| **Protocol** | In-process function calls |
| **Direction** | Verification produces; learning consumes |
| **Content** | Verification results (delivered vs. dispatched, errors, override events) |
| **Validation** | Verification results validated for completeness before learning |
| **Failure behavior** | Learning skips step if verification data is invalid; logs the skip |
| **Ownership** | Verification produces outcomes; learning defines update rules |
| **Versioning** | Outcome schema changes require coordination between verification, learning, and AI/ML |

---

## 3. Model I/O Contracts

### 3.1 Estimation Input

**Purpose:** Compute confidence-weighted deliverable capacity for a resource at a given time.

| Property | Value |
|---|---|
| **Caller** | Backend |
| **Provider** | AI/ML |
| **Input** | Resource representation (per DOMAIN_MODEL.md FlexibilityResource fields) + historical behavior data + current state + forecast uncertainty + time step |
| **Output** | Confidence + trust state (potential_kw, expected_kw, trusted_kw) |
| **Validation** | Resource representation must include all required fields from DOMAIN_MODEL.md; behavior data must cover sufficient history; time step must be valid within scenario horizon |
| **Failure behavior** | Return low confidence flag; use fallback trust values (e.g., confidence = 0, trusted_kw = 0); do not invent trust without evidence |
| **Ownership** | AI/ML computes; backend invokes and persists results |
| **Versioning** | Adding input fields (e.g., new state variables) requires version bump; removing fields requires deprecation period |

### 3.2 Estimation Output

| Field | Type | Description |
|---|---|---|
| `potential_kw` | float | Theoretical maximum deliverable |
| `expected_kw` | float | Expected deliverable given evidence |
| `trusted_kw` | float | Confidence-weighted deliverable for dispatch |
| `confidence` | float | Confidence level (0.0 - 1.0) |
| `uncertainty` | float | Uncertainty measure (TBD — scope to be defined) |

**Invariant:** `trusted_kw` ≤ `expected_kw` ≤ `potential_kw`; `confidence` ∈ [0, 1].

### 3.3 Optimization Input

**Purpose:** Solve dispatch optimization using trusted flexibility.

| Property | Value |
|---|---|
| **Caller** | Backend |
| **Provider** | Optimization (OR-Tools CP-SAT) |
| **Input** | Trusted flexibility set + opportunity/constraints + objective configuration |
| **Output** | Dispatch plan (x[i,t]) or infeasibility report |
| **Validation** | All trusted flexibility values must be ≤ potential; all constraints must be well-formed; objective configuration must be defined |
| **Failure behavior** | Infeasibility → return infeasibility report with constraint analysis; timeout → return timeout with partial result if available; do NOT silently fall back to theoretical capacity |
| **Ownership** | Backend formulates; optimization solves; AI/ML provides trusted flexibility |
| **Versioning** | Adding constraint types requires version bump; objective changes require coordination with all teams |

### 3.4 Optimization Output

**Success case:**

| Field | Type | Description |
|---|---|---|
| `dispatch_plan` | List of {resource_id, time_step, power_kw} | Dispatched flexibility x[i,t] |
| `objective_value` | float | Achieved objective value |
| `status` | enum | `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `TIMEOUT` |
| `infeasibility_report` | (conditional) | Constraint analysis if infeasible |

### 3.5 Simulation Input

| Property | Value |
|---|---|
| **Caller** | Backend |
| **Provider** | Simulation engine |
| **Input** | Scenario configuration + dispatch plan + renewable forecasts |
| **Output** | Time-stepped actual response, system state, renewable conditions |
| **Validation** | Scenario must be valid; dispatch plan must match resource set; forecasts must be at 15-minute resolution |
| **Failure behavior** | Invalid input → reject before execution; divergence → continue, record divergence |
| **Ownership** | Backend orchestrates; simulation engine executes |
| **Versioning** | Input schema changes require coordination with backend, verification, and AI/ML |

### 3.6 Simulation Output

| Field | Type | Description |
|---|---|---|
| `time_steps` | List | Per-step actual response, system state, renewable conditions |
| `actual_response` | List of {resource_id, time_step, delivered_kw} | Actual flexibility delivered |
| `system_state` | List of {time_step, renewable_kw, demand_kw, conditions} | System conditions evolution |
| `override_events` | List | Times where actual deviated from dispatch due to override |
| `failure_events` | List | Times where device failed to respond |
| `rebound_events` | List | Times where demand rebounded after shifting |

### 3.7 Verification Input

| Property | Value |
|---|---|
| **Caller** | Backend |
| **Provider** | Verification module |
| **Input** | Dispatch plan + actual response (from simulation) |
| **Output** | Verification results |
| **Validation** | Both inputs must cover same time steps and resources |
| **Failure behavior** | Mismatched data → return partial verification with annotation |
| **Ownership** | Verification defines comparison; backend provides data |

### 3.8 Verification Output

| Field | Type | Description |
|---|---|---|
| `delivered` | List of {resource_id, time_step, delivered_kw} | Actual delivered flexibility |
| `dispatched` | List of {resource_id, time_step, dispatched_kw} | Dispatched flexibility |
| `error` | List of {resource_id, time_step, error_kw} | Delivered - dispatched |
| `constraint_adherence` | List | Whether constraints were met given actual conditions |
| `override_events` | List | Override occurrences |
| `overall_reliability` | float | Actual/committed ratio |

### 3.9 Learning Input

| Property | Value |
|---|---|
| **Caller** | Backend |
| **Provider** | Learning module |
| **Input** | Verification results |
| **Output** | Updated trust parameters |
| **Validation** | Verification results must be complete and valid |
| **Failure behavior** | Invalid verification → skip update for affected resources; log skip |
| **Ownership** | Learning updates model parameters; AI/ML owns model; backend invokes |

### 3.10 Learning Output

| Field | Type | Description |
|---|---|---|
| `updated_override_rates` | Map<resource_id, float> | Updated override rates |
| `updated_availability_rates` | Map<resource_id, float> | Updated availability rates |
| `confidence_calibration` | Map<resource_id, float> | Calibration adjustments |
| `affected_resources` | List | Resources whose trust parameters changed |

---

## 4. Conceptual REST API Surface

The following API surface is anticipated. These are conceptual, not finalized. Detailed request/response structures will be defined during the contract design phase.

### 4.1 Scenario

| Purpose | Method | Endpoint | Status |
|---|---|---|---|
| Create scenario | POST | `/v1/scenarios` | Proposed |
| List scenarios | GET | `/v1/scenarios` | Proposed |
| Retrieve scenario | GET | `/v1/scenarios/{scenario_id}` | Proposed |
| Delete scenario | DELETE | `/v1/scenarios/{scenario_id}` | Proposed |
| Run simulation | POST | `/v1/scenarios/{scenario_id}/simulate` | Proposed |
| Get simulation status | GET | `/v1/scenarios/{scenario_id}/simulations/{sim_id}/status` | Proposed |
| Get simulation results | GET | `/v1/scenarios/{scenario_id}/simulations/{sim_id}/results` | Proposed |

### 4.2 Resources

| Purpose | Method | Endpoint | Status |
|---|---|---|---|
| List resources | GET | `/v1/resources` | Proposed |
| Create resource | POST | `/v1/resources` | Proposed |
| Retrieve resource | GET | `/v1/resources/{resource_id}` | Proposed |
| Update resource | PUT | `/v1/resources/{resource_id}` | Proposed |
| Get resource trust state | GET | `/v1/resources/{resource_id}/trust` | Proposed |

### 4.3 Dispatch

| Purpose | Method | Endpoint | Status |
|---|---|---|---|
| Get dispatch plan | GET | `/v1/scenarios/{scenario_id}/dispatch` | Proposed |
| Review dispatch | GET | `/v1/scenarios/{scenario_id}/dispatch/review` | Proposed |
| Get verification | GET | `/v1/scenarios/{scenario_id}/simulations/{sim_id}/verification` | Proposed |

### 4.4 Results

| Purpose | Method | Endpoint | Status |
|---|---|---|---|
| Get experiment results | GET | `/v1/experiments/{experiment_id}/results` | Proposed |
| Get metrics summary | GET | `/v1/experiments/{experiment_id}/metrics` | Proposed |

### 4.5 Trust / Flexibility Information

| Purpose | Method | Endpoint | Status |
|---|---|---|---|
| Get flexibility representation | GET | `/v1/resources/{resource_id}/flexibility` | Proposed |
| Get trust history | GET | `/v1/resources/{resource_id}/trust/history` | Proposed |
| Get forecast data | GET | `/v1/scenarios/{scenario_id}/forecasts` | Proposed |

### 4.6 Health / System

| Purpose | Method | Endpoint | Status |
|---|---|---|---|
| System health | GET | `/v1/health` | Proposed |
| System info | GET | `/v1/info` | Proposed |

### 4.7 Error Conditions

| Error | HTTP Status | Scenario |
|---|---|---|
| Validation error | 400 | Malformed or incomplete request body |
| Not found | 404 | Resource, scenario, or simulation not found |
| Conflict | 409 | Resource in incompatible state; duplicate creation |
| Unprocessable | 422 | Valid syntax but semantic error (e.g., infeasible scenario) |
| Internal server error | 500 | Unhandled system error |
| Optimization infeasible | 422 | Dispatch problem infeasible |
| Optimization timeout | 504 | Solver exceeded time limit |
| Low confidence | 206 | Results returned with low confidence flag |

---

## 5. Event Contracts (To Be Formalized)

Internal events for state transitions and loop stages will be defined during the contract design phase. Conceptual events include:

- Resource state changes (available → dispatched, dispatched → completed, etc.)
- Dispatch issued
- Verification completed
- Trust updated
- Simulation step completed
- Scenario started / completed
- Experiment started / completed

---

## 6. Error Categories

| Category | Examples | Behavior |
|---|---|---|
| **Validation errors** | Malformed requests, missing fields, invalid types | 400; return field-level error details |
| **Domain errors** | Invariant violations, invalid state transitions | 422; return domain-specific error message |
| **Optimization errors** | Infeasibility, solver timeout | 422 (infeasible) or 504 (timeout); return diagnostic info |
| **Estimation errors** | Insufficient data, low confidence | 206 with low confidence flag; or 422 if completely unable |
| **Simulation errors** | Divergence, invalid configuration | 200 with divergence annotation; or 422 if invalid config |
| **Persistence errors** | Connection failure, data corruption | 500; retry logic; alert |
| **Authorization errors** | (Future) | 401 / 403 |

---

## 7. Validation Expectations

- All inbound requests are validated against contract schemas before processing.
- Domain inputs are validated against invariants from DOMAIN_MODEL.md.
- Outputs are validated against model I/O contracts before being returned or persisted.
- Trust outputs must satisfy `trusted_kw` ≤ `expected_kw` ≤ `potential_kw`.
- Simulation outputs must be physically plausible (power within limits, energy balance).
- Verification outputs must compare against actual dispatched amounts.

---

## 8. Frozen For Parallel Implementation

The following minimum contracts are FROZEN. All four teams may implement against these boundaries independently.

### 8.1 Domain / Resource Contract

**Purpose:** Shared representation of flexible resources consumed by Frontend, Backend, AI/ML, and Simulation.

**Canonical fields (per DOMAIN_MODEL.md):**

| Category | Fields |
|---|---|
| Identity | `id`, `type`, `location_id`, `rated_power_kw` |
| Availability | `earliest_start`, `latest_end` |
| Energy | `required_kwh`, `minimum_kwh`, `maximum_kwh` |
| Duration | `minimum_duration`, `maximum_duration` |
| Constraints | `deadline`, `min_power`, `max_power`, comfort/process limits |
| Behavior | `historical_response`, `override_rate`, `availability_rate` |
| Trust (computed) | `potential_kw`, `expected_kw`, `trusted_kw`, `confidence` |
| State | Resource state: `available`, `dispatched`, `completed`, `unavailable` |

**Distinctions:**

- **Resource capability:** `type`, `rated_power_kw`, `max_power`, `min_power`, physical limits.
- **Flexibility:** `required_kwh`, `minimum_kwh`, `maximum_kwh`, `earliest_start`, `latest_end`, `deadline`, `minimum_duration`, `maximum_duration`, comfort/process limits — what the resource CAN do operationally.
- **Trust state:** `potential_kw`, `expected_kw`, `trusted_kw`, `confidence` — how reliably the flexibility can be delivered.
- **Resource state:** `available`, `dispatched`, `completed`, `unavailable` — current operational status.

**Owning document:** DOMAIN_MODEL.md.

**Must not be independently redefined by any team.**

### 8.2 AI/ML → Backend Contract

**Purpose:** Flexibility and trust computation boundary.

**Caller:** Backend.
**Provider:** AI/ML module.

**Input:**

| Field | Description |
|---|---|
| Resource representation | FlexibilityResource fields (per domain contract above) |
| Historical behavior | `historical_response`, `override_rate`, `availability_rate` |
| Current state | Resource state, trust state from previous cycle |
| Forecast uncertainty | Renewable/demand forecast uncertainty at candidate time steps |
| Time step | Current 15-minute time step |

**Output:**

| Field | Description |
|---|---|
| `potential_kw` | Theoretical maximum deliverable |
| `expected_kw` | Expected deliverable given evidence |
| `trusted_kw` | Confidence-weighted deliverable for dispatch |
| `confidence` | Confidence level (0.0–1.0) |
| Resource identifiers | `id`, `type`, `location_id`, time step |

**Validation:** `trusted_kw` ≤ `expected_kw` ≤ `potential_kw`; `confidence` ∈ [0.0, 1.0].

**Failure behavior:** Flag low confidence; return conservative estimates; do NOT invent trust without evidence.

**Owning document:** CONTRACTS.md, ALGORITHM_SPEC.md.

### 8.3 Backend → Optimization Contract

**Purpose:** Dispatch problem formulation boundary.

**Caller:** Backend.
**Provider:** Optimization module.

**Input:**

| Field | Description |
|---|---|
| Resources | Relevant FlexibilityResources for the dispatch window |
| Trusted flexibility | `trusted_kw` per resource per time step |
| Resource constraints | Power limits, availability windows, energy requirements, deadlines, minimum duration, process constraints |
| Renewable/opportunity information | Detected opportunities with time windows |
| System constraints | `feeder_capacity` per location |
| Decision variable | `x[i,t]` = amount of flexibility dispatched from resource i at time t (kW) |

**Output:**

| Field | Description |
|---|---|
| `dispatch_plan` | List of {resource_id, time_step, power_kw} representing `x[i,t]` |
| `objective_value` | Achieved objective value |
| `status` | OPTIMAL, FEASIBLE, INFEASIBLE, or TIMEOUT |
| `infeasibility_report` | Constraint analysis (if infeasible) |

**Validation:** All `x[i,t]` must satisfy hard constraints; `x[i,t]` ≤ `trusted_kw[i,t]`.

**Failure behavior:** Infeasibility → return report; timeout → return partial or timeout; do NOT silently fall back to theoretical capacity.

**Owning document:** CONTRACTS.md, ALGORITHM_SPEC.md.

### 8.4 Backend → Simulation Contract

**Purpose:** Boundary between dispatch planning and simulation.

**Caller:** Backend.
**Provider:** Simulation engine.

**Input:**

| Field | Description |
|---|---|
| Scenario | Scenario configuration per EXPERIMENT_SPEC.md |
| Initial resource states | Per resource at scenario start |
| Renewable/demand realization inputs | Forecasts at 15-minute resolution (NOT actual future outcomes) |
| Dispatch plan | `x[i,t]` from optimization |
| System constraints | Feeder capacity, location constraints |

**Output:**

| Field | Description |
|---|---|
| `actual_response` | Per resource per time step: delivered_kw |
| `resource_state_evolution` | State transitions (available → dispatched → completed/unavailable) |
| `renewable_outcomes` | Actual renewable availability per time step |
| `system_outcomes` | System demand/conditions per time step |
| `event_records` | Override events, failure events, rebound events |

**Critical boundary:** Simulation does NOT invent the dispatch plan. The dispatch plan comes from the optimization layer. Simulation models the response TO the dispatch plan.

**Owning document:** CONTRACTS.md, ARCHITECTURE.md.

### 8.5 Simulation → Verification / Learning Contract

**Purpose:** Minimum information for comparing committed/expected vs. actual response.

**Caller:** Verification module.
**Provider:** Simulation engine.

**Input:**

| Field | Description |
|---|---|
| Committed/planned response | What was dispatched: `x[i,t]` per resource per time step |
| Actual simulated response | What was delivered: `actual_response[i,t]` per resource per time step |
| Resource context | Resource type, constraints (for constraint adherence checks) |

**Output:**

| Field | Description |
|---|---|
| `delivered` | Per resource per time step: delivered_kw |
| `dispatched` | Per resource per time step: dispatched_kw |
| `error` | Delivered − dispatched (kW) |
| `overcommitment` | Dispatched beyond what resources can reliably deliver |
| `constraint_adherence` | Whether dispatched plan was feasible given actual conditions |
| `deadline_violations` | Resources not meeting energy requirements within deadlines |
| `rebound_events` | Demand rebound occurrences |
| `actual_committed_reliability` | Ratio of total delivered to total dispatched |
| `override_events` | Override occurrences |
| `failure_events` | Device failure occurrences |

**Supports:**

- Delivery error calculation
- Overcommitment detection
- Constraint/deadline checks
- Rebound analysis
- Trust/reliability update (to Learning)

**Owning document:** CONTRACTS.md, ALGORITHM_SPEC.md, EXPERIMENT_SPEC.md.

### 8.6 Backend → Frontend API Contract

**Purpose:** Minimum API resource shapes for first implementation.

**Caller:** Frontend.
**Provider:** Backend.

**Conceptual resource shapes:**

| Shape | Purpose |
|---|---|
| Resource/portfolio | FlexibilityResource data (identity, type, constraints, trust state) |
| Scenario configuration | Scenario parameters, seeds, resource set |
| Simulation/experiment run request | Scenario ID, scheduler mode (baseline/trust-aware) |
| Run status | Current status of simulation/experiment |
| Results | Trust states, dispatch plans, verification results, learning outcomes |
| Dispatch plan | `x[i,t]` values, objectives, constraints |
| Verification metrics | All metrics per EXPERIMENT_SPEC.md |

**Not frozen:** Authentication, production API versioning, pagination, WebSockets, detailed endpoint paths.

**Owning document:** CONTRACTS.md.

### 8.7 Experiment Contract

**Purpose:** Experiment-level inputs/outputs for Team 4.

**Input:**

| Field | Description |
|---|---|
| Scenario configuration | Per EXPERIMENT_SPEC.md scenario category |
| Seed/reproducibility | Random seed, generator version, parameters |
| Scheduler mode | Baseline (theoretical) or Trust-aware (trusted) |
| Resource set | Resources included (per domain contract) |
| System conditions | Renewable forecasts, demand data, disruption specifications |

**Output:**

| Field | Description |
|---|---|
| Experiment ID | Unique identifier |
| Configuration metadata | Scenario, seed, mode, resource set, conditions |
| Baseline results | Results from theoretical-capacity scheduler |
| Trust-aware results | Results from trusted-capacity scheduler |
| Comparison metrics | All metrics per EXPERIMENT_SPEC.md |

**Philosophy preserved:** Same scenarios, same underlying conditions, different scheduling mechanism — so the comparison is meaningful.

**Owning document:** EXPERIMENT_SPEC.md, CONTRACTS.md.

---

## 9. Not Yet Frozen

The following contracts are NOT yet frozen. They require further decisions before implementation.

| Item | Status | Reason |
|---|---|---|
| API JSON field naming (snake_case vs. camelCase) | PENDING DECISION | Cross-language convention not decided |
| Endpoint naming convention | PENDING DECISION | Detailed endpoint paths not defined |
| Database physical schema | PROPOSED | Table/column names proposed but not decided |
| ID format strategy | TBD | UUID vs. ULID vs. other not decided |
| Timezone implementation | TBD | UTC vs. local vs. hybrid not decided |
| Exact trust formula | TBD | Formula for expected_kw, confidence, trusted_kw not defined |
| Exact confidence formula | TBD | Formula for confidence from evidence not defined |
| Optimization objective weights | PENDING DECISION | Category weights not finalized |
| Specific ML model | TBD | Statistical/ML approach not selected |
| Advanced grid model | TBD | Beyond feeder capacity simple limit |
| Production authentication | TBD | Not in MVP scope |
| Real IoT integration | TBD | Not in MVP scope |
| Production API versioning | TBD | Not in MVP scope |
| Pagination strategy | TBD | Not in MVP scope |
| WebSocket/real-time | TBD | Not in MVP scope |
| Machine-readable OpenAPI schema | TBD | Will be created in contracts/schemas/ |
| Event schema | TBD | Will be created in contracts/schemas/ |

---

## 10. Current Status

DRAFT
