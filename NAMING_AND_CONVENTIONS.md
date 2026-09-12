# NAMING AND CONVENTIONS

## Purpose

Define the canonical terminology, naming conventions, identifier conventions, field naming, API naming, database naming, language-specific conventions, and status terminology for GridFlex AI.

## Scope

This document is the authoritative source for all naming and terminology conventions. It prevents naming drift across independently developed components. Four developers working in parallel must consult this document before introducing any new domain term, field name, status, or interface concept.

## Authority

This document owns naming and terminology conventions. No other document may define alternative names for concepts owned here. Other documents reference this document for naming conventions; they do not redefine them.

## Current Status

DRAFT

---

## 1. Canonical Domain Vocabulary

Each concept has one canonical term. No two concepts may share a name. Terms from other documents must not be used as substitutes unless explicitly defined as distinct here.

### 1.1 Flexibility Concepts

| Concept | Canonical Term | Meaning | Do Not Confuse With | Authority |
|---|---|---|---|---|
| Theoretical Flexibility | Theoretical Flexibility | Maximum shiftable capacity implied by physical limits, ignoring reliability and constraints | Trusted Flexibility; Potential Capacity | DOMAIN_MODEL.md |
| Expected Flexibility | Expected Flexibility | Expected deliverable capacity given current evidence, including operational state, constraints, and uncertainty | Trusted Flexibility; Theoretical Flexibility | DOMAIN_MODEL.md |
| Trusted Flexibility | Trusted Flexibility | Confidence-weighted deliverable capacity used for dispatch decisions | Expected Flexibility; Theoretical Flexibility; Delivered Flexibility | DOMAIN_MODEL.md |
| Delivered Flexibility | Delivered Flexibility | Actual flexibility delivered as measured by verification (actual response vs. dispatched instruction) | Dispatched flexibility; Committed flexibility | DOMAIN_MODEL.md |
| Potential Capacity | Potential Capacity | Maximum deliverable capacity from physical limits (associated with `potential_kw` field) | Theoretical Flexibility (conceptually related but field-level vs. concept-level) | DOMAIN_MODEL.md, ALGORITHM_SPEC.md |

### 1.2 Core Entities

| Concept | Canonical Term | Meaning | Do Not Confuse With | Authority |
|---|---|---|---|---|
| FlexibilityResource | FlexibilityResource | A single coordinated flexible load with operational constraints and behavior history | Resource; Device; Asset; Load | DOMAIN_MODEL.md |
| Trust State | Trust State | A time-dependent computed state representing potential, expected, trusted capacity and confidence | Trust; Confidence; Reliability estimate | DOMAIN_MODEL.md, ALGORITHM_SPEC.md |
| Renewable Forecast | Renewable Forecast | Predicted renewable generation availability over time | Solar forecast; Generation forecast | ARCHITECTURE.md, DATA_SPEC.md |
| Opportunity | Opportunity | A renewable-aligned window where dispatching flexibility would absorb renewable energy or reduce peak pressure | Dispatch opportunity; Window; Slot | ARCHITECTURE.md, ALGORITHM_SPEC.md |
| Dispatch Plan | Dispatch Plan | A schedule of flexibility dispatch across resources and time steps (x[i,t]) | Schedule; Plan; Dispatch solution | ALGORITHM_SPEC.md, DOMAIN_MODEL.md |
| Dispatch Instruction | Dispatch Instruction | A specific dispatch command to a resource for a specific time | Instruction; Command; Signal | ARCHITECTURE.md |
| Actual Response | Actual Response | The real (simulated) flexibility delivered by a resource in response to a dispatch instruction | Delivered response; Realized flexibility | ARCHITECTURE.md |
| Verification | Verification | Comparison of actual response against dispatched instructions | Validation; Check; M&V | ARCHITECTURE.md |
| Learning | Learning | Process of updating trust estimation parameters based on verification outcomes | Model update; Trust update; Feedback | ALGORITHM_SPEC.md |
| Scenario | Scenario | A defined set of conditions (resources, forecasts, disruptions) under which a simulation runs | Simulation case; Test case; Configuration | ARCHITECTURE.md, EXPERIMENT_SPEC.md |
| Simulation Run | Simulation Run | A complete execution of the simulation engine for a scenario | Run; Execution; Simulation | ARCHITECTURE.md |
| Experiment Run | Experiment Run | A simulation run comparing baseline and trust-aware schedulers on equivalent scenarios | Evaluation run; Comparison run | EXPERIMENT_SPEC.md |
| Behavior Record | Behavior Record | Historical response data for a resource | History; Response history; Log | DOMAIN_MODEL.md, DATA_SPEC.md |

### 1.3 State Concepts

