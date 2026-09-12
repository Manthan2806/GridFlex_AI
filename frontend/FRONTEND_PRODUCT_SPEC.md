# FRONTEND PRODUCT SPECIFICATION

## Purpose

Define the authoritative product/information specification for the GridFlex AI frontend. This document describes what the frontend is, who it is for, what problem it helps the user understand and act on, the core user journey, page inventory, information hierarchy, navigation, data boundary, MVP scope, and anti-scope-creep principles.

## Scope

This document is the single source of truth for frontend product decisions at the current phase. It does not contain visual design decisions (colors, typography, spacing, component styling, animations, aesthetic direction) nor technical architecture decisions (folder structure, state management, API client, routing library, package choices). Those belong to separate future phases.

## Authority

This document owns frontend product scope, page responsibilities, information hierarchy, navigation, data boundary, MVP boundary, and anti-scope-creep principles. Implementation documents (FRONTEND_ARCHITECTURE.md, component specs, visual design system) must not redefine product scope; they reference this document.

## Current Status

LOCKED

---

## A. FRONTEND PURPOSE

The GridFlex AI frontend is an **operational intelligence interface** for GridFlex AI.

**Primary user:** Utility / Demand-Response Aggregator operator.

The frontend is **not** primarily a consumer energy app. It does not target EV drivers, homeowners, or retail customers.

The frontend helps the operator understand and act on six core questions:

1. **What is happening?** — Current system state, renewable opportunity, flexibility availability.
2. **What flexibility exists?** — Portfolio of flexible resources and their capabilities.
3. **What flexibility can be trusted?** — Potential vs. expected vs. trusted flexibility with confidence.
4. **What should be dispatched?** — Recommended dispatch plan with rationale and constraints.
5. **Did the decision work?** — Verification of actual response vs. dispatched plan.
6. **What was learned?** — How verification updated trust/reliability for future decisions.

**Product experience:** An operational/decision-oriented interface, not a marketing dashboard. The interface prioritizes information density, clear hierarchy, and decision support over visual flair.

**Terminology rule:** Do not use "AI-powered" as a substitute for describing actual functionality. Features are described by what they do (trust computation, simulation, verification, learning), not by marketing labels.

---

## B. CORE PRODUCT STORY

The frontend visualizes the GridFlex AI core workflow:

```
Understand → Trust → Decide → Simulate → Verify → Learn
```

This maps to the project's canonical system loop (authoritative per ALGORITHM_SPEC.md, ARCHITECTURE.md, DOMAIN_MODEL.md, PROJECT.md):

```
Observe → Represent → Estimate → Trust → Match → Dispatch → Simulate → Verify → Learn
```

**Clarification:** The frontend visualizes this workflow; it does not own the underlying optimization, simulation, trust calculation, or learning logic. Those reside in the backend, AI/ML, optimization, and simulation subsystems. The frontend consumes contract-defined data and presents it for operator decision-making.

---

## C. INFORMATION HIERARCHY

The following priority hierarchy governs information presentation. Visual importance (prominence, placement, density) should follow this hierarchy.

### Tier 1 — Decision-Critical (Must be immediately visible/accessible)

- **Renewable opportunity** — Current and near-term renewable availability windows.
- **Trusted flexibility** — Confidence-weighted deliverable capacity (trusted_kw) per resource and aggregate.
- **Recommended dispatch** — The dispatch plan (x[i,t]) with selected resources, amounts, and time window.
- **Actual vs. committed response** — Delivered flexibility vs. dispatched flexibility, error, overcommitment.

### Tier 2 — Decision Context (Available on demand, supports Tier 1)

- **Potential flexibility** — Theoretical maximum (potential_kw).
- **Expected flexibility** — Evidence-adjusted deliverable (expected_kw).
- **Confidence** — Confidence level in trust estimate (0.0–1.0).
- **Constraints** — Operational limits (power, energy, duration, deadlines, feeder capacity).
- **Grid headroom** — Feeder capacity vs. current/planned dispatch.
- **Time window** — Dispatch validity window, deadlines, scenario horizon.

### Tier 3 — Supporting Information (Secondary views, detail drawers)

