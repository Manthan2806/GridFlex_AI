# DECISION LOG

## Purpose

Record major project decisions, their context, alternatives considered, evidence, trade-offs, consequences, and reversibility for GridFlex AI.

## Scope

This document is the authoritative source for major project decisions. Each decision records context, alternatives, evidence, trade-offs, consequences, and reversibility. It is not a generic diary. If an engineering discovery causes an architectural decision, the final decision belongs here and the implementation discovery remains in ENGINEERING_LOG.md.

## Authority

This document is the authoritative source for major project decisions. Other documents must not contradict decisions recorded here. Decisions marked PENDING must not be treated as decided.

## Current Status

DRAFT

---

## 1. Decision Template

Each decision follows this template:

## Decision N — <Title>

### Status

DECIDED | PENDING

### Decision

What was decided.

### Context

Why this decision was needed.

### Problem

What problem this decision solves or addresses.

### Alternatives Considered

What alternatives were evaluated.

### Evidence

What evidence supports this decision. No fabricated evidence.

### Trade-offs

What was gained and what was sacrificed.

### Consequences

What follows from this decision.

### Reversibility

Can this decision be reversed? How costly?

### Affected Components

Which components, documents, or teams are affected.

### Follow-up

What follow-up actions are needed.

---

## 2. DECIDED Decisions

### Decision 1: Simulation-First MVP

### Status

DECIDED

### Decision

The initial implementation must demonstrate the core trusted-flexibility loop without requiring real IoT hardware or real utility integration. MVP uses synthetic device-level behavior data and public/system-level energy data.

### Context

The project needs to validate the core loop and differentiation before investing in real infrastructure.

### Problem

Real IoT and utility integration would make the concept expensive to validate and slow to iterate on.

### Alternatives Considered

- Build against real hardware from the start.
- Build a production VPP from the start.

### Evidence

Research findings (RESEARCH.md) indicate the core loop and differentiation can be validated without real infrastructure; real integration is a later phase.

### Trade-offs

Faster validation of the concept; cannot demonstrate real-world performance initially.

### Consequences

MVP uses synthetic device-level flexibility and behavior data; real IoT and utility integration are deferred. No claim of production validation.

### Reversibility

Reversible — real integration can be added later as the architecture is modular.

### Affected Components

All teams; PROJECT.md (non-goals); DATA_SPEC.md (synthetic data rules); TESTING_STRATEGY.md (real-data validated vs. production validated).

### Follow-up

Determine when real-data validation is needed and how it will be conducted.

---

### Decision 2: Primary User is Utility / Demand-Response Aggregator

### Status

DECIDED

### Decision

The utility or demand-response aggregator is the primary user of GridFlex AI.

### Context

The product must have a clearly defined primary user to guide feature prioritization.

### Problem

Without a defined primary user, feature decisions lack a consistent priority framework.

### Alternatives Considered

- Consumer-focused load shifting.
- Commercial/industrial only.
- Generic.

### Evidence

Research findings and problem statement point to the aggregator/utility as the party that coordinates heterogeneous flexible loads at scale and bears the risk of under-delivery.

### Trade-offs

Narrows the feature set to aggregation/orchestration concerns rather than end-user consumer features.

### Consequences

Product features target aggregation, orchestration, and reliability reporting.

### Reversibility

Reversible — additional user segments can be added later.

### Affected Components

PROJECT.md, ARCHITECTURE.md, CONTRACTS.md, TEAM_WORK.md.

### Follow-up

No immediate action required; revisit if product direction changes.

---

### Decision 3: Modular Monolith Architecture

### Status

DECIDED

### Decision

The system will use a modular monolith architecture — a single deployable unit with internally separated modules, REST-first communication. No microservices in the initial implementation.

### Context

The system needs clear internal boundaries while remaining a single deployable unit initially.

### Problem

Microservices from the start would add complexity disproportionate to the MVP's needs.

### Alternatives Considered

- Microservices from the start.
- Monolith without internal module boundaries.

### Evidence