**Critical distinction: these are four different state concepts and must NOT be merged.**

| State Concept | Canonical States | Authority |
|---|---|---|
| Resource State | `available`, `dispatched`, `completed`, `unavailable` | DOMAIN_MODEL.md |
| Trust State | Time-dependent computed state (potential_kw, expected_kw, trusted_kw, confidence) | DOMAIN_MODEL.md, ALGORITHM_SPEC.md |
| Simulation Run State | TBD — requires simulation engine decision | TBD |
| Dispatch State | TBD — requires dispatch engine decision | TBD |

### 1.4 Flexibility Representation Pipeline

| Stage | Canonical Name | Input | Output | Authority |
|---|---|---|---|---|
| Observe | Observe | System clock, scenario config, forecasts | System state snapshot | ALGORITHM_SPEC.md |
| Represent | Represent | Resource data | Resource representations | ALGORITHM_SPEC.md, DOMAIN_MODEL.md |
| Estimate | Estimate | Resource representation + behavior + uncertainty | Confidence estimate | ALGORITHM_SPEC.md |
| Trust | Trust | Expected flexibility + confidence | Trust state | ALGORITHM_SPEC.md |
| Match | Match | Trust state + renewable forecast | Candidate opportunities | ALGORITHM_SPEC.md |
| Dispatch | Dispatch | Trusted flexibility + opportunity + constraints | Dispatch plan x[i,t] or infeasibility | ALGORITHM_SPEC.md |
| Simulate | Simulate | Scenario + dispatch plan | Actual response + system state | ARCHITECTURE.md |
| Verify | Verify | Dispatch plan + actual response | Verification result | ARCHITECTURE.md |
| Learn | Learn | Verification outcomes | Updated trust parameters | ALGORITHM_SPEC.md |

### 1.5 Flexibility Representation Pipeline

The canonical execution ordering is:

```
Observe → Represent → Estimate → Trust → Match → Dispatch → Simulate → Verify → Learn
```

This ordering is authoritative: Dispatch (formulate/issue dispatch plan) precedes Simulate (test the proposed dispatch plan against simulated resource/system state). Verification follows simulation by comparing simulated actual response against the dispatch plan. Learning updates future estimates from verified outcomes.

Decision variable: `x[i,t]` = amount of flexibility dispatched from resource i at time t.

---

## 2. Canonical Field Names

These field names are canonical. Do not rename them for aesthetic or convenience reasons. These are conceptual domain-level requirements, not finalized database columns (per DOMAIN_MODEL.md).

| Canonical Name | Meaning | Unit | Level | Authority |
|---|---|---|---|---|
| `id` | Unique identifier | N/A | Domain | DOMAIN_MODEL.md |
| `type` | Resource type: ev, water_heater, industrial_batch | enum | Domain | DOMAIN_MODEL.md |
| `location_id` | Geographic location identifier | string | Domain | DOMAIN_MODEL.md |
| `rated_power_kw` | Nameplate maximum power rating | kW | Domain | DOMAIN_MODEL.md |
| `earliest_start` | Earliest time flexibility can begin | timestamp | Domain | DOMAIN_MODEL.md |
| `latest_end` | Latest time flexibility must end | timestamp | Domain | DOMAIN_MODEL.md |
| `required_kwh` | Energy that must be delivered | kWh | Domain | DOMAIN_MODEL.md |
| `minimum_kwh` | Minimum energy delivery requirement | kWh | Domain | DOMAIN_MODEL.md |
| `maximum_kwh` | Maximum energy that can be delivered | kWh | Domain | DOMAIN_MODEL.md |
| `minimum_duration` | Minimum continuous operating duration | minutes | Domain | DOMAIN_MODEL.md |
| `maximum_duration` | Maximum continuous operating duration | minutes | Domain | DOMAIN_MODEL.md |
| `deadline` | Hard deadline by which energy must be delivered | timestamp | Domain | DOMAIN_MODEL.md |
| `min_power` | Minimum power while resource is operating | kW | Domain | DOMAIN_MODEL.md |
| `max_power` | Maximum power while resource is operating | kW | Domain | DOMAIN_MODEL.md |
| `historical_response` | Time series of past dispatch responses | data structure | Domain | DOMAIN_MODEL.md |
| `override_rate` | Fraction of dispatch instructions not fully complied with | float [0,1] | Domain | DOMAIN_MODEL.md |
| `availability_rate` | Fraction of time resource is available when requested | float [0,1] | Domain | DOMAIN_MODEL.md |
| `potential_kw` | Theoretical maximum deliverable capacity | kW | Domain/Computed | DOMAIN_MODEL.md, ALGORITHM_SPEC.md |
| `expected_kw` | Expected deliverable capacity given current evidence | kW | Domain/Computed | DOMAIN_MODEL.md, ALGORITHM_SPEC.md |
| `trusted_kw` | Confidence-weighted deliverable capacity for dispatch | kW | Domain/Computed | DOMAIN_MODEL.md, ALGORITHM_SPEC.md |
| `confidence` | Confidence level in the trust estimate | float [0,1] | Domain/Computed | DOMAIN_MODEL.md, ALGORITHM_SPEC.md |
| `x[i,t]` | Amount of flexibility dispatched from resource i at time t | kW | Algorithmic | ALGORITHM_SPEC.md |
| `feeder_capacity` | Maximum power flow capacity of distribution feeder | kW | Domain | DOMAIN_MODEL.md |

