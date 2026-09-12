# GridFlex AI

## What GridFlex AI Is

GridFlex AI is a simulation-first flexibility intelligence and orchestration system for utilities and demand-response aggregators. It coordinates flexible electricity demand with renewable-energy availability by representing heterogeneous flexible loads using their actual operational constraints and estimating how reliably that flexibility can actually be delivered.

## Current Hackathon Prototype

The runnable prototype currently covers EV resources only. It connects a locked
Histogram Gradient Boosting estimate and conditional lower-bound model to a FastAPI
endpoint, creates a feeder-limited dispatch plan, and executes that plan in the
15-minute simulation engine. Candidate v2 passed its source-disjoint hybrid/synthetic
offline demo gate, but it is not approved for real deployment. The frontend,
production database, optimizer, water-heater model, and industrial-load model remain
planned work.

### Run the integrated demo

From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
uvicorn backend.app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/docs` and run `POST /simulate/full`. The backend loads the
locked v2 demo artifact rather than retraining during the request. Run the automated
checks with `pytest -q`.

## Core Concept

**Trusted Flexibility.** Theoretical flexibility says "this load can shift X kW." Trusted flexibility says "this load can *reliably* deliver Y kW at time t, given its operational constraints, historical response behavior, and current uncertainty." GridFlex AI converts optimistic capacity into a time-dependent, confidence-weighted trust state before dispatch, then verifies actual response and learns from it.

## Core System Loop

GridFlex AI follows a closed-loop process spanning observation, representation, estimation, trust evaluation, opportunity matching, dispatch, simulation, verification, and learning.

The canonical execution ordering is:

```
Observe → Represent → Estimate → Trust → Match → Dispatch → Simulate → Verify → Learn
```

Dispatch (formulate plan) precedes Simulate (test plan). Verification follows simulation. Learning updates future estimates from verified outcomes.

Stage names are canonical across all documents: Observe, Represent, Estimate, Trust, Match, Dispatch, Simulate, Verify, Learn.

For algorithmic details, see ALGORITHM_SPEC.md. For architecture context, see ARCHITECTURE.md.

## Architecture Summary

- **Architecture:** Modular monolith, REST-first. No microservices.
- **Frontend:** React + TypeScript (presentation, scenario config, results).
- **Backend:** Python + FastAPI (orchestration, REST API, simulation, dispatch).
- **Database:** PostgreSQL (persistence).
- **Optimization:** OR-Tools CP-SAT (dispatch solving).
- **Simulation:** Custom Python simulation engine (device behavior, scenarios).
- **AI/ML:** Statistical/ML-based flexibility confidence/reliability estimation.
- **Domain:** Central domain layer with FlexibilityResource, TrustState, Opportunity, DispatchPlan, etc.
- **Time Resolution:** 15 minutes (MVP).

See ARCHITECTURE.md for component boundaries, data flow, failure boundaries, and dependency direction.

## Technology Direction

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript |
| Backend | Python + FastAPI |
| Database | PostgreSQL |
| Optimization | OR-Tools CP-SAT |
| Simulation | Custom Python engine |
| AI/ML | Offline-demo-approved EV candidate v2 (not deployment-approved) |
| Time Resolution | 15 minutes (MVP) |

## Repository Structure

```text
GridFlex AI/
├── README.md
├── NAMING_AND_CONVENTIONS.md
├── DEPENDENCY_MAP.md
├── PROJECT.md
├── ARCHITECTURE.md
├── DOMAIN_MODEL.md
├── CONTRACTS.md
├── DATA_SPEC.md
├── ALGORITHM_SPEC.md
├── EXPERIMENT_SPEC.md
├── RESEARCH.md
├── DECISION_LOG.md
├── ENGINEERING_LOG.md
├── TEAM_WORK.md
├── TESTING_STRATEGY.md
├── docs/
│   ├── components/
│   └── decisions/
├── contracts/
│   ├── README.md
│   └── schemas/
├── backend/
├── frontend/
├── ai_ml/
├── devops/
├── data/
│   ├── raw/
│   │   ├── solar/
│   │   ├── weather/
│   │   ├── demand/
│   │   └── tariff/
│   ├── processed/
│   │   ├── solar_15min/
│   │   ├── demand_15min/
│   │   └── opportunities/
│   ├── synthetic/
│   │   ├── ev/
│   │   ├── water_heater/
│   │   ├── industrial/
│   │   ├── behavior/
│   │   └── scenarios/
│   └── README.md
├── experiments/
│   ├── baseline/
│   ├── trust_aware/
│   └── results/
├── scripts/
└── tests/
    ├── unit/
    ├── integration/
    ├── e2e/
    └── validation/
