# ARCHITECTURE

## Purpose

Define the system boundaries, components, responsibilities, data flow, control flow, runtime flow, major dependencies, state transitions, failure boundaries, and architectural principles for GridFlex AI.

## Scope

This document covers the conceptual architecture of the system at the current phase. It describes boundaries and responsibilities, not implementation details. When another document needs a concept owned here, it references this document rather than redefining it.

## Authority

This document is the authoritative source for system boundaries, component responsibilities, data flow, control flow, runtime flow, major dependencies, state transitions, failure boundaries, and architectural principles. Implementation details that have not yet been decided must not be invented here.

## Current Status

DRAFT

---

## 1. Architecture Goals

1. **Represent heterogeneous flexibility** — support EV charging, water heaters, and industrial batch/process loads through a common representation.
2. **Compute trust, not just capacity** — produce time-dependent, confidence-weighted deliverable capacity.
3. **Simulate before dispatch** — verify dispatch outcomes in simulation before commitment.
4. **Close the loop** — verification outcomes feed learning to improve future estimates.
5. **Compare approaches** — enable baseline (theoretical) vs. trust-aware scheduling on identical scenarios.
6. **Maintain clear boundaries** — each component has a well-defined responsibility and non-responsibility.

## 2. Architecture Principles

1. **Trust is computed, not stored.** Trust is a time-dependent state derived from evidence each cycle (per DOMAIN_MODEL.md).
2. **Separation of representation from estimation.** Representing a resource's constraints is distinct from estimating how reliably it can deliver.
3. **Simulation before execution.** Dispatch plans are simulated before being considered committed.
4. **Verification closes the loop.** Actual response must be verified and used to update future estimates.
5. **No unverified claims.** Documents must classify statements as verified fact, research finding, engineering inference, assumption, unknown, or contested (per RESEARCH.md).
6. **Contract-first.** Interfaces are defined by contracts before implementation (per CONTRACTS.md).
7. **Modular monolith.** Single deployable unit with internally separated modules; no microservices (per DECISION_LOG.md).
8. **Simulation-first.** The system is designed around a simulation engine before any real execution path exists (per PROJECT.md).
9. **Information boundary.** The optimizer may see forecasts but must not receive actual future outcomes that would represent leakage (per DATA_SPEC.md).

## 3. System Boundary

GridFlex AI's system boundary encompasses:

- Resource representation and constraint modeling
- Flexibility estimation and trust computation
- Renewable opportunity detection and matching
- Dispatch optimization
- Simulation of device behavior and system conditions
- Verification of actual vs. dispatched flexibility
- Learning from verification outcomes
- REST API for frontend interaction
- Persistence of resources, scenarios, forecasts, dispatch plans, trust states, and results

**Outside the system boundary:**

- Real IoT device communication
- Real utility systems (SCADA, EMS, market interfaces)
- Actual grid power flow
- Customer-facing mobile apps
- Regulatory M&V protocols
- Multi-aggregator coordination

See PROJECT.md "WHAT GRIDFLEX AI IS NOT" for the complete exclusion list.

## 4. External Boundary

The system interacts with the following external entities:

| External Entity | Interaction | Channel |
|---|---|---|
| Frontend (React + TypeScript) | Receives scenario configs, sends simulation requests, displays results | REST API |
| Public/system energy data | Provides solar, weather, demand, tariff inputs | File import (data/raw/) |
| Synthetic data generator | Provides device-level flexibility and behavior data | File import (data/synthetic/) |
| OR-Tools CP-SAT | Receives formulated optimization problem, returns dispatch plan or infeasibility | Library invocation |