**Important:** These are conceptual requirements. The final database schema is a separate artifact derived from DOMAIN_MODEL.md during implementation. Do not treat this table as frozen schema.

### 2.1 Field Naming Drift Flagged for Correction

| Found In | Found Name | Canonical Name | Issue | Status |
|---|---|---|---|---|
| CONTRACTS.md line 168 | "Confidence score" | `confidence` | "Score" suffix not used elsewhere; canonical field is `confidence` | FIX REQUIRED: Change to confidence |

---

## 3. Python Naming Conventions

### 3.1 Variables

snake_case

Examples: `resource_id`, `trusted_kw`, `dispatch_plan`, `simulation_run`

### 3.2 Functions and Methods

snake_case

Examples: `estimate_trust()`, `simulate_dispatch()`, `get_resource_by_id()`

### 3.3 Modules and Packages

snake_case

Examples: `domain.models`, `services.optimization`, `engine.simulation`

### 3.4 Classes

PascalCase

Examples: `FlexibilityResource`, `TrustState`, `DispatchPlan`, `SimulationEngine`

### 3.5 Constants

UPPER_SNAKE_CASE

Examples: `DEFAULT_TIME_RESOLUTION_MINUTES = 15`, `MAX_RETRY_ATTEMPTS = 3`

### 3.6 Enums

PascalCase for enum class; UPPER_SNAKE_CASE for enum members

Examples:

```python
class ResourceState(str, Enum):
    AVAILABLE = "available"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    UNAVAILABLE = "unavailable"
```

### 3.7 Private Members

Prefix with single underscore: `_internal_method()`, `_private_attr`

### 3.8 Files

snake_case `.py`

Examples: `trust_computation.py`, `simulation_engine.py`, `optimization_solver.py`

### 3.9 Directories

snake_case

Examples: `backend/domain/`, `backend/services/`, `simulation/`

---

## 4. TypeScript Naming Conventions

### 4.1 Variables

camelCase

Examples: `resourceId`, `trustedKw`, `dispatchPlan`

### 4.2 Functions

camelCase

Examples: `estimateTrust()`, `getSimulationStatus()`

### 4.3 Types and Interfaces

PascalCase, suffix with `Type` or `Interface` if needed for clarity, or use `I` prefix (team preference)

Examples: `FlexibilityResource`, `TrustState`, `IDispatchPlan` (or `DispatchPlan`)

### 4.4 Classes (if used)

PascalCase

### 4.5 Enums

PascalCase for enum type; UPPER_SNAKE_CASE for members

Examples:

```typescript
enum ResourceState {
  AVAILABLE = "available",
  DISPATCHED = "dispatched",
  COMPLETED = "completed",
  UNAVAILABLE = "unavailable"
}
```

### 4.6 Constants

UPPER_SNAKE_CASE (or camelCase for module-level const where convention dictates)

### 4.7 React Components

PascalCase for component names and files

Examples: `ScenarioConfig.tsx`, `TrustVisualization.tsx`, `DispatchReview.tsx`

### 4.8 React Hooks

camelCase prefixed with `use`

Examples: `useScenario()`, `useSimulationStatus()`, `useTrustState()`

### 4.9 React Props

camelCase

Examples: `resourceId`, `onDispatchComplete`, `scenarioConfig`

### 4.10 React Event Handlers

camelCase, typically prefixed with `handle` or `on`

Examples: `handleScenarioSubmit()`, `onSimulationComplete()`

### 4.11 React State Variables

camelCase, typically with `is`, `has`, `can`, or descriptive prefix for `useState`

Examples: `isLoading`, `hasResults`, `selectedScenario`

### 4.12 Files

PascalCase `.tsx` for components; camelCase `.ts` for utilities, types, hooks

Examples: `ScenarioConfig.tsx`, `trustUtils.ts`, `simulationTypes.ts`

### 4.13 Directories

camelCase or kebab-case (team preference; pick one)