REST-first, modular monolith is appropriate for a simulation-first MVP with a small team (per DECISION_LOG original reasoning).

### Trade-offs

Less independent deployment granularity than microservices; requires discipline to maintain module boundaries.

### Consequences

Single deployable unit; internally separated modules; REST-first communication. Documented in ARCHITECTURE.md and PROJECT.md.

### Reversibility

Reversible — modules can be extracted into services later if justified.

### Affected Components

All teams; ARCHITECTURE.md (architecture style); PROJECT.md (non-goals: no microservices).

### Follow-up

No immediate action required; revisit if scaling requirements change.

---

### Decision 4: Use OR-Tools CP-SAT for MVP Optimization

### Status

DECIDED

### Decision

OR-Tools CP-SAT will be used for the MVP dispatch optimization.

### Context

The optimization problem involves discrete scheduling decisions with hard constraints and a multi-category objective.

### Problem

Need a solver that handles constraint-based scheduling with discrete variables and is available for Python.

### Alternatives Considered

- Custom heuristic solver.
- Linear programming.
- Other commercial solvers (Gurobi, CPLEX).

### Evidence

CP-SAT is well-suited to constraint-based scheduling with discrete variables and is available for Python. (Per RESEARCH.md section 16.)

### Trade-offs

CP-SAT is not ideal for all objective types and may have longer solve times on large instances; requires careful formulation.

### Consequences

Optimization depends on OR-Tools; formulation must be carefully designed.

### Reversibility

Reversible — solver can be swapped if formulation requirements change.

### Affected Components

Backend (orchestration), Optimization module, CONTRACTS.md (optimization interface).

### Follow-up

Determine specific CP-SAT formulation details during algorithm specification.

---

### Decision 5: Use React + TypeScript for Frontend

### Status

DECIDED

### Decision

React + TypeScript will be used for the frontend.

### Context

The frontend presents simulation configuration and results.

### Problem

Need a suitable technology for data-heavy operational dashboards.

### Alternatives Considered

- Other UI frameworks (Vue, Angular, Svelte).
- Plain HTML/JS.

### Evidence

React + TypeScript is a standard, well-supported choice for data-heavy operational dashboards.

### Trade-offs

Adds a frontend technology stack to maintain.

### Consequences

Frontend team owns React + TypeScript; backend owns the REST API contract.

### Reversibility

Reversible — frontend framework can be changed.

### Affected Components

Frontend team, CONTRACTS.md (API contracts), ARCHITECTURE.md (frontend boundary).

### Follow-up

No immediate action required.

---

### Decision 6: Use FastAPI/Python for Backend

### Status

DECIDED

### Decision

FastAPI with Python will be used for the backend.

### Context

The backend orchestrates simulation, optimization, and estimation.

### Problem

Need a web framework that supports REST APIs, validation, and async patterns suitable for simulation orchestration.

### Alternatives Considered

- Other Python web frameworks (Django, Flask).
- Non-Python backend (Node.js, Go, Java).

### Evidence

FastAPI provides strong support for REST APIs, validation, and async patterns suitable for simulation orchestration. Python is also used for simulation and AI/ML.

### Trade-offs

Ties the backend to Python, which is also used for simulation and AI/ML.

### Consequences

Backend, simulation, and AI/ML share a Python codebase.

### Reversibility

Reversible — backend framework or language can be changed, though cost is higher.

### Affected Components

Backend team, all Python-based components.

### Follow-up

No immediate action required.

---

### Decision 7: Do Not Use Unnecessary Microservices

### Status

DECIDED

### Decision

The initial architecture avoids microservices. A modular monolith is sufficient for the MVP.

### Context

The initial architecture should avoid premature distributed-system complexity.

### Problem

Microservices add operational and developmental complexity that is not warranted at MVP scale.

### Alternatives Considered

- Microservices from the start.

### Evidence

