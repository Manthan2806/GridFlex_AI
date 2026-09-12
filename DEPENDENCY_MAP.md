# DEPENDENCY MAP

## Purpose

Show who owns what, who depends on whom, which interfaces are shared, which work can happen independently, and where coordination is required.

## Scope

This is a lightweight dependency and ownership map. It supplements TEAM_WORK.md and CONTRACTS.md. It is not an architecture document.

## Current Status

DRAFT

---

## 1. Dependency Graph

```
FRONTEND (T1)
  depends on
BACKEND API (T2)

BACKEND (T2)
  depends on
DOMAIN CONTRACT (DOMAIN_MODEL.md + NAMING_AND_CONVENTIONS.md)
AI/ML CONTRACT (T3)
OPTIMIZATION CONTRACT (T2 module)
SIMULATION CONTRACT (T4)
DATABASE (T2)

AI/ML (T3)
  depends on
DOMAIN CONTRACT
DATA SPEC (DATA_SPEC.md)
BACKEND INVOCATION CONTRACT

SIMULATION (T4)
  depends on
DOMAIN CONTRACT
SCENARIO DATA (DATA_SPEC.md)
DISPATCH PLAN (from Optimization)

EXPERIMENTS (T4)
  depends on
SIMULATION (T4)
OPTIMIZATION (T2)
METRICS (EXPERIMENT_SPEC.md)

VALIDATION (T4)
  depends on
ALL
```

---

## 2. Ownership Matrix

| Area | Owner | Consumers |
|---|---|---|
| Frontend | T1 | User |
| Backend/API | T2 | T1 |
| Domain Contract | Shared (DOMAIN_MODEL.md) | T1, T2, T3, T4 |
| Intelligence/AI/ML | T3 | T2 |
| Optimization | T2 (subsystem) | T2, T4 |
| Simulation | T4 (subsystem) | T2, T4 |
| Experiments | T4 | T2, T3, T4 |
| Data/ML Datasets | T3 + T4 per DATA_SPEC | T3, T4 |
| Database Integration | T2 | T2 |
| Validation | T4 | All |
| Naming/Terminology | All (NAMING_AND_CONVENTIONS.md) | All |

---

## 3. Independent Work Identification

Can start immediately with frozen contracts:

| Team | Can Begin | Depends On |
|---|---|---|
| T1 (Frontend) | UI prototyping against mock responses | Backend API contract freeze |
| T2 (Backend) | Skeleton development | Domain contract + API contract freeze |
| T3 (AI/ML) | Model prototyping (if domain model stable) | Domain contract + DATA_SPEC freeze |
| T4 (Simulation) | Simulation engine prototyping | Domain contract + Scenario data freeze |

Cannot start until resolved:

| Item | Blocking |
|---|---|
| API JSON naming convention | T1 + T2 coordination |
| Database schema details | T2 |
| ID format strategy | T2 |
| Timezone handling | T2 |
| Exact trust formula | T3 |
| Specific ML model | T3 |
| Optimization weights | T2 |

---

## 4. Coordination Points

| Coordination | When | Between |
|---|---|---|
| API contract freeze | Before parallel implementation | T1 + T2 |
| Domain contract freeze | Before parallel implementation | All |
| Model I/O freeze | Before AI/ML integration | T2 + T3 |
| Simulation contract freeze | Before simulation integration | T2 + T4 |
| Experiment framework freeze | Before experiments | T4 |
| Cross-team change discovered | Before dependent implementation | Per Parallel Development Rules |

---

## 5. Notes

- Optimization is a subsystem, not a fifth teammate. Primarily owned/integrated by Team 2, with Team 4 responsible for experiment/validation use.
- Simulation is a subsystem, not a separate entity. Owned by Team 4.
- "Flexibility" as a concept is shared: it spans resource capability (domain), trust state (AI/ML), and dispatch constraints (optimization). The domain contract (CONTRACTS.md section 8.1) is the single source of truth.
- The DEPENDENCY_MAP.md intentionally stays short. Detailed architecture belongs in ARCHITECTURE.md. Detailed contracts belong in CONTRACTS.md.