Examples: `frontend/src/components/`, `frontend/src/hooks/`, `frontend/src/types/`

---

## 5. API Naming Conventions

### 5.1 JSON Field Naming — PENDING DECISION

The JSON field naming convention for API request/response bodies has not been formally decided.

**PENDING DECISION:** Should API JSON fields use snake_case or camelCase?

**Recommended candidate:** snake_case

**Reasoning:**
1. Python/FastAPI backend uses snake_case natively
2. React/TypeScript can accept snake_case via configuration (e.g., `camelcase-keys` library)
3. Cross-language consistency is easier with a single convention
4. Contract readability is higher with explicit separators
5. Transformation overhead is lower when backend and database share convention
6. Long-term maintainability benefits from one canonical form (snake_case in NAMING_AND_CONVENTIONS.md)

**This must not be implemented until formally decided.**

### 5.2 Endpoint Naming — PENDING DECISION

Endpoint naming convention has not been formally decided. CONCRETE endpoints are defined in CONTRACTS.md.

**Recommended candidate:** kebab-case or snake_case path segments

Example (candidate, not final): `/v1/scenarios/{scenario_id}/simulations`

### 5.3 Path Parameters — PENDING DECISION

Convention for path parameter naming has not been formally decided.

**Recommended candidate:** snake_case matching field names

Example: `{resource_id}`, `{scenario_id}`, `{simulation_run_id}`

### 5.4 Query Parameters — PENDING DECISION

Convention for query parameter naming has not been formally decided.

**Recommended candidate:** snake_case

### 5.5 HTTP Status Semantics

Follow standard HTTP semantics as referenced in CONTRACTS.md:

| Status | Usage |
|---|---|
| 200 | Successful request |
| 206 | Partial success (e.g., results with low confidence) |
| 400 | Validation error |
| 404 | Not found |
| 409 | Conflict (e.g., incompatible resource state) |
| 422 | Unprocessable entity (e.g., infeasible dispatch, invalid domain input) |
| 500 | Internal server error |
| 504 | Gateway timeout (e.g., solver timeout) |

### 5.6 API Versioning — PENDING DECISION

Versioning convention has not been formally decided.

**Recommended candidate:** URL path prefix (e.g., `/v1/`)

### 5.7 Resource Naming in API

Use canonical entity names from NAMING_AND_CONVENTIONS.md section 1:

| Entity | API Path Segment | Authority |
|---|---|---|
| FlexibilityResource | `resources` | DOMAIN_MODEL.md |
| Scenario | `scenarios` | ARCHITECTURE.md |
| Simulation Run | `simulations` | ARCHITECTURE.md |
| Dispatch Plan | `dispatch` | ALGORITHM_SPEC.md |
| Trust State | `trust` | DOMAIN_MODEL.md |
| Experiment Run | `experiments` | EXPERIMENT_SPEC.md |

---

## 6. Database Naming — PROPOSED

The following PostgreSQL naming convention is PROPOSED. It has not been formally decided and requires a database schema decision.

### 6.1 Tables

snake_case, plural

Examples: `flexibility_resources`, `trust_states`, `dispatch_plans`, `simulation_runs`, `scenarios`, `verification_results`, `behavior_records`

### 6.2 Columns

snake_case

Examples: `resource_id`, `trusted_kw`, `confidence`, `earliest_start`, `latest_end`, `location_id`, `rated_power_kw`

### 6.3 Foreign Keys

snake_case, suffixed with `_id`

Examples: `location_id`, `scenario_id`, `resource_id`

### 6.4 Indexes

snake_case, prefixed with `idx_`

Examples: `idx_trust_state_resource_time`, `idx_dispatch_plan_scenario`

### 6.5 Constraints

snake_case, prefixed with `chk_` (check), `fk_` (foreign key), `uk_` (unique)

Examples: `chk_trust_ordering`, `fk_dispatch_plan_resource`

### 6.6 Timestamps

snake_case, suffixed with `_at` for point-in-time, `_period` for ranges

Examples: `created_at`, `updated_at`, `started_at`, `ended_at`, `observation_period`

### 6.7 Important Note

This is PROPOSED, not finalized. The actual database schema will be derived from DOMAIN_MODEL.md conceptual fields during implementation. Do not treat these as existing schema definitions.

---

## 7. ID Policy — TBD

### 7.1 ID Strategy — PENDING DECISION

The identifier strategy has not been formally decided.

**TBD — identifier strategy requires contract/database decision.**

### 7.2 ID Categories