Modular monolith is sufficient for the MVP and allows later extraction (per DECISION_LOG #3).

### Trade-offs

Less independent deployment granularity.

### Consequences

Single deployable unit; module boundaries must be respected.

### Reversibility

Reversible — services can be extracted later.

### Affected Components

ARCHITECTURE.md, PROJECT.md (non-goals).

### Follow-up

No immediate action required; revisit if team or scale demands it.

---

### Decision 8: Do Not Make LLMs Part of the Core Control Loop

### Status

DECIDED

### Decision

LLMs will NOT be part of the core control loop. AI/ML scope is limited to statistical/ML confidence/reliability estimation and forecasting.

### Context

The control loop makes time-sensitive dispatch decisions based on computed trust and optimization.

### Problem

LLMs may be inappropriate for time-sensitive, deterministic control decisions.

### Alternatives Considered

- Use LLMs for decision support or control.

### Evidence

Research findings and engineering inference (RESEARCH.md sections 5, 16) indicate LLMs are not appropriate for the core control loop at this stage; statistical/ML approaches are preferred for reliability estimation.

### Trade-offs

Loses potential natural-language configurability or explanation capabilities.

### Consequences

AI/ML scope is limited to statistical/ML confidence/reliability estimation and forecasting.

### Reversibility

Reversible — LLM integration can be reconsidered if later research justifies it.

### Affected Components

AI/ML team scope, PROJECT.md (non-goals), RESEARCH.md (constraints).

### Follow-up

No immediate action required; revisit if LLM capabilities advance and are shown to be beneficial.

---

### Decision 9: 15-Minute Simulation Resolution

### Status

DECIDED

### Decision

The simulation operates on a 15-minute system time resolution for the MVP.

### Context

The simulation needs a time resolution appropriate for the target use cases.

### Problem

Finer resolution increases computational cost; coarser resolution may miss relevant events.

### Alternatives Considered

- 1-minute resolution (too fine for MVP resource types).
- 5-minute resolution (possibly excessive).
- 15-minute resolution (chosen).
- 30-minute or hourly resolution (too coarse for EV/water heater dynamics).

### Evidence

15-minute intervals are the standard settlement and metering interval; sufficient granularity for MVP resource types; balances fidelity with computational tractability.

### Trade-offs

Misses sub-15-minute events; acceptable for MVP resource types.

### Consequences

All time-indexed entities use 15-minute resolution; changes require documented decision.

### Reversibility

Reversible — resolution can be changed through an explicit documented decision.

### Affected Components

PROJECT.md, DATA_SPEC.md, ALGORITHM_SPEC.md, ARCHITECTURE.md, DOMAIN_MODEL.md.

### Follow-up

No immediate action required.

---

### Decision 11: Canonical Core Loop Ordering

### Status

DECIDED

### Decision

The canonical execution ordering of the core loop is:

```
Observe → Represent → Estimate → Trust → Match → Dispatch → Simulate → Verify → Learn
```

Dispatch (formulate/issue dispatch plan) precedes Simulate (simulate the proposed dispatch plan against simulated resource/system state). Verification follows simulation by comparing simulated actual response against the dispatch plan. Learning updates future estimates from verified outcomes.

### Context

Different documents previously described different orderings. PROJECT.md placed Simulate before Dispatch. ALGORITHM_SPEC.md and ARCHITECTURE.md placed Dispatch before Simulate.

### Problem

Four developers working independently need a single canonical ordering to prevent incompatible implementations.

### Alternatives Considered

- Simulate before Dispatch (ordering in original PROJECT.md)
- Dispatch before Simulate (ordering in ALGORITHM_SPEC.md and ARCHITECTURE.md)

### Evidence

Optimization produces a dispatch plan `x[i,t]`. Simulation simulates execution/response to a dispatch plan. Verification compares actual/simulated response against the dispatch plan. Learning uses verified outcomes. Simulation cannot test a plan that does not exist. A dispatch plan must be formulated before it can be simulated.

### Trade-offs

None — this is a logical semantic requirement, not a trade-off.

### Consequences

All documents now use the Dispatch-before-Simulate ordering consistently. No implementation can claim the other ordering.

### Reversibility

Reversible — the ordering can be changed through an explicit documented decision if system semantics change.

### Affected Components

PROJECT.md, ARCHITECTURE.md, ALGORITHM_SPEC.md, CONTRACTS.md, DOMAIN_MODEL.md, NAMING_AND_CONVENTIONS.md, README.md, EXPERIMENT_SPEC.md.

### Follow-up

No immediate action required; ordering is now authoritative.

---

### Decision 12: XYZ Role Resolved as Simulation, Experiments, and DevOps

### Status

DECIDED

### Decision

XYZ is resolved as: Simulation + Experiments + Validation, with necessary DevOps/tooling. This corresponds to the fourth implementation workstream: TEAM 4 — SIMULATION, EXPERIMENTS & DEVOPS ENGINEER.

### Context

TEAM_WORK.md previously listed XYZ as unresolved pending architecture and dependency analysis. The four-team structure is now defined and the role is clearly scoped.

### Problem

A fourth team role was undefined, preventing team parallelization.

### Alternatives Considered

- Leave XYZ unresolved (blocks parallelization)
- Assign XYZ to a different scope (inconsistent with task ownership)

### Evidence

Simulation engine, experiment framework, and validation infrastructure are distinct from frontend, backend, and AI/ML scope. These areas share dependencies (simulation uses dispatch contracts, experiments use optimization and simulation) that align with a single team.

### Trade-offs

This team carries the burden of running experiments and validating results in addition to DevOps tooling, which may require significant effort during experiment execution phases.

### Consequences

Team 4 owns simulation/, experiments/, scripts/, devops/, tests/validation/.

### Reversibility

Reversible — team scope can be reorganized if project needs change.

### Affected Components

TEAM_WORK.md, DECISION_LOG.md (PENDING decisions), project team structure.

### Follow-up

No immediate action required; team scope is now defined.

---

### Decision 10: Renewable Absorption as Primary Optimization Objective

### Status

DECIDED

### Decision

Renewable absorption is the primary optimization objective for the MVP. Market price optimization is not included.

### Context

The product focuses on renewable-aware demand orchestration.

### Problem

Multiple objective categories compete for priority; a primary objective must be established for MVP.

### Alternatives Considered

- Cost minimization as primary.
- Peak shaving as primary.
- Equal multi-objective weighting (not feasible for MVP).

### Evidence

Project context emphasizes renewable integration as the primary motivation.

### Trade-offs

Other objectives (comfort, cost, peak pressure) are secondary in the MVP.

### Consequences

Objective includes multiple categories per ALGORITHM_SPEC.md but renewable absorption is primary; tariff data is contextual only.

### Reversibility

Reversible — objective priority can change based on user feedback.

### Affected Components

ALGORITHM_SPEC.md, ARCHITECTURE.md, DATA_SPEC.md (tariff is contextual).

### Follow-up

Objective weights and exact formulation are TBD per ALGORITHM_SPEC.md.

---

## 3. PENDING Decisions

The following decisions are PENDING and must not be treated as decided:

| Decision | Description | Blocking |
|---|---|---|
| Final optimization objective weights | Exact weights between objective categories | Algorithm implementation |
| Exact trust computation formulas | How potential → expected → confidence → trusted | Trust computation implementation |
| Database schema details | Table structure, indexes, constraints | Backend implementation |
| Geographic scope of datasets | National vs. regional vs. Gujarat-specific | Data acquisition |
| Specific ML model for confidence estimation | Which statistical/ML approach to use | AI/ML implementation |
| Infeasibility fallback heuristic | What to do when optimization is infeasible | Algorithm implementation |
| Number of experimental runs | How many runs per scenario for statistical significance | Experiment execution |
| API JSON field naming convention | snake_case vs. camelCase | Frontend/Backend coordination |
| Timezone handling for timestamps | UTC vs. local vs. hybrid | Backend implementation |
| Opportunity detection thresholds | Criteria for identifying renewable-aligned windows | Algorithm implementation |
| Learning update rule | Specific mechanism for updating trust from verification | AI/ML implementation |
| Simulation Run State values | State model for simulation runs | Simulation engine design |

---

## 4. Current Status

DRAFT
