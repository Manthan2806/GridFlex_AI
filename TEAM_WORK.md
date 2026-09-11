# TEAM WORK

## Purpose

Define team structure, ownership, workstreams, responsibilities, integration boundaries, and handoff requirements for GridFlex AI.

## Scope

This document is the authoritative source for team structure, ownership, workstreams, responsibilities, integration boundaries, and handoff requirements. It provides the minimum structure for four teammates to work independently after contracts are frozen.

## Authority

This document is the authoritative source for team structure, ownership, workstreams, responsibilities, integration boundaries, and handoff requirements. Other documents must not redefine team ownership.

## Current Status

DRAFT

---

## 1. Team Structure

Four implementation workstreams:

1. **TEAM 1 — FRONTEND** (Frontend Engineer)
2. **TEAM 2 — BACKEND & INTEGRATION** (Backend & Integration Engineer)
3. **TEAM 3 — AI/ML & INTELLIGENCE** (AI/ML & Intelligence Engineer)
4. **TEAM 4 — SIMULATION, EXPERIMENTS & DEVOPS** (Simulation, Experiments & DevOps Engineer)

XYZ is resolved as Simulation + Experiments + Validation, with necessary DevOps/tooling.

---

## 2. Team Ownership

### 2.1 TEAM 1 — FRONTEND

**Primary ownership:** `frontend/`

**Responsibilities:**

- React + TypeScript UI
- Scenario configuration
- Resource/flexibility views
- Dispatch visualization
- Simulation/experiment result visualization
- API integration
- User-facing states

**Dependencies:**

- Backend REST contracts (CONTRACTS.md section 8.6)
- Canonical domain vocabulary (NAMING_AND_CONVENTIONS.md)
- Result schemas

**Must not independently change:**

- Backend contracts
- Domain model
- AI/ML outputs
- Optimization formulation
- Simulation semantics

### 2.2 TEAM 2 — BACKEND & INTEGRATION

**Primary ownership:** `backend/`

**Responsibilities:**

- FastAPI
- REST API
- Validation
- Orchestration
- Persistence integration
- Coordination of AI/ML, optimization and simulation

**Dependencies:**

- Domain contract (CONTRACTS.md section 8.1)
- AI/ML contract (CONTRACTS.md section 8.2)
- Optimization contract (CONTRACTS.md section 8.3)
- Simulation contract (CONTRACTS.md section 8.4)
- Frontend API contract (CONTRACTS.md section 8.6)

**Must not independently redefine:**

- ML semantics
- Trust calculations
- Optimization formulation
- Simulation behavior

### 2.3 TEAM 3 — AI/ML & INTELLIGENCE

**Primary ownership:** `ai_ml/`

**Responsibilities:**

- Flexibility estimation
- Expected flexibility
- Trusted flexibility
- Confidence/reliability
- Learning/update logic
- Forecasting where required
- Model evaluation

**Dependencies:**

- Resource/domain contract (CONTRACTS.md section 8.1)
- Data specification (DATA_SPEC.md)
- Backend invocation contract (CONTRACTS.md section 8.2)

**Must not independently redefine:**

- Resource schema
- Backend API
- Optimization objective
- Simulation behavior

### 2.4 TEAM 4 — SIMULATION + EXPERIMENTS + DEVOPS

**Primary ownership:** `simulation/`, `experiments/`, `scripts/`, `devops/`, `tests/validation/`

**Responsibilities — Simulation:**

- Time-stepped simulation
- Synthetic resource behavior
- Scenario evolution
- Actual simulated response
- Failures
- Overrides
- Rebound
- Renewable/demand realization

**Responsibilities — Experiments:**

- Baseline
- Trust-aware
- Reproducibility
- Scenario execution
- Metrics
- Comparison

**Responsibilities — Validation:**

- Validation pipeline
- Experiment verification
- Realistic-data validation where applicable

**Responsibilities — DevOps/tooling:**

- Development environment consistency
- Necessary run/build tooling
- Deployment preparation only as needed

**Dependencies:**

- AI/ML contract (CONTRACTS.md section 8.2)
- Backend API (for orchestration)
- Domain vocabulary (NAMING_AND_CONVENTIONS.md)
- Optimization formulation (CONTRACTS.md section 8.3)
- Simulation contract inputs (CONTRACTS.md section 8.4)

**Must not independently redefine:**

- AI/ML contract
- Backend API
- Domain vocabulary
- Optimization semantics

---

## 3. Parallel Development Rules

1. Each teammate works primarily inside their owned directories.
2. Shared contract files are not casually modified.
3. A contract change requires coordination before dependent implementation changes.
4. Domain terminology must follow NAMING_AND_CONVENTIONS.md.
5. Do not duplicate business logic across teams.
6. Do not redefine another team's responsibility inside local code.
7. Team branches may diverge during implementation, but integration contracts remain common.
8. When a teammate discovers a required cross-team change, document the proposed change before implementing dependent changes.
9. Git operations are outside the scope of this documentation task; do not perform any Git commands.

---

## 4. Handoff Requirements

| Handoff | From | To | Condition |
|---|---|---|---|
| API contract conformance | Frontend | Backend | Before integration testing |
| Estimation interface conformance | Backend | AI/ML | Before trust computation integration |
| Dispatch formulation interface conformance | Backend | Optimization | Before optimization integration |
| Simulation interface conformance | Backend | Simulation | Before simulation integration |
| Schema and provenance conformance | All | Data | Per DATA_SPEC.md |
| Domain model conformance | Domain | All | Before dependent work begins |
| Model I/O conformance | AI/ML | Backend | Before end-to-end testing |

---

## 5. Current Task Assignments

No individual task assignments yet. Detailed implementation tasks will be created during the implementation phase.

---

## 6. Current Status

DRAFT