| ID Type | Proposed Format | Status |
|---|---|---|
| Resource ID | string (UUID or ULID) | TBD |
| Scenario ID | string (UUID or ULID) | TBD |
| Simulation Run ID | string (UUID or ULID) | TBD |
| Experiment Run ID | string (UUID or ULID) | TBD |
| Dispatch ID | string (UUID or ULID) | TBD |
| Trust State ID | string (UUID or ULID) | TBD |
| Verification ID | string (UUID or ULID) | TBD |

**Critical requirement:** All ID fields must use a consistent format. Developers must not independently invent incompatible ID formats. The strategy must be decided before implementation begins.

---

## 8. Time and Timestamp Conventions

### 8.1 Time-Step Concept

The simulation operates on a **15-minute time step**. A time step is indexed by an integer or timestamp representing a 15-minute interval.

**Authority:** PROJECT.md, DATA_SPEC.md, ALGORITHM_SPEC.md

### 8.2 Timestamps

| Field | Canonical Name | Meaning | Format |
|---|---|---|---|
| Simulation time | `t` | Current 15-minute time step index | integer (1...T) or ISO 8601 timestamp |
| Scenario start | `scenario_start` | Start of simulation horizon | ISO 8601 timestamp |
| Scenario end | `scenario_end` | End of simulation horizon | ISO 8601 timestamp |

**Timezone handling — TBD:** The timezone for timestamps has not been formally decided. All timestamps should include timezone information. UTC is the recommended default for internal calculations but has not been formally decided.

### 8.3 Start/End Semantics

| Field | Semantics | Authority |
|---|---|---|
| `earliest_start` | Earliest time flexibility can begin (inclusive) | DOMAIN_MODEL.md |
| `latest_end` | Latest time flexibility must end (inclusive) | DOMAIN_MODEL.md |
| `deadline` | Hard deadline by which energy must be delivered | DOMAIN_MODEL.md |

### 8.4 Duration Semantics

Durations are in minutes unless otherwise specified.

| Field | Unit | Authority |
|---|---|---|
| `minimum_duration` | minutes | DOMAIN_MODEL.md |
| `maximum_duration` | minutes | DOMAIN_MODEL.md |

### 8.5 Time Conversion Factor

At 15-minute resolution, one time step = 0.25 hours. Energy calculations: `kWh = kW × 0.25` per time step.

**Authority:** ALGORITHM_SPEC.md (energy requirements constraint uses `0.25 = 15min in hours`)

### 8.6 Preventing Ambiguity

Developers must not interpret `earliest_start`, `latest_end`, and `deadline` differently across teams. These are domain-level semantics defined in DOMAIN_MODEL.md. Any change to their semantics must be documented in DOMAIN_MODEL.md.

---

## 9. Units

### 9.1 Canonical Units

| Quantity | Unit | Symbol | Context |
|---|---|---|---|
| Power | kilowatt | kW | Instantaneous/rate-like power quantity |
| Energy | kilowatt-hour | kWh | Energy quantity over time |
| Temperature | degrees Celsius | °C | Water heater, industrial process |
| State of Charge | percentage | % | EV batteries |
| Duration | minutes | min | Operating duration |
| Time | minutes or ISO 8601 | — | Time step resolution, timestamps |
| Confidence | fraction | 0.0 - 1.0 | Trust confidence level |
| Power flow | kilowatt | kW | Dispatch variable x[i,t], feeder capacity |

### 9.2 Unit Rules

1. **Internal calculations must not silently mix kW and kWh.** kW is a rate (power at an instant); kWh is an accumulation (energy over time). Mixing them produces incorrect results.

2. **kW = instantaneous/rate-like quantity.** Used for: power ratings, dispatch amounts, power limits, feeder capacity, x[i,t].

3. **kWh = energy quantity over time.** Used for: energy requirements, energy delivered, energy consumed.

4. **Duration is in minutes.** Used for: minimum_duration, maximum_duration, time step resolution.

5. **No arbitrary alternative units.** Do not introduce pounds, BTU, or other non-SI units unless explicitly required by domain context (none currently required).

### 9.3 Unit Documentation Rule

Every dataset, field, and API response must record units explicitly. Units must be consistent within a dataset.

**Authority:** DATA_SPEC.md

---

## 10. Boolean / Enum / Status Conventions

### 10.1 Boolean Naming Convention

Use `is_`, `has_`, or `can_` prefix for conceptual boolean fields (implementation-specific):

| Convention | Example | Context |
|---|---|---|
| `is_*` | `is_available`, `is_active` | General state |
| `has_*` | `has_override`, `has_failure` | Possession of a condition |
| `can_*` | `can_dispatch`, `can_shift` | Capability/permission |

### 10.2 Resource State — Canonical