## 5. Internal Component Map

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                 │
│              (React + TypeScript)                               │
│  Scenario configuration · Result visualization · Dispatch review │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────────┐
│                        BACKEND                                  │
│                   (Python + FastAPI)                            │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Application Orchestration                   │    │
│  │   Scenario management · Loop orchestration · Result      │    │
│  │   aggregation · API routing                              │    │
│  └────────────────────────┬────────────────────────────────┘    │
│                           │                                     │
│  ┌────────────────────────▼────────────────────────────────┐    │
│  │                   Domain Layer                          │    │
│  │   FlexibilityResource · TrustState · Opportunity ·       │    │
│  │   DispatchPlan · Scenario                                │    │
│  └────────────────────────┬────────────────────────────────┘    │
│                           │                                     │
│  ┌────────────────────────▼────────────────────────────────┐    │
│  │              Domain Services                            │    │
│  │                                                         │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │    │
│  │  │ Flexibility   │  │ Trust        │  │ Opportunity   │  │    │
│  │  │ Representation│  │ Calculation  │  │ Detection     │  │    │
│  │  └──────────────┘  └──────────────┘  └───────────────┘  │    │
│  │                                                         │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │    │
│  │  │ Optimization  │  │ Simulation   │  │ Verification  │  │    │
│  │  │ (OR-Tools)    │  │ Engine       │  │               │  │    │
│  │  └──────────────┘  └──────────────┘  └───────────────┘  │    │
│  │                                                         │    │
│  │  ┌──────────────┐                                       │    │
│  │  │ Learning      │                                       │    │
│  │  └──────────────┘                                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                     │
│  ┌────────────────────────▼────────────────────────────────┐    │
│  │              Persistence (PostgreSQL)                    │    │
│  └─────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────-─┘
```

## 6. Component Responsibilities

### 6.1 Frontend (React + TypeScript)

**Owns:**
- Scenario configuration UI (resource definitions, forecast inputs, simulation parameters)
- Result visualization (trust states, dispatch plans, verification results, learning curves)
- Dispatch review interface
- Dashboard views of simulation outcomes

**Does NOT own:**
- Optimization or domain logic
- Trust computation
- Data generation
- Direct database access

### 6.2 Backend (Python + FastAPI)

**Owns:**
- REST API endpoints and request validation
- Scenario management (create, list, retrieve)
- Simulation orchestration (driving the time-stepped loop)
- Dispatch orchestration (triggering optimization, recording results)
- Application-level error handling
- Result aggregation and persistence coordination

**Does NOT own:**
- Domain model definitions (owned by DOMAIN_MODEL.md, implemented as shared domain code)
- Trust computation formulas (owned by AI/ML team, orchestrated by backend)
- Optimization formulation details (owned by optimization subsystem, integrated by Backend)
- Frontend presentation logic

### 6.3 Domain Layer

**Owns:**
- FlexibilityResource representation (constraints, state, behavior)
- TrustState representation (potential, expected, trusted, confidence)
- Opportunity representation
- DispatchPlan representation
- Scenario representation
- Core invariants (per DOMAIN_MODEL.md)

**Does NOT own:**
- How trust is computed (AI/ML concern)
- How optimization is solved (Optimization concern)
- How simulation proceeds (Simulation concern)
- How results are presented (Frontend concern)

### 6.4 AI/ML (Statistical/ML-based flexibility confidence/reliability estimation)

**Owns:**
- Flexibility estimation models
- Trust computation logic
- Forecasting models (where required)
- Learning/update logic from verification outcomes
- Model I/O definitions (per CONTRACTS.md)

**Does NOT own:**
- Optimization formulation
- Simulation engine
- Domain entity definitions (consumes them)
- REST API endpoints
- Database schema (depends on data per DATA_SPEC.md)

### 6.5 Optimization (OR-Tools CP-SAT)

**Owns:**
- Problem formulation (variables, constraints, objective) given inputs from backend
- Solver invocation and result parsing
- Dispatch plan output or infeasibility reporting

**Does NOT own:**
- Trust estimation (consumes trusted flexibility as input)
- Constraint extraction from resources (consumes domain model)
- Simulation (receives dispatch plan, does not simulate it)
- Objective weight decisions (TBD, requires decision)

### 6.6 Simulation (Custom Python simulation engine)

**Owns:**
- Time-stepped simulation of device behavior
- Scenario evolution (renewable availability, system conditions)
- Modeling of device response to dispatch (including overrides, failures, rebound)
- Production of actual outcomes for verification

**Does NOT own:**
- Trust computation (receives trust state as input)
- Optimization (receives dispatch plan as input)
- Domain model definitions (uses them but does not define them)
- Forecast generation (receives forecasts as input; must not receive actual future outcomes)

### 6.7 Persistence (PostgreSQL)

**Owns:**
- Durable storage of resources, scenarios, forecasts, dispatch plans, trust states, results
- Data retrieval for simulation runs and analysis

**Does NOT own:**
- Business logic
- Data transformation rules (orchestrated by backend/AI/ML)
- Trust computation

## 7. Component Non-Responsibilities

| Component | Explicitly NOT Responsible For |
|---|---|
| Frontend | Optimization, trust computation, data generation, direct database access, domain logic |
| Backend | Domain model definition, trust computation formulas, optimization formulation, presentation logic |
| Domain Layer | How trust is computed, how optimization is solved, how simulation proceeds, presentation |
| AI/ML | Optimization formulation, simulation engine, domain entity definitions, REST API, DB schema |
| Optimization | Trust estimation, constraint extraction, simulation, objective weight decisions (TBD) |
| Simulation | Trust computation, optimization, domain model definition, forecast generation |
| Persistence | Business logic, data transformation, trust computation |

## 8. Dependency Direction

Dependencies flow in one primary direction:

```
Frontend
    ↓ (REST API)
