# Frontend Component Vocabulary

**Status**: LOCKED — COMPONENT VOCABULARY v1.0  
**Purpose**: Conceptual component hierarchy and shared/page boundaries for the GridFlex AI frontend MVP. Documentation only — no React components, pages, routes, dependencies, CSS, or implementation details.

> **Conceptual component ≠ implementation file.** A conceptual component in this document is a named responsibility boundary with a defined purpose, scope, and behavior contract. It does not dictate a file path, filename, TypeScript interface, props interface, or library. Multiple conceptual components may map to one implementation file or vice versa during implementation. The concrete file structure, naming, and technical realization are deferred to the implementation phase or FRONTEND_ARCHITECTURE.md.

---

## Guiding Constraints

- **Documentation only.** No component implementations, JSX, TypeScript props, libraries, styling, charting, routing, or state management.
- **Small and intentional.** Avoid generic dashboard/AI-slop components and component sprawl.
- **Product boundaries.** Only four MVP pages: Overview, Flexibility, Dispatch, Experiments.
- **Data boundaries.** Frontend displays contract-provided data; frontend must NOT calculate trust, confidence, flexibility, optimization, dispatch, simulation, verification, or learning.
- **Scenario selection.** Interaction remains deferred; do not prescribe a selector pattern.
- **Visual/interaction details.** Exact filenames, folders, TypeScript props, libraries, styling, and accessibility implementations remain deferred.

---

## Component Hierarchy

Application Shell
    ↓
Page Composition
    ↓
Feature Components
    ↓
Shared UI Components
    ↓
Primitive UI Elements

**Principle: REUSE WHERE MEANINGFUL**  
(not: REUSE EVERYTHING)

A component should exist when it has a clear product/design/interaction responsibility.

---

## Responsive Principles

1. Desktop — primary experience
2. Tablet — fully supported
3. Mobile — responsive and usable, but secondary

Do not create a separate mobile component system. Do not prescribe implementation details such as a hamburger menu unless that is later decided during interaction/architecture implementation.

---

## Shared Components (cross-page)

### App Shell
- **Purpose:** Provides the global layout structure containing navigation, scenario context, and simulation mode indicator.
- **Responsibility:** Maintains consistent frame across all pages; hosts primary navigation and global state indicators.
- **Used By:** All pages
- **Important States:** None (structural container)
- **What it must NOT do:** Must not contain page-specific content or calculate domain intelligence.

### Primary Navigation
- **Purpose:** Enables switching between the four MVP pages.
- **Responsibility:** Presents navigation items for Overview, Flexibility, Dispatch, and Experiments; indicates current page.
- **Used By:** App Shell
- **Important States:** Active page indicator
- **What it must NOT do:** Must not navigate to non-MVP pages or contain resource management controls.

### Page Header
- **Purpose:** Identifies the current page and displays scenario context.
- **Responsibility:** Shows page title and active scenario information where relevant.
- **Used By:** All pages
- **Important States:** Loading, Populated/Success, Empty, Error
- **What it must NOT do:** Must not display resource-specific data or optimization controls.

### Scenario Context
- **Purpose:** Displays the active scenario information (ID, time horizon, mode).
- **Responsibility:** Makes the current operational context visible to the operator.
- **Used By:** Page Header (Overview, Dispatch, Experiments pages)
- **Important States:** Loading, Populated/Success
- **What it must NOT do:** Must not allow scenario selection/editing (interaction deferred).

### Simulation Mode Indicator
- **Purpose:** Visibly indicates the system operates in simulation mode (not live utility integration).
- **Responsibility:** Provides persistent visual cue that actions are simulated/test, not physical device control.
- **Used By:** App Shell or Page Header (Dispatch page primarily)
- **Important States:** Active/Inactive
- **What it must NOT do:** Must not imply real-world device control or live grid interaction.

### Section Header
- **Purpose:** Labels distinct sections within a page.
- **Responsibility:** Provides clear visual separation and labeling for content groups.
- **Used By:** All pages (e.g., System Snapshot header, Renewable Opportunity header)
- **Important States:** None
- **What it must NOT do:** Must not contain interactive controls or display data values.