| State | Meaning |
|---|---|
| `available` | Resource is available for dispatch |
| `dispatched` | Resource has been given a dispatch instruction |
| `completed` | Resource has fulfilled its dispatch |
| `unavailable` | Resource is not available (offline, full, etc.) |

**Do NOT use as synonyms:**
- `active` is NOT a substitute for `available` ("active" means operating/running, "available" means ready for dispatch)
- `done` is NOT a substitute for `completed`
- `offline` is NOT a substitute for `unavailable` (offline is one possible cause of unavailable; unavailable is the canonical state)
- `inactive` is NOT a substitute for any state

**Authority:** DOMAIN_MODEL.md

### 10.3 Trust State — Canonical

| Field | Meaning | Range |
|---|---|---|
| `potential_kw` | Theoretical maximum deliverable capacity | ≥ expected_kw |
| `expected_kw` | Expected deliverable capacity given evidence | ≥ trusted_kw; ≤ potential_kw |
| `trusted_kw` | Confidence-weighted deliverable for dispatch | ≤ expected_kw |
| `confidence` | Confidence level | [0.0, 1.0] |

**Invariant:** `trusted_kw` ≤ `expected_kw` ≤ `potential_kw`; `confidence` ∈ [0.0, 1.0]

**Authority:** DOMAIN_MODEL.md, ALGORITHM_SPEC.md, CONTRACTS.md

### 10.4 State Concept Separation

These are four distinct state concepts. Do not merge them:

| Concept | States | Authority |
|---|---|---|
| Resource State | available, dispatched, completed, unavailable | DOMAIN_MODEL.md |
| Trust State | Time-dependent: potential_kw, expected_kw, trusted_kw, confidence | DOMAIN_MODEL.md |
| Simulation Run State | TBD | TBD |
| Dispatch State | TBD | TBD |

### 10.5 Other Statuses — TBD

| Status Category | Canonical Values | Status |
|---|---|---|
| Simulation Run State | TBD | TBD |
| Dispatch State | TBD | TBD |
| Experiment Run State | TBD | TBD |
| Optimization Status | OPTIMAL, FEASIBLE, INFEASIBLE, TIMEOUT | PROPOSED (per CONTRACTS.md) |

---

## 11. Abbreviation Policy

Use abbreviations only when the full term is well-known and the abbreviated form is shorter and clearer. Do not randomly create abbreviations.

| Abbreviation | Full Term | Usage Context | Approved |
|---|---|---|---|
| AI | Artificial Intelligence | General technology context | Yes |
| ML | Machine Learning | General technology context | Yes |
| API | Application Programming Interface | Technical context | Yes |
| EV | Electric Vehicle | Resource type context | Yes |
| DR | Demand Response | Technical context | Yes |
| DER | Distributed Energy Resource | Technical context | Yes |
| VPP | Virtual Power Plant | Technical context | Yes |
| MVP | Minimum Viable Product | Project management context | Yes |
| SOC | State of Charge | EV battery context | Yes |
| M&V | Measurement and Verification | Regulatory context | Yes |
| IPMVP | International Performance Measurement and Verification Protocol | Regulatory context | Yes |
| SCADA | Supervisory Control and Data Acquisition | Industrial control context | Yes |
| OpenADR | Open Automated Demand Response | Protocol context | Yes |
| OCPP | Open Charge Point Protocol | EV charging context | Yes |
| CP-SAT | Constraint Programming SATisfier | Optimization solver context | Yes |
| REST | Representational State Transfer | Architecture context | Yes |
| DSO | Distribution System Operator | Grid context | Yes |
| TSO | Transmission System Operator | Grid context | Yes |

**Rule:** If an abbreviation is not obvious or established, prefer the full term. Do not introduce new abbreviations without documenting them here.

---

## 12. File and Folder Naming

### 12.1 Root Documentation Files

UPPER_SNAKE_CASE.md — preserve this convention for all authoritative root specification documents.

Examples: PROJECT.md, ARCHITECTURE.md, DOMAIN_MODEL.md, ALGORITHM_SPEC.md, DATA_SPEC.md, CONTRACTS.md, EXPERIMENT_SPEC.md, RESEARCH.md, DECISION_LOG.md, ENGINEERING_LOG.md, TEAM_WORK.md, TESTING_STRATEGY.md, README.md, NAMING_AND_CONVENTIONS.md

Do NOT rename existing documents.

### 12.2 Source Code Directories

Preserve the current project structure. Implementation directory naming will be refined during implementation.

### 12.3 Data Directory Structure

Preserve the existing data directory structure as documented in DATA_SPEC.md and data/README.md.

### 12.4 Contracts Directory

`contracts/schemas/` is reserved for machine-readable contract files (not yet created). `contracts/README.md` is the placeholder.