- **Resource history** — Past dispatch responses, override events, availability patterns.
- **Supporting metrics** — Renewable absorption, constraint violations, deadline violations, rebound.
- **Activity** — Recent dispatches, simulations, verification outcomes.

### Tier 4 — Metadata (Available on deep inspection only)

- **IDs** — resource_id, scenario_id, simulation_id, dispatch_id.
- **Timestamps** — Observation time, dispatch time, verification time.
- **Technical metadata** — Seeds, versions, solver status, raw optimization output.

---

## D. PAGE INVENTORY

The MVP contains **exactly four primary pages**. There are no additional primary pages in MVP v0.1.

| Page | Route (Conceptual) | Purpose |
|------|-------------------|---------|
| **Overview** | `/` or `/overview` | "What is happening right now?" — System-level snapshot. |
| **Flexibility** | `/flexibility` | "What flexible resources exist, and how trustworthy are they?" — Portfolio and resource-level trust. |
| **Dispatch** | `/dispatch` | "What should the system dispatch for this renewable opportunity?" — Decision, rationale, simulation. |
| **Experiments** | `/experiments` | "Did the trust-aware approach actually work?" — Baseline vs. trust-aware comparison, learning outcomes. |

---

## E. OVERVIEW PAGE

### Purpose

**"What is happening right now?"** — Aggregate/system-level context for rapid situational awareness.

### Sections

1. **Header / Scenario Context** — Active scenario, time horizon, simulation mode indicator.
2. **System Snapshot** — Aggregate key metrics (see below).
3. **Renewable Opportunity** — Current/near-term renewable availability, forecast summary.
4. **Flexibility State** — Aggregate flexibility picture (potential, expected, trusted, confidence).
5. **Next Dispatch** — Upcoming or most recent recommended dispatch summary.
6. **Recent Activity** — Timeline of recent dispatches, simulations, verifications.

### System Snapshot Focus

The System Snapshot section focuses on these aggregate values:

- **Renewable opportunity** — Total renewable energy available in the current/next window (kWh).
- **Trusted flexibility** — Sum of trusted_kw across available resources (kW), with confidence context.
- **Grid headroom** — Feeder capacity headroom (kW) at relevant locations.

> **Terminology note:** "Available flexibility" is not a separate flexibility metric. Availability is a resource status qualifier (available/dispatched/completed/unavailable). Trusted flexibility already represents the confidence-weighted deliverable capacity from available resources. Do not introduce "Available Flexibility" as an independent metric.

### What Overview Does NOT Contain

- Resource management (add/edit/delete resources).
- Detailed analytics or historical trends.
- Experiment configuration.
- Weather dashboard.
- Tariff dashboard.
- Maps / geographical visualization.
- Device controls.
- Optimizer configuration controls.
- ML/trust formula controls.

### System Status Representation

System status (simulation running, idle, error) may be represented through the global application shell/header rather than as a large standalone dashboard section.

---

## F. FLEXIBILITY PAGE

### Purpose

**"What flexible resources exist, and how trustworthy are they?"** — Full portfolio view with resource-level trust information.

### Sections

1. **Header** — Page title, scenario context, portfolio-level summary.
2. **Portfolio Snapshot** — Aggregate portfolio metrics.
3. **Search / Minimal Filters** — Lightweight filtering controls.
4. **Resource Portfolio** — List/table of all resources with trust information.
5. **Resource Detail Drawer** — Per-resource detail on click.

### Portfolio Snapshot

- **Resource count** — Total resources in portfolio.
- **Potential flexibility** — Sum of potential_kw (kW).
- **Expected flexibility** — Sum of expected_kw (kW).
- **Trusted flexibility** — Sum of trusted_kw (kW).

> **Confidence note:** Confidence is primarily a resource-level concept. Do not invent an "Average AI Confidence" or equivalent aggregate KPI as a required Portfolio Snapshot metric. Only describe an aggregate confidence representation if an authoritative backend contract explicitly provides one.

### Resource Portfolio (List/Table)

Each row shows:

- **Resource identity** — ID, type (ev / water_heater / industrial_batch), location_id.
- **Potential** — potential_kw (kW).
- **Expected** — expected_kw (kW).
- **Trusted** — trusted_kw (kW).
- **Confidence** — confidence (0.0–1.0).
- **Availability/Status** — Current resource state (available, dispatched, completed, unavailable).
- **Key constraint indicator** — e.g., deadline proximity, feeder limit.

### Minimal Filtering

- **Type** — Filter by resource type (ev, water_heater, industrial_batch).
- **Status** — Filter by resource state (available, dispatched, completed, unavailable).
- **Location** — Optional, only if justified by portfolio scale.

Simple text search by resource ID is allowed.

### Resource Detail Drawer

Clicking a resource opens a drawer (not a new page) showing:

- Current status.
- Potential / expected / trusted / confidence.
- Relevant constraints (deadline, power limits, energy requirements, feeder capacity).
- Compact response history — recent dispatch events, actual vs. dispatched, override occurrences.

### What the Frontend Must NOT Allow

- Adding resources.
- Editing resources.
- Deleting resources.
- Device pairing / IoT provisioning.
- Manual trust modification.
- Manual confidence modification.
- Dispatch optimization / solver configuration.
- Physical device control.

### Important Principle

**The frontend displays authoritative trust/confidence values returned by the system. It does not calculate or manually override them.** Trust is a time-dependent computed state derived from evidence each cycle (per DOMAIN_MODEL.md section 4.2).

---

## G. DISPATCH PAGE

### Purpose

**"What should the system dispatch for this renewable opportunity?"** — Decision support for the current dispatch window.

### Sections

1. **Header / Scenario Context** — Active scenario, time window, simulation mode.
2. **Renewable Opportunity** — Detailed renewable availability for the decision window (forecast, uncertainty).
3. **Relevant Flexibility** — Only resources relevant to this dispatch (subset of portfolio), showing potential / expected / trusted / confidence.
4. **Recommended Dispatch** — The dispatch plan (x[i,t]): selected resources, dispatched amounts per time step, total dispatched.
5. **Decision Rationale** — Why these resources, why these amounts (renewable opportunity, trusted flexibility, relevant constraints, reliability/trust influence where available).
6. **Constraint Check** — Validation of hard constraints (power limits, energy requirements, deadlines, minimum duration, feeder capacity).
7. **Simulation Result** — Compact result of "Simulate Dispatch" action.

### Primary MVP Action

**Simulate Dispatch** — Triggers simulation of the recommended dispatch plan against the scenario. Returns actual response, verification preview, and constraint adherence.

### What the Frontend Must NOT Imply

- GridFlex AI does **not** have real-world device control in MVP v0.1. The simulation action is a *test*, not a physical dispatch.
- No physical dispatch/approval workflow (no "confirm and send to devices").

### What the Frontend Must NOT Expose

- Solver configuration (CP-SAT parameters).
- Optimization objective weights.
- ML/trust formula settings.
- Raw optimizer output (dual values, solver logs).
- API configuration.
- Physical device controls.

### Scope Clarification

Dispatch shows **decision-level information** — only the flexibility relevant to the current decision and the resulting dispatch plan. It is not the full portfolio view (that is the Flexibility page).

---

## H. EXPERIMENTS PAGE

### Purpose

**"Did the trust-aware approach actually work?"** — Complete baseline vs. trust-aware analysis on equivalent scenarios.

### Primary Comparison

**Baseline** (theoretical-capacity scheduling) **vs.** **Trust-aware** (trusted-flexibility scheduling).

Both schedulers run on the **same underlying scenario/conditions** (identical resources, forecasts, disruptions, seeds). The only difference is the capacity input: potential_kw vs. trusted_kw.

### Sections

1. **Header / Experiment Context** — Experiment ID, scenario category, seed, scheduler modes, time horizon.
2. **Experiment Summary** — High-level outcome (improvement / neutral / regression / inconclusive per EXPERIMENT_SPEC.md interpretation rules).
3. **Baseline vs. Trust-Aware** — Side-by-side comparison of dispatch plans, resource selection, timing.
4. **Outcome Metrics** — All primary and secondary metrics (see below).
5. **Delivery Visualization** — Time-series of dispatched vs. delivered for both schedulers.
6. **Event Replay** — Step-through of the core loop for a selected time window.
7. **Trust Update** — Effect of verification on future trust/reliability estimates.