Backend/API
    ↓ (orchestration)
Application Orchestration
    ↓ (calls)
Domain Services
    ↓ (uses)
┌──────────────────────────────────┐
│ Domain Services                  │
│ ├── Flexibility Representation   │
│ ├── Trust Calculation ←── AI/ML  │
│ ├── Opportunity Detection        │
│ ├── Optimization ←── OR-Tools    │
│ ├── Simulation                   │
│ ├── Verification                 │
│ └── Learning                     │
└──────────────────────────────────┘
    ↓ (reads/writes)
Persistence / Experiment Outputs
```

Key dependency rules:

- Frontend depends on Backend (REST API contract in CONTRACTS.md).
- Backend depends on Domain (data structures), AI/ML (estimation/trust), Optimization (dispatch), Simulation (execution).
- AI/ML depends on Domain (resource representation), Data (training data per DATA_SPEC.md).
- Optimization depends on Backend (problem formulation), Domain (constraints).
- Simulation depends on Backend (orchestration), Domain (resource models), AI/ML (trust state inputs).
- Verification depends on Simulation (actual outcomes), Backend (dispatch plans).
- Learning depends on Verification (outcomes), AI/ML (update mechanism).
- Persistence is depended upon by all components; it depends on none.

## 9. Data Flow

Primary data flow through the system:

1. **Resource enrollment:** Resource data (constraints, type, location) → Domain model → Persistence.
2. **Behavior history:** Historical response data → AI/ML (estimation input).
3. **Estimation:** Resource representation + behavior history + current state + forecast uncertainty → AI/ML → confidence + trust state.
4. **Opportunity detection:** Renewable forecasts + system conditions → Opportunity Detection → candidate dispatch windows.
5. **Matching:** Trust state + opportunities → candidate dispatch problems.
6. **Optimization:** Trusted flexibility + opportunity + constraints + objective → Optimization → dispatch plan (x[i,t]) or infeasibility.
7. **Simulation:** Scenario + dispatch plan → Simulation Engine → actual response + system state + renewable conditions.
8. **Verification:** Dispatched plan + actual response → Verification → verification result.
9. **Learning:** Verification result → Learning → updated trust estimates.
10. **Result aggregation:** All outputs → Backend → Persistence → Frontend.

## 10. Control Flow

The control flow progresses through the core decision loop at each 15-minute time step:

```
Observe(t) → Represent(t) → Estimate(t) → Trust(t) → Match(t) → Dispatch(t) → Simulate(t) → Verify(t) → Learn(t)
```

This ordering is authoritative: Dispatch (formulate plan) must precede Simulate (test plan). Verification follows simulation. Learning updates future estimates from verified outcomes.

**Full loop stages:**

| Stage | Description | Document |
|---|---|---|
| Observe | Current conditions and forecasts | ALGORITHM_SPEC.md, ARCHITECTURE.md |
| Represent | Resource constraints and state | DOMAIN_MODEL.md |
| Estimate | Confidence-weighted deliverability | ALGORITHM_SPEC.md, AI/ML |
| Trust | Time-dependent trust state | ALGORITHM_SPEC.md |
| Match | Renewable-aligned opportunities | ALGORITHM_SPEC.md |
| Dispatch | Optimization → x[i,t] plan | ALGORITHM_SPEC.md |
| Simulate | Device response to dispatch plan | ARCHITECTURE.md, EXPERIMENT_SPEC.md |
| Verify | Actual vs. dispatched comparison | ARCHITECTURE.md |
| Learn | Update trust from verification | ALGORITHM_SPEC.md |

The core loop is consistently referred to across documents using the same stage names: Observe, Represent, Estimate, Trust, Match, Dispatch, Simulate, Verify, Learn.

## 11. Runtime Lifecycle

### 11.1 Simulation Run Lifecycle

1. **Initialization:** Backend receives scenario configuration from frontend.
2. **Setup:** Scenario, resources, and forecasts are loaded into the simulation engine.
3. **Time-stepping:** For each 15-minute step:
   a. Observe current conditions (renewable, demand, resource states).
   b. Represent resources using domain model.
   c. Estimate trust via AI/ML.
   d. Match trusted flexibility with opportunities.
   e. Solve optimization for dispatch plan.
   f. Simulate execution of plan (including overrides, failures, rebound).
   g. Verify actual vs. dispatched.
   h. Update trust via learning.
   i. Persist intermediate results.
4. **Finalization:** Aggregate results, persist final state, return to frontend.

### 11.2 Request Lifecycle (API)

1. Frontend sends request via REST API.
2. Backend validates request against contract (CONTRACTS.md).
3. Backend routes to appropriate service.
4. Service processes, coordinating with domain, AI/ML, optimization, simulation as needed.
5. Results are persisted and returned via REST response.

## 12. Core Decision Loop

The core decision loop is documented in detail in ALGORITHM_SPEC.md. Summary:

| Stage | Input | Processing | Output |
|---|---|---|---|
| Observe | System clock, scenario config | Read current conditions and forecasts | System state snapshot |
| Represent | Resource data | Apply domain model constraints | Resource representations |
| Estimate | Resource representation + behavior + uncertainty | Statistical/ML estimation | Confidence estimate |
| Trust | Expected flexibility + confidence | Time-dependent trust computation | potential_kw, expected_kw, trusted_kw, confidence |
| Match | Trust state + renewable forecast | Opportunity detection | Candidate dispatch windows |
| Simulate | Scenario + dispatch plan | Time-stepped device behavior simulation | Actual response, system state |
| Dispatch | Trusted flexibility + opportunity + constraints | OR-Tools CP-SAT optimization | Dispatch plan x[i,t] or infeasibility |
| Verify | Dispatch plan + actual response | Comparison | Verification result |
| Learn | Verification result | Trust update rule | Updated future trust estimates |

**Critical information boundary:** The optimizer may see forecasts. The optimizer must NOT receive actual future outcomes. The simulator reveals actual outcomes. Verification evaluates them. Learning updates future estimates. (Per DATA_SPEC.md.)

## 13. State Model

### 13.1 Resource State

A FlexibilityResource moves through states (per DOMAIN_MODEL.md):

```
available → dispatched → completed
available → unavailable
unavailable → available (when conditions permit)
```

### 13.2 Trust State

Trust is a time-dependent computed state with four conceptual fields:

- `potential_kw` — theoretical maximum deliverable capacity.
- `expected_kw` — expected deliverable capacity given current evidence.
- `trusted_kw` — confidence-weighted deliverable capacity used for dispatch decisions.
- `confidence` — confidence level in the trust estimate.

**Invariant:** trusted_kw ≤ expected_kw ≤ potential_kw.

### 13.3 Trust State Classification

| Category | Definition | Documented In |
|---|---|---|
| Theoretical Flexibility | Maximum shiftable capacity from physical limits | DOMAIN_MODEL.md, ALGORITHM_SPEC.md |
| Expected Flexibility | Expected deliverable capacity given evidence | DOMAIN_MODEL.md, ALGORITHM_SPEC.md |
| Trusted Flexibility | Confidence-weighted deliverable for dispatch | DOMAIN_MODEL.md, ALGORITHM_SPEC.md |
| Delivered Flexibility | Actual flexibility delivered per verification | DOMAIN_MODEL.md, EXPERIMENT_SPEC.md |

## 14. Failure Boundaries

| Failure | Boundary | Behavior |
|---|---|---|
| Optimization solver failure | Optimization → Backend | Fall back to deterministic heuristic or report infeasibility; do NOT silently degrade to theoretical capacity |
| Estimation failure | AI/ML → Backend | Flag low confidence rather than inventing trust; pass through with confidence = 0 or similar |
| Simulation divergence | Simulation → Backend | Record the divergence for learning; do NOT propagate unverified actuals into trust updates |
| Backend unavailability | Backend → Frontend | Frontend shows last-known state; no silent dispatch occurs |
| Data unavailability | Persistence → Backend | Use last-known good data; flag data quality issue |
| Invalid scenario configuration | Frontend → Backend | Reject with validation error before processing begins |
| Infeasible dispatch | Optimization → Backend | Report infeasibility with constraint analysis; do not force a solution |

### 14.1 Error Propagation Rules

- Errors in estimation propagate forward with a low-confidence flag; they do not halt the loop unless trust is entirely unavailable.
- Errors in optimization halt the dispatch step; the simulator runs the last known or null dispatch plan.
- Errors in simulation are recorded but do not halt the loop; verification flags the divergence.
- Errors in verification halt the learning step for that time step; trust is not updated from failed verification.

## 15. Persistence Boundary

PostgreSQL stores:

- Resource records (identity, type, constraints, behavior parameters)
- Scenario records (configuration, parameters, seeds)
- Forecast records (solar, weather, demand, tariff)
- Trust state records (per resource, per time step)
- Dispatch plan records (x[i,t] values, objectives, constraints)
- Simulation result records (actual response, system state)
- Verification result records (dispatched vs. actual)
- Experiment run records (metrics, configurations, provenance)

PostgreSQL does NOT store:

- Business logic
- Trust computation formulas
- Optimization model state (transient)
- Simulation engine state (transient during run)

## 16. Simulation Boundary

The simulation engine operates within these boundaries:

**Inside:**
- Device behavior modeling (EV, water heater, industrial)
- Scenario evolution (15-minute resolution)
- Renewable availability simulation
- Override, failure, and rebound modeling
- Production of actual outcomes for verification

**Outside:**
- Trust computation (input, not computed)
- Optimization (input: dispatch plan; not re-simulated)
- Forecast generation (input: forecasts; must NOT produce actual future outcomes)
- Grid power flow (not simulated)

## 17. AI/ML Boundary

**Inside the AI/ML boundary:**
- Flexibility estimation (potential → expected → trusted)
- Confidence computation
- Forecasting (renewable, demand — where required)
- Learning update rules (verification → future trust)

**Outside the AI/ML boundary:**
- Optimization formulation (consumes AI/ML output)
- Simulation engine (consumes trust state as input)
- Domain model definition (consumes domain entities)
- REST API (backend concern)

**Constraint:** No LLMs in the core control loop (per DECISION_LOG.md #8). AI/ML is statistical/ML-based.

## 18. Optimization Boundary

**Inside the Optimization boundary:**
- Problem formulation (variables, constraints, objective)
- CP-SAT solver invocation
- Solution parsing (dispatch plan or infeasibility)

**Outside:**
- Trust estimation (input only)
- Constraint extraction (input only)
- Simulation (does not simulate the plan)
- Objective weight decisions (TBD)

## 19. API Boundary

The API boundary is defined conceptually in CONTRACTS.md and will be formalized as machine-readable contracts. Summary:

- REST-first communication between Frontend and Backend.
- Backend orchestrates all internal component interactions.
- AI/ML, Optimization, and Simulation are invoked by Backend via internal interfaces.
- Persistence is accessed via Backend (not directly by other components).

See CONTRACTS.md for detailed contract definitions.

## 20. Frontend Boundary

**Inside:**
- React + TypeScript application
- Scenario configuration UI
- Result visualization (trust states, dispatch plans, verification results, learning curves)
- Dispatch review interface

**Outside:**
- Any domain logic
- Any optimization logic
- Any trust computation
- Direct data access (must go through Backend REST API)

## 21. Future Hardware / Integration Boundary

The following are explicitly outside the current architecture and would require architectural changes:

- Real IoT device communication (OCPP, OpenADR, Modbus)
- Real utility integration (SCADA, EMS, market interfaces)
- Distribution grid power flow simulation
- Multi-aggregator coordination
- Real-time communication with devices

These would require:
- New integration components (device adapters, utility gateways)
- Real-time communication infrastructure
- Distribution grid simulation modules
- Possibly microservice extraction for independent scaling

## 22. Scalability Considerations

| Concern | Current Approach | Future Consideration |
|---|---|---|
| Resource count | MVP scale (hundreds to low thousands) | Partition by location; potential service extraction |
| Simulation time | Single-threaded Python simulation engine | Parallel scenario execution if needed |
| Optimization scale | CP-SAT at MVP scale | Solver configuration tuning; possible solver swap if needed |
| Data volume | PostgreSQL; synthetic + public data | Partitioning; archival strategies for large simulations |
| Concurrent users | Single scenario at a time | Scenario queue; async result delivery |

**Currently not a concern:** Microservice extraction, distributed computation, horizontal scaling. The modular monolith is appropriate for MVP scale.

## 23. Security Boundary

| Boundary | Current Approach |
|---|---|
| Authentication | Not in MVP scope (simulation-first) |
| Authorization | Not in MVP scope |
| Data encryption | Standard PostgreSQL and HTTPS configurations |
| Input validation | Backend validates all inbound requests per CONTRACTS.md |
| Credential management | Environment variables; .env.example provides placeholders |
| API rate limiting | Not in MVP scope |

Security is not a primary concern at the simulation-first MVP stage but must be considered for future real-utility integration phases.

## 24. Observability Boundary

| Concern | Current Approach |
|---|---|
| Logging | Structured logging in Backend and Simulation; sufficient for MVP |
| Metrics | Simulation output metrics per EXPERIMENT_SPEC.md; no custom metrics pipeline in MVP |
| Tracing | Not in MVP scope |
| Alerting | Not in MVP scope |
| Debugging | Simulation output analysis; trust state visualization in Frontend |

## 25. Architectural Trade-offs

| Trade-off | Decision | Rationale | Consequence |
|---|---|---|---|
| Modular monolith vs. microservices | Modular monolith | Appropriate for MVP with small team; reversible | Single deployable; module discipline required |
| REST-first vs. event-driven | REST-first | Simpler for MVP; synchronous flow is sufficient for simulation | Event-driven deferred to future if needed |
| Simulation-first vs. real integration | Simulation-first | Validates core loop without hardware; reversible | Cannot demonstrate real-world performance |
| CP-SAT vs. other solvers | CP-SAT | Good for constraint-based scheduling with discrete variables | Solver-specific formulation; may need tuning |
| Python everywhere (backend, sim, ML) | Single language | Reduces context switching; shared ecosystem | Python GIL may limit concurrency; acceptable for MVP |
| PostgreSQL vs. other DBs | PostgreSQL | Standard relational DB; sufficient for MVP data model | May need scaling later; acceptable for MVP |
| 15-minute vs. finer resolution | 15-minute | Sufficient for MVP use cases; reduces computational load | Sub-15-minute events may be missed; change requires documented decision |

## 26. Deferred Architectural Options

The following architectural options are explicitly deferred and NOT part of the current architecture:

- Microservice extraction (explicitly per DECISION_LOG.md and PROJECT.md)
- Event-driven communication (REST-first per DECISION_LOG.md)
- Real-time device communication (non-goal per PROJECT.md)
- Distribution grid simulation (non-goal per PROJECT.md)
- Multi-aggregator coordination (non-goal per PROJECT.md)
- Reinforcement learning for core dispatch (non-goal per PROJECT.md)
- Customer-facing apps (non-goal per PROJECT.md)

## 27. Conceptual vs. Implementation Architecture

This document describes the **conceptual architecture** — boundaries, responsibilities, and flows. The **implementation structure** (package layout, class names, API endpoint paths, database table names) will be determined during implementation and documented in ENGINEERING_LOG.md as discoveries are made.

The conceptual architecture will remain stable while implementation details may evolve. For example:
- The Backend may be organized as a FastAPI application with routers, services, and domain modules.
- The Simulation Engine may be a Python class hierarchy or a procedural engine.
- The Domain Layer may be implemented as Python dataclasses or Pydantic models.

The boundaries and responsibilities documented here must remain stable regardless of implementation choices.

## 28. Current Status

DRAFT