---

## 13. Document Status Terminology

### 13.1 Definitions

| Status | Definition | When to Use |
|---|---|---|
| **DRAFT** | Document is under active development or significantly incomplete. Content may change substantially. | Document has been expanded but decisions within it are not finalized. Most documents at this phase. |
| **PARTIALLY DEFINED** | Core structure and most content are established, but specific sections contain TBD items that require future decisions. | Key structure is defined but some critical details are unresolved (e.g., ALGORITHM_SPEC.md has formulas TBD). |
| **PROPOSED** | A specific proposal is made but not yet formally agreed upon by the relevant team(s). | Specific technical proposals (e.g., database naming, API conventions) awaiting decision. |
| **FROZEN** | Relevant decisions have been intentionally finalized. No further changes without a documented decision. | Only when the decisions within the document are explicitly agreed upon. |
| **SUPERSEDED** | A newer version of this document has replaced this one. Retained for historical reference. | A document has been replaced by an updated version. |

### 13.2 Important Rule

**A document is NOT FROZEN merely because it exists or has been written extensively.** A document is FROZEN only when the relevant decisions within it have been intentionally finalized by the appropriate team(s).

### 13.3 Current Document Statuses

| Document | Status |
|---|---|
| README.md | DRAFT |
| PROJECT.md | DRAFT |
| ARCHITECTURE.md | DRAFT |
| DOMAIN_MODEL.md | DRAFT |
| CONTRACTS.md | DRAFT |
| DATA_SPEC.md | DRAFT |
| ALGORITHM_SPEC.md | PARTIALLY DEFINED |
| EXPERIMENT_SPEC.md | DRAFT |
| RESEARCH.md | DRAFT |
| DECISION_LOG.md | DRAFT |
| ENGINEERING_LOG.md | DRAFT |
| TEAM_WORK.md | DRAFT |
| TESTING_STRATEGY.md | DRAFT |
| NAMING_AND_CONVENTIONS.md | DRAFT |

---

## 14. Authority and Cross-Reference Rule

### 14.1 Authoritative Document Ownership

Every concept has one authoritative owner:

| Document | Owns |
|---|---|
| PROJECT.md | Project identity, problem, MVP boundary, goals, success criteria |
| ARCHITECTURE.md | System boundaries, components, data/control flow, failure boundaries |
| DOMAIN_MODEL.md | Domain entities, invariants, flexibility concepts, resource lifecycle, field names |
| CONTRACTS.md | Interfaces, API contracts, model I/O, validation, error contracts |
| DATA_SPEC.md | Datasets, schemas, provenance, synthetic data rules, data quality |
| ALGORITHM_SPEC.md | Core algorithmic logic, optimization, trust calculation |
| EXPERIMENT_SPEC.md | Evaluation methodology, baseline vs. trust-aware, metrics, scenarios |
| RESEARCH.md | Research findings, evidence, landscape |
| DECISION_LOG.md | Major decisions and rationale |
| ENGINEERING_LOG.md | Implementation discoveries and failures |
| TEAM_WORK.md | Team structure, ownership, integration boundaries |
| TESTING_STRATEGY.md | Testing philosophy and validation layers |
| NAMING_AND_CONVENTIONS.md | Canonical terminology and naming conventions |
| README.md | Navigation only. Does NOT own project specifications. |

### 14.2 Cross-Reference Rule

If another document needs to mention a concept, **reference the authoritative document rather than redefining it.**

Example: If CONTRACTS.md needs to mention the trust invariant, it references DOMAIN_MODEL.md; it does not restate the full domain model.

### 14.3 Naming Convention Authority

If another document needs to name a field, endpoint, status, or entity, it should use the canonical name from this document (NAMING_AND_CONVENTIONS.md) or the authoritative document for that concept. It must not introduce alternative names.

---

## 15. Known Naming / Terminology Issues

### 15.1 Issues Fixed During Audit

| Issue | Found In | Fix Applied |
|---|---|---|
| "Confidence score" used instead of "confidence" | CONTRACTS.md line 168 | Corrected to "confidence" |
| Core Loop ordering conflict (Simulate before Dispatch vs. Dispatch before Simulate) | PROJECT.md, ARCHITECTURE.md, ALGORITHM_SPEC.md, NAMING_AND_CONVENTIONS.md | Resolved: Dispatch before Simulate is now the canonical ordering across all documents. See DECISION_LOG.md for the decision record. |

### 15.2 Unresolved Naming / Terminology Issues