### Primary Metrics (per EXPERIMENT_SPEC.md)

- **Flexibility delivery error** — Dispatched vs. delivered (kWh).
- **Overcommitment** — Dispatch beyond reliable deliverable (kWh).
- **Renewable absorption** — Renewable energy aligned with dispatched flexibility (kWh).

### Secondary Metrics

- Constraint violations (count).
- Deadline violations (count).
- Rebound (kWh).
- Committed flexibility (total dispatched kWh).
- Actual flexibility (total delivered kWh).
- Actual/committed reliability (ratio).

### Critical Rules

- **Do NOT design the interface to automatically declare Trust-aware the winner.** The actual experiment result must determine the outcome. Neutral or regression results are valid and must be presentable.
- The interface must support the interpretation rules in EXPERIMENT_SPEC.md sections 14 and 19 (Improvement, Neutral, Regression, Inconclusive).

### Event Replay Representation

The event replay should represent the canonical loop stages:

```
Observe → Represent → Estimate → Trust → Match → Dispatch → Simulate → Verify → Learn
```

### Trust Update Visualization

The page may show how verification outcomes updated trust estimates (override rates, availability rates, confidence calibration) for affected resources.

### What the Frontend Must NOT Expose

- ML training controls / hyperparameters / model selection.
- Optimizer configuration.
- Raw solver logs.
- Dataset exploration.
- Engineering logs.
- Infrastructure monitoring.

---

## I. CROSS-PAGE INFORMATION RESPONSIBILITY

The following matrix defines where information belongs. This prevents duplication and ensures each page has a clear, non-overlapping responsibility.

| Information | Overview | Flexibility | Dispatch | Experiments |
|-------------|----------|-------------|----------|-------------|
| **Renewable opportunity** | Summary / context | — | Detailed decision input | Experiment/scenario context |
| **Potential flexibility** | Aggregate/system-level | Resource-level | Decision-level (relevant subset) | Before/after experimental analysis |
| **Expected flexibility** | Aggregate/system-level | Resource-level | Decision-level (relevant subset) | Before/after experimental analysis |
| **Trusted flexibility** | Aggregate/system-level | Resource-level | Decision-level (relevant subset) | Before/after experimental analysis |
| **Confidence** | Aggregate context | Current resource-level | Consumes system-supplied confidence for relevant resources; does not invent separate model | Trust/reliability changes after verification |
| **Constraints** | Aggregate headroom | Resource constraints | Dispatch feasibility / constraint validation | Constraint violation metrics |
| **Dispatch plan** | Next dispatch summary | — | Full recommended plan + rationale | Both schedulers' plans compared |
| **Simulation result** | Recent activity link | — | Compact immediate result | Complete analysis + event replay |
| **Verification result** | Recent activity link | Response history in drawer | Simulation preview | Full verification + trust update |
| **Learning outcome** | — | — | — | Trust/reliability parameter changes |

### Key Distinctions

- **Overview** → Aggregate/system-level context only.
- **Flexibility** → Full resource portfolio and resource-level trust information.
- **Dispatch** → Only flexibility relevant to the current decision and the resulting dispatch.
- **Experiments** → Complete baseline-vs-trust-aware analysis and learning outcome.

---

## J. NAVIGATION

### Primary Navigation

Exactly four items, matching the page inventory:

- **Overview**
- **Flexibility**
- **Dispatch**
- **Experiments**

No nested navigation is required for MVP.

### Detail Interactions

- **Resource detail** → Drawer (from Flexibility page).
- **Experiment/event detail** → Inline detail interaction or drawer (not a new primary page).
- **Scenario context** → Persists across relevant views (Overview, Dispatch, Experiments).

---

## K. GLOBAL FRONTEND REQUIREMENTS

MVP must support:

- **Application shell** — Layout, header, navigation, scenario context persistence.
- **Navigation** — Client-side routing between the four pages.
- **Routing** — Clean URLs for each page; deep-linkable.
- **Scenario context** — Active scenario clearly visible where relevant. **The exact global scenario-selection interaction is intentionally DEFERRED to the frontend interaction/architecture phase.** Do not assume a global selector, page-specific selector, dropdown, drawer, modal, or other interaction pattern.
- **Simulation-mode indication** — Clear visual indicator that the system is in simulation mode (not live utility integration).
- **Responsive behavior** — Desktop primary experience; tablet fully supported; mobile responsive and usable but secondary. Do not interpret this as requiring a separate mobile product.
- **Loading states** — For data fetching, simulation execution, experiment runs.
- **Empty states** — No resources, no scenarios, no results, no dispatch.
- **Error states** — API errors, simulation failures, validation errors, infeasible dispatch.
- **Success/completion states** — Simulation complete, experiment complete, dispatch simulated.

### Explicitly NOT in MVP

- Settings / preferences.
- Authentication / login.
- User profiles.
- Notification center / toast system (beyond inline error/success).
- Role management / permissions.
- Multi-user collaboration.

---

## L. DATA BOUNDARY

### Frontend Owns

- Presentation (how data is shown).
- User interaction (clicks, filters, navigation, simulation trigger).
- View state (selected resource, expanded drawer, active tab, filter values).
- Navigation / routing.
- Visualization (charts, tables, status indicators — logic for rendering, not the underlying computations).

### Frontend Does NOT Own (Authoritative)

- **Trust calculations** — potential_kw, expected_kw, trusted_kw, confidence computation.
- **Flexibility calculations** — Resource constraint normalization, energy/power feasibility.
- **Optimization** — Dispatch plan formulation and solving (x[i,t]).
- **Simulation logic** — Device behavior modeling, actual response generation, override/failure/rebound modeling.
- **Learning** — Trust parameter updates from verification.
- **Domain decision logic** — Any business rule that affects the authoritative state.

The frontend **consumes contract-defined data** (per CONTRACTS.md section 8.6 and DOMAIN_MODEL.md). It does not derive authoritative domain values.

---

## M. MOCK DATA STRATEGY

Frontend development initially uses contract-aligned mock/fixture data.

### Rules

1. **Mock data must follow project contracts** (CONTRACTS.md section 8.1 domain contract, section 8.6 backend→frontend shapes).
2. **Do not invent arbitrary frontend-only domain models.** Use the canonical fields from NAMING_AND_CONVENTIONS.md and DOMAIN_MODEL.md.
3. **Do not present mock values as live utility data.** Simulation mode must be clearly indicated.
4. **Simulation/mock scenarios must be identifiable** where necessary (e.g., scenario IDs, seed display).
5. **Mock data exists to enable frontend development before backend integration.**
6. **A frontend data/API adapter boundary should allow mock data to later be replaced by backend data without rewriting the UI.**

> The exact technical adapter implementation is deferred to FRONTEND_ARCHITECTURE.md. This document only establishes the principle.

---

## N. REQUIRED UI STATES

Pages and components must account for the following states. Visual styling of these states is deferred to the visual design phase.

### General States (All Pages)

- **Loading** — Data fetching, simulation running, experiment executing.
- **Populated / Success** — Data available, results rendered.
- **Empty** — No resources, no scenario selected, no results yet.
- **Error** — API failure, validation error, simulation failure, infeasible dispatch.

### Dispatch Page States

- **Recommendation ready** — Dispatch plan available for review.
- **Simulation running** — "Simulate Dispatch" triggered, waiting for result.
- **Simulation complete** — Result available (actual response, verification preview).
- **Simulation failed** — Error from simulation engine.

### Experiments Page States

- **Ready** — Configuration selected, ready to run.
- **Running** — Experiment execution in progress.
- **Completed** — Results available for comparison.
- **Failed** — Experiment execution error.

---

## O. FRONTEND MVP BOUNDARY

### MUST HAVE (MVP v0.1)

- Four-page workflow (Overview, Flexibility, Dispatch, Experiments).
- Scenario context persistence across pages.
- Portfolio view with potential/expected/trusted/confidence per resource.
- Resource detail drawer with constraints and compact history.
- Dispatch page with renewable opportunity, relevant flexibility, recommended dispatch (x[i,t]), rationale, constraint check.
- "Simulate Dispatch" action with compact result.
- Experiments page with baseline vs. trust-aware comparison, all primary/secondary metrics, delivery visualization, event replay, trust update.
- Application shell, navigation, routing, simulation-mode indicator.
- Loading, empty, error, success states per section N.
- Contract-aligned mock data strategy per section M.