### Metric Display
- **Purpose:** Presents a single metric value with label and unit.
- **Responsibility:** Shows contract-provided values (e.g., trusted_kw, confidence) with appropriate formatting.
- **Used By:** All pages where metrics appear
- **Important States:** Loading, Populated/Success, Empty, Error
- **What it must NOT do:** Must not calculate values, invent metrics, or display frontend-derived domain intelligence.

### Status Indicator
- **Purpose:** Communicates operational state (e.g., resource availability, constraint status).
- **Responsibility:** Uses semantic labeling/color to indicate states like available/dispatched/completed/unavailable or constraint violations.
- **Used By:** Flexibility (Resource Row), Dispatch (Constraint Check), Experiments (Event Replay)
- **Important States:** Available, Dispatched, Completed, Unavailable, Constraint Violation, Normal
- **What it must NOT do:** Must not invent domain states or calculate trust/confidence.

### State Message
- **Purpose:** Displays contextual messages for loading, empty, error, and success conditions.
- **Responsibility:** Provides user-feedback for view states without implying missing features.
- **Used By:** All pages
- **Important States:** Loading, Empty, Error, Success
- **What it must NOT do:** Must not suggest unimplemented functionality or calculate domain values.

### Action/Button
- **Purpose:** Triggers user-initiated interactions.
- **Responsibility:** Presents actionable controls (primarily Simulate Dispatch on Dispatch page).
- **Used By:** Dispatch page (primary), other pages as needed for secondary actions
- **Important States:** Enabled, Disabled (during loading), Loading
- **What it must NOT do:** Must not expose solver internals, ML controls, optimization parameters, or physical device controls.

### Data Table
- **Purpose:** Presents structured tabular data for scanning and comparison.
- **Responsibility:** Displays resource portfolio data with consistent column alignment and visible units.
- **Used By:** Flexibility page (Resource Portfolio)
- **Important States:** Loading, Populated/Success, Empty, Error
- **What it must NOT do:** Must not hide trust values behind hover, convert to oversized cards, or contain add/edit/delete controls.

### Drawer
- **Purpose:** Presents detailed information in an overlay that preserves page context.
- **Responsibility:** Shows resource-level or experiment-level detail without losing the underlying list/table view.
- **Used By:** Flexibility (Resource Detail Drawer), Experiments (Event Replay detail)
- **Important States:** Open, Closed
- **What it must NOT do:** Must not become a full management screen or allow resource/trust editing.

---

## Overview Page Components

- **System Snapshot** — Aggregate key metrics (renewable opportunity, trusted flexibility, grid headroom)
- **Renewable Opportunity Summary** — Current/near-term renewable availability, forecast summary
- **Flexibility State Summary** — Aggregate flexibility picture (potential, expected, trusted, confidence)
- **Next Dispatch Summary** — Upcoming or most recent recommended dispatch summary
- **Recent Activity Summary** — Timeline of recent dispatches, simulations, verifications

These remain aggregate/system-level.

**Do NOT invent:**
- individual resource cards
- decorative dashboard widgets

---

## Flexibility Page Components

- **Portfolio Snapshot** — Aggregate portfolio metrics (resource count, potential, expected, trusted flexibility)
- **Resource Search** — Lightweight filtering controls (Type, Status, Location, Text search by ID)
- **Resource Portfolio/Table** — List/table of all resources with trust information
- **Resource Row** — Individual resource entry showing identity, potential, expected, trusted, confidence, availability/status, key constraint indicator
- **Resource Detail Drawer** — Per-resource detail showing status, potential, expected, trusted, confidence, constraints, compact response history, actual vs dispatched response, override occurrences
- **Constraint Indicator** — Visual indicator of key operational limits (deadline proximity, feeder capacity)
- **Response History** — Presentation/visualization of past dispatch events, actual vs dispatched, override occurrences

Resource-level information:
- identity
- type
- location
- potential
- expected
- trusted
- confidence
- availability/status
- key constraint indicator

**Do NOT create:**
- add resource
- delete resource
- edit trust
- edit confidence
- physical device pairing
- physical device control
- optimizer configuration
- ML configuration
- flexibility score trend display (explicitly prohibited)

---

## Dispatch Page Components