| Term A | Term B | Why They May Conflict | Affected Documents | Recommended Resolution | Status |
|---|---|---|---|---|---|
| "Theoretical Flexibility" vs. "Potential Capacity" | Related but distinct | Both refer to maximum shiftable capacity; "Theoretical Flexibility" is a concept (PROJECT.md, DOMAIN_MODEL.md); "Potential Capacity" is a field-level concept (`potential_kw`) | PROJECT.md, DOMAIN_MODEL.md, ALGORITHM_SPEC.md, ARCHITECTURE.md, CONTRACTS.md | Determine if "Potential Capacity" is a synonym for "Theoretical Flexibility" or a distinct field-level concept. Currently treated as related but field-level vs. concept-level. | PROPOSED: Treat as related but distinct (concept vs. field) |
| API JSON field naming convention | snake_case vs. camelCase | Python/FastAPI uses snake_case; TypeScript/React uses camelCase by default | CONTRACTS.md (pending), all teams | Must be decided before API implementation. PENDING DECISION. | PENDING DECISION |
| Database table/column naming convention | TBD | Proposed snake_case but not formally decided | All teams | Must be decided before database implementation. PROPOSED, PENDING DECISION. | PROPOSED |
| ID format strategy | UUID vs. ULID vs. other | Not decided | All teams | Must be decided before implementation. TBD. | TBD |
| Timezone handling | UTC vs. local vs. hybrid | Not decided | DOMAIN_MODEL.md, DATA_SPEC.md, all teams | Must be decided before implementation. TBD. | TBD |
| Simulation Run State values | TBD | Not defined | TBD | Must be decided when simulation engine is designed. | TBD |
| Dispatch State values | TBD | Not defined | TBD | Must be decided when dispatch process is designed. | TBD |
| "resource type" vs "resource kind" vs "resource category" | — | No actual inconsistency found; "resource type" is canonical | Multiple documents | No action needed. | RESOLVED: "resource type" is canonical |

---

## 16. Terminology Cross-Reference Map

To prevent concepts from being redefined across documents, here is the cross-reference for key concepts:

| Concept | Canonical Definition In | Referenced In |
|---|---|---|
| Theoretical Flexibility | DOMAIN_MODEL.md | ALGORITHM_SPEC.md, ARCHITECTURE.md, PROJECT.md, EXPERIMENT_SPEC.md |
| Expected Flexibility | DOMAIN_MODEL.md | ALGORITHM_SPEC.md, ARCHITECTURE.md |
| Trusted Flexibility | DOMAIN_MODEL.md | ALGORITHM_SPEC.md, ARCHITECTURE.md, PROJECT.md, EXPERIMENT_SPEC.md, RESEARCH.md |
| Delivered Flexibility | DOMAIN_MODEL.md | ARCHITECTURE.md, EXPERIMENT_SPEC.md, ALGORITHM_SPEC.md |
| FlexibilityResource | DOMAIN_MODEL.md | All |
| Trust State | DOMAIN_MODEL.md | ALGORITHM_SPEC.md, ARCHITECTURE.md, CONTRACTS.md |
| potential_kw / expected_kw / trusted_kw / confidence | DOMAIN_MODEL.md, ALGORITHM_SPEC.md | ARCHITECTURE.md, CONTRACTS.md, PROJECT.md |
| x[i,t] | ALGORITHM_SPEC.md | ARCHITECTURE.md, DOMAIN_MODEL.md, CONTRACTS.md |
| Core Loop (stage names and ordering) | ALGORITHM_SPEC.md | ARCHITECTURE.md, PROJECT.md, README.md, EXPERIMENT_SPEC.md |
| 15-minute resolution | DATA_SPEC.md, PROJECT.md | ALGORITHM_SPEC.md, ARCHITECTURE.md, DOMAIN_MODEL.md, DECISION_LOG.md |
| Modular monolith | DECISION_LOG.md | ARCHITECTURE.md, PROJECT.md, README.md |
| REST-first | DECISION_LOG.md | ARCHITECTURE.md, PROJECT.md, TEAM_WORK.md |
| Simulation-first | DECISION_LOG.md | ARCHITECTURE.md, PROJECT.md, README.md |
| OR-Tools CP-SAT | DECISION_LOG.md | ARCHITECTURE.md, PROJECT.md |
| Resource States | DOMAIN_MODEL.md | ARCHITECTURE.md |
| Renewable Forecast | ARCHITECTURE.md | DATA_SPEC.md |
| Opportunity | ALGORITHM_SPEC.md | ARCHITECTURE.md |
| Scenario | ARCHITECTURE.md | EXPERIMENT_SPEC.md |
| Simulation Run | ARCHITECTURE.md | EXPERIMENT_SPEC.md |
| Experiment Run | EXPERIMENT_SPEC.md | ARCHITECTURE.md |

---

## 17. Current Status

DRAFT