### DEFERRED (Post-MVP, Requires Explicit Approval)

- Richer analytics / historical trend views.
- Additional visualizations (Sankey, geographic maps, correlation plots).
- Advanced historical filtering (date ranges, custom aggregations).
- Richer experiment controls (parameter sweeps, custom scenario builder).
- Additional scenario categories beyond the six defined in EXPERIMENT_SPEC.md.
- Real-time / WebSocket updates (currently REST polling only).
- Maps / geographical context.
- Authentication / roles / multi-user.
- Advanced resource management (enrollment UI, bulk import).
- Notification center / alerting.
- Export / reporting (PDF, CSV).
- Customizable dashboards / saved views.

### NOT ALLOWED WITHOUT EXPLICIT APPROVAL

- Arbitrary new pages beyond the four defined.
- Arbitrary dashboard widgets not tied to the core workflow.
- Chatbot / conversational UI.
- Gamification / rewards / leaderboards.
- Blockchain / marketplace UI.
- Physical IoT control / device provisioning.
- Fake real-time behavior (simulating live data when in simulation mode).
- Generic "AI features" without product justification (e.g., "AI summary" buttons).
- Decorative analytics (charts that don't answer a decision question).
- Features copied from generic SaaS dashboards without product justification in this document.

---

## P. ANTI-SCOPE-CREEP PRINCIPLES

The following principles prevent scope creep and AI-generated UI bloat. They are binding for MVP and future phases unless explicitly overridden by a documented product decision.

1. **The frontend MVP is the smallest interface capable of demonstrating the complete core workflow.** (Understand → Trust → Decide → Simulate → Verify → Learn)

2. **Every UI feature must have a defined product purpose.** No component exists "because it's nice to have" or "because dashboards usually have it."

3. **A component must not exist merely because it is common in dashboards.** (e.g., no generic "KPI cards row" unless each card answers a specific operator question.)

4. **A chart must answer a meaningful question.** No charts for decoration. Each visualization must map to a Tier 1 or Tier 2 information need.

5. **Metrics must have clear meaning and provenance.** Every number shown must trace to a canonical field (NAMING_AND_CONVENTIONS.md) or a contract-defined output (CONTRACTS.md).

6. **Do not invent domain calculations in the frontend.** No derived fields that are not in the contract. If a calculation is needed, it belongs in the backend/AI/ML and must be added to the contract.

7. **Do not create UI for capabilities the system does not actually provide.** If the backend doesn't compute it, the frontend doesn't show it.

8. **Do not imply live utility/device integration when operating in simulation mode.** The simulation-mode indicator must be persistent and clear.

9. **Do not add pages merely to separate information that can be handled with an existing page, drawer, or detail interaction.** The four-page structure is intentional and sufficient for MVP.

10. **New features require explicit product approval.** This document is the approval record for MVP. Post-MVP additions require a new decision recorded in DECISION_LOG.md and reflected in an updated version of this document.

---

## Q. CORE FRONTEND COMPLETION CRITERIA

The frontend MVP is considered **functionally complete** when the following journey works cleanly end-to-end:

```
Open application
→ Understand system state (Overview)
→ See renewable opportunity (Overview → Dispatch)
→ See flexibility portfolio (Flexibility)
→ Understand potential vs. expected vs. trusted (Flexibility → Dispatch)
→ Review dispatch recommendation (Dispatch)
→ Understand recommendation rationale (Dispatch)
→ Understand constraint validation (Dispatch)
→ Simulate dispatch (Dispatch → "Simulate Dispatch")
→ See simulation result (Dispatch)
→ Compare baseline vs. trust-aware (Experiments)
→ Inspect actual response vs. dispatched (Experiments → Delivery Visualization)
→ Inspect verification details (Experiments → Event Replay / Verification)
→ Inspect trust update / learning outcome (Experiments → Trust Update)
```

**Visual polish is NOT a prerequisite for MVP completion.** Functional correctness, contract conformance, and complete journey coverage are the criteria.

---

## CONTRADICTIONS & UNRESOLVED DECISIONS

### Contradictions Found During Authoring

| Area | Project Document | Frontend Spec Decision | Notes |
|------|------------------|------------------------|-------|
| Core loop ordering | PROJECT.md, ARCHITECTURE.md, ALGORITHM_SPEC.md all now agree: **Dispatch → Simulate** (per DECISION_LOG.md resolution) | Frontend spec uses Dispatch → Simulate ordering consistently | Resolved in NAMING_AND_CONVENTIONS.md section 15.1; no active contradiction. |
| "Potential Capacity" vs. "Theoretical Flexibility" | NAMING_AND_CONVENTIONS.md section 15.2: Treated as related but distinct (concept vs. field) | Frontend spec uses "Potential flexibility" (potential_kw) as the field-level term; "Theoretical Flexibility" as the concept | Consistent with NAMING_AND_CONVENTIONS.md proposed resolution. |
| API JSON naming (snake_case vs. camelCase) | NAMING_AND_CONVENTIONS.md section 5.1: PENDING DECISION | Frontend spec does not decide; defers to architecture phase | Unresolved — must be decided before API implementation. |
| Simulation Run State values | NAMING_AND_CONVENTIONS.md section 10.5: TBD | Frontend spec references "simulation running/complete/failed" as UI states | Unresolved — backend must define canonical states; frontend will adopt. |
| Dispatch State values | NAMING_AND_CONVENTIONS.md section 10.5: TBD | Frontend spec uses "Recommendation ready / Simulation running / Simulation complete / Simulation failed" | Unresolved — backend must define; frontend states are UI-facing approximations. |

### Explicitly Unresolved (Deferred to Later Phases)

1. **API JSON field naming convention** — snake_case vs. camelCase. (PENDING DECISION in NAMING_AND_CONVENTIONS.md.)
2. **Database schema / ID format / timezone handling** — Backend decisions; frontend will adopt. (TBD in NAMING_AND_CONVENTIONS.md.)
3. **Exact trust formulas** — AI/ML team ownership; frontend only displays outputs. (TBD in ALGORITHM_SPEC.md.)
4. **Optimization objective weights** — PENDING DECISION in CONTRACTS.md; affects dispatch rationale display.
5. **Specific ML model** — TBD in CONTRACTS.md; affects confidence interpretation.

> **Note:** Visual design system and technical architecture decisions have been finalized in FRONTEND_DESIGN_SYSTEM.md and FRONTEND_ARCHITECTURE.md respectively. They are no longer unresolved.

---

## FILES CONSULTED

The following authoritative project documents were read and used as the basis for this specification:

1. **README.md** — Project navigation, architecture summary, documentation map.
2. **PROJECT.md** — Project identity, problem, primary user, MVP scope, non-goals, success criteria, core loop, what GridFlex AI is not.
3. **ARCHITECTURE.md** — System boundaries, component responsibilities, data/control flow, frontend boundary, core decision loop, failure boundaries.
4. **DOMAIN_MODEL.md** — Domain entities, flexibility concepts (theoretical/expected/trusted/delivered), trust state, resource lifecycle, invariants, canonical field names.
5. **CONTRACTS.md** — Service boundaries, model I/O contracts, conceptual REST API surface, frozen contracts for parallel implementation (sections 8.1–8.7).
6. **DATA_SPEC.md** — Data categories, time resolution (15-min), geographic scope, units, leakage prevention, provenance.
7. **EXPERIMENT_SPEC.md** — Baseline vs. trust-aware methodology, scenario categories, metrics, comparison methodology, interpretation rules, reproducibility.
8. **TEAM_WORK.md** — Team 1 (Frontend) ownership, responsibilities, dependencies, must-not-redefine rules.
9. **DEPENDENCY_MAP.md** — Dependency graph, ownership matrix, independent work identification.
10. **NAMING_AND_CONVENTIONS.md** — Canonical terminology, field names, naming conventions, core loop ordering, state concepts, document status terminology, cross-reference map.

---

## DOCUMENT STATUS

LOCKED

---

*End of FRONTEND_PRODUCT_SPEC.md*