- **Renewable Opportunity Detail** — Detailed renewable availability for the decision window (forecast, uncertainty)
- **Relevant Flexibility** — Subset of portfolio relevant to this dispatch, showing potential/expected/trusted/confidence
- **Recommended Dispatch** — The dispatch plan (x[i,t]): selected resources, dispatched amounts per time step, total dispatched
- **Decision Rationale** — Why these resources, why these amounts (renewable opportunity, trusted flexibility, relevant constraints, reliability/trust influence)
- **Constraint Check** — Validation of hard constraints (power limits, energy requirements, deadlines, minimum duration, feeder capacity)
- **Simulation Action** — Primary action: Simulate Dispatch (triggers simulation against scenario)
- **Simulation Result** — Compact result of simulation (actual response, verification preview, constraint adherence)

Primary action: Simulate Dispatch (simulation/decision validation, NOT physical grid control)

**Do NOT create components requiring:**
- solver internals
- objective weights
- mathematical optimization details
- ML internals
- physical dispatch approval

---

## Experiments Page Components

- **Experiment Context** — Experiment ID, scenario category, seed, scheduler modes, time horizon
- **Experiment Summary** — High-level outcome (improvement / neutral / regression / inconclusive)
- **Baseline vs Trust-Aware Comparison** — Side-by-side comparison of dispatch plans, resource selection, timing
- **Outcome Metrics** — All primary and secondary metrics (flexibility delivery error, overcommitment, renewable absorption, etc.)
- **Delivery Visualization** — Time-series of dispatched vs. delivered for both schedulers
- **Event Replay** — Step-through of the core loop for a selected time window
- **Trust Update** — Effect of verification on future trust/reliability estimates

Comparison:
- Baseline = theoretical-capacity scheduling
- Trust-aware = trusted-flexibility scheduling

The frontend must remain neutral and support improvement, neutral, regression, inconclusive outcomes.

**Do NOT create:**
- custom experiment builder
- arbitrary experiment management controls
- UI that assumes Trust-aware wins

---

## Component States

Preserve the established states.

**General:**
- Loading
- Populated / Success
- Empty
- Error

**Dispatch:**
- Recommendation Ready
- Simulation Running
- Simulation Complete
- Simulation Failed

**Experiments:**
- Ready
- Running
- Completed
- Failed

Do not invent additional authoritative domain states.

---

## Component Data Boundary

Preserve this rule:

Components DISPLAY authoritative domain information.
Components do NOT OWN domain intelligence.

They must not calculate authoritative:
- trust
- confidence
- flexibility
- optimization
- dispatch
- simulation
- verification
- learning

Presentation transformations are allowed only when they preserve domain meaning.

---

## Component Composition Rules

Preserve these rules:

- Prefer composition over giant configurable components.
- Avoid dozens of boolean props.
- Avoid UniversalCard / SmartCard abstractions.
- Avoid generic components with no semantic responsibility.
- Keep feature-specific logic inside the feature.
- Extract shared components only when reuse is meaningful.
- Keep domain intelligence outside presentation components.
- Do not make every page section reusable automatically.

---

## Shared vs Page-Specific Inventory

### Shared / Shell
- App Shell
- Primary Navigation
- Page Header
- Scenario Context
- Simulation Mode Indicator
- Section Header
- Metric Display
- Status Indicator
- State Message
- Action/Button
- Data Table
- Drawer

### Overview
- System Snapshot
- Renewable Opportunity Summary
- Flexibility State Summary
- Next Dispatch Summary
- Recent Activity Summary

### Flexibility
- Portfolio Snapshot
- Resource Search
- Resource Filters
- Resource Portfolio/Table
- Resource Row
- Resource Detail Drawer
- Constraint Indicator
- Response History

### Dispatch
- Renewable Opportunity Detail
- Relevant Flexibility
- Recommended Dispatch
- Decision Rationale
- Constraint Check
- Simulation Action
- Simulation Result

### Experiments
- Experiment Context
- Experiment Summary
- Baseline vs Trust-Aware Comparison
- Outcome Metrics
- Delivery Visualization
- Event Replay
- Trust Update

These are conceptual component roles, NOT implementation files.
Some may later be combined during implementation if doing so preserves clear responsibility.

---

## Final Inventory Table