```

## Documentation Map

| Document | What It Owns | Authority |
|---|---|---|
| PROJECT.md | Project identity, problem, MVP boundary, goals | Authoritative |
| ARCHITECTURE.md | System boundaries, components, data/control flow | Authoritative |
| DOMAIN_MODEL.md | Domain entities, invariants, flexibility concepts | Authoritative |
| CONTRACTS.md | API contracts, interfaces, validation, error contracts | Authoritative |
| DATA_SPEC.md | Datasets, schemas, provenance, synthetic data rules | Authoritative |
| ALGORITHM_SPEC.md | Core algorithmic logic, optimization, trust calculation | Authoritative |
| EXPERIMENT_SPEC.md | Baseline vs. trust-aware comparison, metrics, scenarios | Authoritative |
| RESEARCH.md | Research findings, evidence, landscape | Authoritative |
| DECISION_LOG.md | Major decisions, context, trade-offs | Authoritative |
| ENGINEERING_LOG.md | Implementation discoveries and failures | Authoritative |
| TEAM_WORK.md | Team structure, ownership, integration boundaries | Authoritative |
| TESTING_STRATEGY.md | Testing philosophy and validation layers | Authoritative |
| NAMING_AND_CONVENTIONS.md | Canonical terminology and naming conventions | Authoritative |
| DEPENDENCY_MAP.md | Team ownership, dependencies, interfaces, coordination | Authoritative |

This README is a navigation document, not a source of truth. It does not own project specifications.

## Contribution / Documentation Rules

1. **Read the authoritative document** for the concept you are working with before making changes. Do not redefine concepts across documents. Reference instead.
2. **Before introducing a new domain term, field name, status, or interface concept, check NAMING_AND_CONVENTIONS.md and the authoritative document for that concept.**
3. **Classify claims** per the evidence system in RESEARCH.md: VERIFIED FACT, RESEARCH FINDING, ENGINEERING INFERENCE, ASSUMPTION, UNKNOWN, CONTESTED.
4. **Do not invent implementation details** in architecture documents. Those belong in ENGINEERING_LOG.md during implementation.
5. **Do not fabricate discoveries** in ENGINEERING_LOG.md. Only real entries.
6. **Do not treat conceptual domain fields as database schemas.** DOMAIN_MODEL.md fields are conceptual requirements.
7. **Do not claim production validation** without real deployment evidence. See TESTING_STRATEGY.md distinction.
8. **Mark document status** (DRAFT, PARTIALLY DEFINED, PROPOSED, FROZEN, SUPERSEDED) at the end of each document.
9. **Record PENDING decisions** in DECISION_LOG.md; do not convert TBD items to decisions.
10. **Use canonical terminology** from NAMING_AND_CONVENTIONS.md consistently across all documents.

## Pointer to PROJECT.md

For the current project status, success criteria, MVP scope, non-goals, and future possibilities, see PROJECT.md.

## Getting Started

### 1. Environment Setup
The project uses a standard Python virtual environment.
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Dependency Installation
Install the necessary runtime dependencies:
```bash
pip install -r requirements.txt
```
For development and testing, also install:
```bash
pip install -r requirements-dev.txt
```

### 3. Running Tests
The test suite ensures the integrity of the data pipeline, model integration, and optimization engine.
```bash
python -m pytest -q
```

### 4. Running the MVP Experiment
To run the end-to-end experiment demonstrating the tradeoff between baseline (potential_kw) and trust-aware (trusted_kw) dispatch:
```bash
python scripts/run_mvp_experiment.py
```
This script runs a paired deterministic simulation and outputs a comprehensive metric comparison. A structured JSON result is also saved to `experiments/output/mvp_experiment.json`.

It also runs a separate, clearly labelled seeded-disruption comparison. Synthetic
EV availability and user-override events are generated from the same seed,
resource ID and timestamp for both strategies, so the comparison is repeatable
and fair. This section is demonstration evidence, not real-world validation.

### 5. Demo Mode / EV Model Limitation
The MVP experiment uses Candidate v2 through `OfflineDemoEVModelClientV2(demo_mode=True)`. Candidate v2 passed its
declared independent offline holdout checks and has status **accepted_for_offline_demo**. It loads a saved, hash-checked
model artifact and does not retrain during a request.

Candidate v2 is suitable for the hackathon prototype, but real-world deployment remains disabled. Candidate v1 and
`ExperimentalEVModelClient` remain in the repository only for reproducibility and historical tests.

## Status

DRAFT