| Component | Scope | Responsibility | Used By | Key States | Notes |
|-----------|-------|----------------|---------|------------|-------|
| App Shell | Shared | Provides global layout structure containing navigation, scenario context, and simulation mode indicator | All pages | None (structural) | Hosts primary navigation and global state indicators |
| Primary Navigation | Shared | Enables switching between the four MVP pages | App Shell | Active page indicator | Presents navigation items for Overview, Flexibility, Dispatch, Experiments |
| Page Header | Shared | Identifies the current page and displays scenario context | All pages | Loading, Populated/Success, Empty, Error | Shows page title and active scenario information where relevant |
| Scenario Context | Shared | Displays active scenario information (ID, time horizon, mode) | Page Header (Overview, Dispatch, Experiments) | Loading, Populated/Success | Makes current operational context visible; interaction deferred |
| Simulation Mode Indicator | Shared | Visibly indicates system operates in simulation mode | App Shell or Page Header | Active/Inactive | Provides persistent visual cue that actions are simulated/test |
| Section Header | Shared | Labels distinct sections within a page | All pages | None | Provides clear visual separation and labeling for content groups |
| Metric Display | Shared | Presents single metric value with label and unit | All pages where metrics appear | Loading, Populated/Success, Empty, Error | Shows contract-provided values with appropriate formatting |
| Status Indicator | Shared | Communicates operational state (e.g., resource availability) | Flexibility, Dispatch, Experiments | Available, Dispatched, Completed, Unavailable, Constraint Violation, Normal | Uses semantic labeling/color to indicate states |
| State Message | Shared | Displays contextual messages for loading, empty, error, success | All pages | Loading, Empty, Error, Success | Provides user-feedback for view states without implying missing features |
| Action/Button | Shared | Triggers user-initiated interactions | Dispatch page (primary), others as needed | Enabled, Disabled (loading), Loading | Presents actionable controls (primarily Simulate Dispatch) |
| Data Table | Shared | Presents structured tabular data for scanning and comparison | Flexibility page (Resource Portfolio) | Loading, Populated/Success, Empty, Error | Displays resource portfolio data with consistent column alignment |
| Drawer | Shared | Presents detailed information in an overlay preserving page context | Flexibility (Resource Detail), Experiments (Event Replay) | Open, Closed | Shows resource/experiment detail without losing underlying list/view |
| System Snapshot | Overview | Aggregate key metrics (renewable opportunity, trusted flexibility, grid headroom) | Overview page | Loading, Populated/Success, Empty, Error | Shows system-level summary values |
| Renewable Opportunity Summary | Overview | Current/near-term renewable availability, forecast summary | Overview page | Loading, Populated/Success, Empty, Error | Renewable availability context for situational awareness |
| Flexibility State Summary | Overview | Aggregate flexibility picture (potential, expected, trusted, confidence) | Overview page | Loading, Populated/Success, Empty, Error | Aggregate flexibility state for quick assessment |
| Next Dispatch Summary | Overview | Upcoming or most recent recommended dispatch summary | Overview page | Loading, Populated/Success, Empty, Error | Summary of recent or upcoming dispatch |
| Recent Activity Summary | Overview | Timeline of recent dispatches, simulations, verifications | Overview page | Loading, Populated/Success, Empty, Error | Historical context of recent system actions |
| Portfolio Snapshot | Flexibility | Aggregate portfolio metrics (resource count, potential, expected, trusted) | Flexibility page | Loading, Populated/Success, Empty, Error | High-level portfolio statistics |
| Resource Search | Flexibility | Lightweight filtering controls (Type, Status, Location, Text search by ID) | Flexibility page | Loading, Populated/Success, Empty, Error | Enables filtering resource portfolio view |
| Resource Filters | Flexibility | Filter controls for resource portfolio (Type, Status, Location) | Flexibility page | Loading, Populated/Success, Empty, Error | Component of Resource Search functionality |
| Resource Portfolio/Table | Flexibility | List/table of all resources with trust information | Flexibility page | Loading, Populated/Success, Empty, Error | Main resource listing showing trust data |
| Resource Row | Flexibility | Individual resource entry showing identity, potential, expected, trusted, confidence, availability/status, constraint indicator | Flexibility page | Loading, Populated/Success, Empty, Error | Represents single resource in portfolio table |
| Resource Detail Drawer | Flexibility | Per-resource detail showing status, potential, expected, trusted, confidence, constraints, compact response history, actual vs dispatched, override occurrences | Flexibility page | Open, Closed | Detailed view triggered by Resource Row selection |
| Constraint Indicator | Flexibility | Visual indicator of key operational limits (deadline proximity, feeder capacity) | Flexibility page (Resource Row, Resource Detail) | Normal, Violation, Warning | Highlights critical operational constraints |
| Response History | Flexibility | Presentation/visualization of past dispatch events, actual vs dispatched, override occurrences | Flexibility page (Resource Detail Drawer) | Loading, Populated/Success, Empty, Error | Historical performance context for resource |
| Renewable Opportunity Detail | Dispatch | Detailed renewable availability for decision window (forecast, uncertainty) | Dispatch page | Loading, Populated/Success, Empty, Error | Specific renewable data for current dispatch decision |
| Relevant Flexibility | Dispatch | Subset of portfolio relevant to dispatch, showing potential/expected/trusted/confidence | Dispatch page | Loading, Populated/Success, Empty, Error | Resources applicable to current decision window |
| Recommended Dispatch | Dispatch | Dispatch plan (x[i,t]): selected resources, amounts per time step, total dispatched | Dispatch page | Loading, Populated/Success, Empty, Error | Backend-provided dispatch recommendation |
| Decision Rationale | Dispatch | Why these resources, amounts (renewable opportunity, trusted flexibility, constraints, trust influence) | Dispatch page | Loading, Populated/Success, Empty, Error | Contract-provided explanation only |
| Constraint Check | Dispatch | Validation of hard constraints (power limits, energy, deadlines, feeder capacity) | Dispatch page | Loading, Populated/Success, Empty, Error | Feasibility validation of recommended dispatch |
| Simulation Action | Dispatch | Primary action: Simulate Dispatch (triggers simulation against scenario) | Dispatch page | Enabled, Disabled (loading), Loading | Triggers simulation; NOT physical dispatch |
| Simulation Result | Dispatch | Compact simulation result (actual response, verification preview, constraint adherence) | Dispatch page | Loading, Populated/Success, Empty, Error | Outcome of Simulate Dispatch action |
| Experiment Context | Experiments | Experiment ID, scenario category, seed, scheduler modes, time horizon | Experiments page | Loading, Populated/Success, Empty, Error | Identifies and contextualizes the experiment |
| Experiment Summary | Experiments | High-level outcome (improvement / neutral / regression / inconclusive) | Experiments page | Loading, Populated/Success, Empty, Error | Top-line result of baseline vs trust-aware comparison |
| Baseline vs Trust-Aware Comparison | Experiments | Side-by-side comparison of dispatch plans, resource selection, timing | Experiments page | Loading, Populated/Success, Empty, Error | Structural comparison between scheduler approaches |
| Outcome Metrics | Experiments | All primary and secondary metrics (flexibility delivery error, overcommitment, renewable absorption, etc.) | Experiments page | Loading, Populated/Success, Empty, Error | Quantitative results of experiment comparison |
| Delivery Visualization | Experiments | Time-series of dispatched vs. delivered for both schedulers | Experiments page | Loading, Populated/Success, Empty, Error | Visual comparison of dispatch adherence |
| Event Replay | Experiments | Step-through of core loop for selected time window | Experiments page | Loading, Populated/Success, Empty, Error | Detailed verification of canonical loop stages |
| Trust Update | Experiments | Effect of verification on future trust/reliability estimates | Experiments page | Loading, Populated/Success, Empty, Error | Learning outcome presentation |

**Total conceptual components**: 39

---

## Deferred Decisions

- Exact filenames and folder structure
- TypeScript prop interfaces
- Tailwind/CSS class names or CSS-in-JS configs
- Charting library or raw SVG
- Routing mechanism
- State management library / custom hooks
- Testing framework or test utilities
- Breakpoint values and detailed layout
- Scenario-selection pattern
- Global scenario-selection interaction
- Experiment/event detail interaction pattern
- Exact loading skeleton/spinner/progress pattern
- Accessibility test setup

> All deferred decisions remain out of scope for this document. They will be resolved in implementation design, not in this vocabulary.

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-09-12 | Corrected component vocabulary per product spec review: removed Footer/ThemeToggle, fixed hierarchy, corrected responsive principles, defined proper component inventory, added missing component definitions | — |

(End of file)