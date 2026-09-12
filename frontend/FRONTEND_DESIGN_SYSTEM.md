# FRONTEND DESIGN SYSTEM

## Purpose

Define the visual, layout, interaction, and presentation rules for the GridFlex AI frontend.

This document translates the locked frontend product specification into design-system guidance. It does not redefine product scope, data ownership, backend contracts, routes, technical architecture, component implementation, or package choices.

## Scope

This document covers:

- Operational visual principles.
- Information density and hierarchy.
- Semantic typography roles.
- Semantic color roles.
- Surfaces, panels, tables, drawers, controls, and status representation.
- Data visualization principles for operational decision support.
- Metric presentation rules.
- Responsive and accessibility principles.
- Anti-AI-slop visual rules.

This document does not create React components, pages, routes, source folders, CSS files, Tailwind configuration, or implementation architecture.

## Authority

FRONTEND_PRODUCT_SPEC.md remains authoritative for frontend product scope, page responsibilities, information hierarchy, navigation, MVP boundary, and data boundary.

NAMING_AND_CONVENTIONS.md remains authoritative for canonical terminology, field names, units, status naming, and naming drift prevention.

CONTRACTS.md remains authoritative for backend-to-frontend data shapes and contract boundaries.

This document owns frontend presentation rules only.

## Current Status

LOCKED — VISUAL DESIGN SYSTEM v1.0

This document is now the finalized visual identity for MVP implementation. Future changes to the visual identity require an explicit design decision.

---

## 1. Design Intent

GridFlex AI is an operational intelligence interface for a Utility / Demand-Response Aggregator operator.

The design must feel like a working control-room decision surface: calm, precise, dense, legible, and grounded in system state.

The design must not feel like:

- A marketing dashboard.
- A consumer energy app.
- A generic AI SaaS landing page.
- A decorative analytics gallery.
- A fake live-control console.

The interface exists to help the operator answer:

1. What is happening?
2. What flexibility exists?
3. What flexibility can be trusted?
4. What should be dispatched?
5. Did the decision work?
6. What was learned?

Every visual decision must support one of those questions.

---

## 2. Core Visual Principles

### 2.1 Operational First

The interface should prioritize decision readiness over aesthetic novelty.

Visual prominence must follow the product information hierarchy:

- Tier 1: Decision-critical information.
- Tier 2: Decision context.
- Tier 3: Supporting information.
- Tier 4: Metadata.

Tier 1 information should be visible without hunting. Tier 4 information should not compete for attention.

### 2.2 Dense but Scannable

The frontend should support repeated operational use. It should present many values cleanly without turning the page into unrelated widgets.

Density is good when it improves comparison, prioritization, or decision confidence. Density is bad when it hides the next action or makes metric meaning ambiguous.

### 2.3 Evidence Over Hype

Do not use visual language that implies magic, autonomous certainty, or generic intelligence.

Use precise labels such as:

- Trusted flexibility.
- Expected flexibility.
- Confidence.
- Constraint check.
- Actual vs. committed response.
- Verification result.
- Learning outcome.

Do not use labels such as:

- AI score.
- Smart recommendation.
- Magic optimization.
- AI-powered insights.
- Genius mode.

### 2.4 Simulation Honesty

The MVP is simulation-first and does not provide real-world device control.

The design must make simulation mode persistently visible. Any action related to dispatch must visually communicate that it is simulation/testing, not physical device control.

No visual pattern may imply that GridFlex AI is sending commands to real devices in MVP v0.1.

### 2.5 Contract-Visible, Not Frontend-Invented

Numbers and states shown by the UI must come from contract-defined data or canonical fields.

The UI may format, group, compare, sort, filter, and visualize data. It must not invent authoritative domain values, derived trust values, or unofficial confidence aggregates.

---

## 3. Information Density Rules

### 3.1 Page Density

Overview should be moderately dense and optimized for situational awareness.

Flexibility should be the densest page because it owns the full resource portfolio and resource-level trust information.

Dispatch should be focused, with density concentrated around the decision window, relevant resources, recommended dispatch plan, rationale, and constraint check.

Experiments should support detailed comparison, but comparison structure must keep baseline and trust-aware results aligned.

### 3.2 Density by Information Tier

Tier 1 information may use larger type, stronger placement, or persistent visibility.

Tier 2 information should be close to Tier 1 information but visually quieter.

Tier 3 information belongs in secondary sections, expandable regions, inline details, or drawers.

Tier 4 metadata should be available for inspection but visually minimized.

### 3.3 Avoid False Symmetry

Do not give equal visual weight to all metrics simply because they are displayed together.

For example, `trusted_kw` should be more prominent than `potential_kw` when the operator is deciding whether flexibility can be trusted.

### 3.4 Avoid Dashboard Filler

Do not create metric cards, charts, badges, or panels unless each item answers a product-approved question from FRONTEND_PRODUCT_SPEC.md.

---

## 4. Layout System

### 4.1 Application Shell

The shell must support exactly four primary navigation items:

- Overview.
- Flexibility.
- Dispatch.
- Experiments.

No nested primary navigation is required for MVP.

The shell should also provide space for:

- Scenario context where relevant.
- Persistent simulation-mode indication.
- System status representation if needed.

The exact shell layout is deferred to frontend architecture and component documentation.

### 4.2 Page Structure

Each page should use a consistent pattern:

- Page header with page purpose and scenario context where applicable.
- Primary decision area.
- Supporting context area.
- Detail or activity area when required by the product spec.

Do not introduce unrelated sidebars, widget grids, or ornamental sections.

### 4.3 Spatial Hierarchy

Use spacing to separate decision groups, not to create decorative emptiness.

Related values should sit close enough for comparison. Unrelated workflows should be clearly separated.

### 4.4 Responsive Priority

Desktop is the primary experience. Tablet must remain fully usable. Mobile must be responsive and usable but is secondary.

Mobile views should preserve meaning by stacking and prioritizing, not by removing required MVP information.

---

## 5. Typography

### 5.1 Fonts

Primary UI font: Inter
Display/identity font: Space Grotesk
Technical/data font: JetBrains Mono

Usage:

Space Grotesk:
- wordmark
- major page titles
- selected identity moments

Inter:
- normal UI
- body
- labels
- controls
- tables
- metrics

JetBrains Mono:
- IDs
- scenario IDs
- simulation IDs
- technical metadata
- seeds/technical values where appropriate

Never use JetBrains Mono for normal prose.

### 5.2 Typography Scale

| Role | Size / Line Height |
|------|-------------------|
| Display | 32 / 38 |
| Page Title | 24 / 30 |
| Section | 18 / 24 |
| Metric XL | 28 / 34 |
| Metric | 22 / 28 |
| Body | 14 / 20 |
| Body Small | 13 / 18 |
| Metadata | 12 / 16 |

### 5.3 Typography Weights

700 — major emphasis
600 — headings/important metrics
500 — labels/controls
400 — body

### 5.4 Semantic Type Roles

The design system should define type by role, not by arbitrary visual style.

Required roles:

| Role | Purpose |
|---|---|
| Page title | Identify the current page and operator question. |
| Section title | Mark major page sections from the product spec. |
| Metric value | Show decision-critical numeric values. |
| Metric label | Name the metric using canonical terminology. |
| Unit label | Display units such as kW, kWh, minutes, percent, or confidence range. |
| Table header | Support scanning and sorting of tabular data. |
| Table cell | Present dense operational values. |
| Status label | Represent state without ambiguity. |
| Helper text | Clarify empty, loading, and error states. |
| Metadata text | Display IDs, seeds, timestamps, and technical metadata quietly. |

### 5.5 Typography Rules

Metric values should be easy to compare. Units must remain visible and attached to the value.

Canonical field names may appear in technical/detail contexts, but user-facing labels should use canonical product terms where clearer.

Do not use oversized marketing-style headings inside operational panels.

Do not use tiny type for decision-critical values.

Do not rely on typography alone to convey error, warning, success, confidence, or availability state.

---

## 6. Color System

This design system uses ONLY two chromatic brand colors plus a neutral system. No unrelated blues, greens, purples, cyans, oranges, etc. are introduced as normal brand/UI colors.

The palette is constructed from tints, shades, and tones of these two colors plus restrained neutral values.

### Primary Brand Color: Burgundy

| Scale | Hex | Note |
|-------|-----|------|
| 50 | #F7ECEF | Warmest tint |
| 100 | #EFD9DE | |
| 200 | #DEB4BE | |
| 300 | #C78998 | |
| 400 | #A95A6D | |
| 500 | #6B1E2E | Primary brand |
| 600 | #561823 | Strong accent |
| 700 | #41121B | |
| 800 | #2B0C12 | |
| 900 | #160609 | Darkest shade |

### Secondary Brand Color: Warm Cream

| Scale | Hex | Note |
|-------|-----|------|
| 50 | #FEFCF8 | Warmest tint |
| 100 | #FBF6ED | |
| 200 | #F7EFE2 | |
| 300 | #F1E7D6 | Secondary brand |
| 400 | #D8C7AE | |
| 500 | #BCA98C | |
| 600 | #9D896C | |
| 700 | #7D6A50 | |
| 800 | #5E4E39 | |
| 900 | #403426 | Darkest shade |

### Neutral System (NOT a third brand-color family)

| Name | Hex | Purpose |
|------|-----|---------|
| Ink | #171412 | Primary text, high-contrast |
| Charcoal | #302B27 | Secondary text |
| Grey | #6F6963 | Disabled/text-secondary |
| Light Grey | #B9B2AA | Subtle dividers, muted backgrounds |
| Mist | #E5E0DA | Surface fills, light contexts |
| White | #FFFFFF | Clean canvas |

**The neutral system exists to support readability and structure and is NOT a third brand-color family.**

### Color Usage Distribution

- warm neutral/cream surfaces: approximately 70–80%
- white: approximately 10–20%
- burgundy: approximately 5–10%
- strong burgundy (600+): less than 5%

**Burgundy is primarily for:**
- identity
- actions
- active states
- emphasis
- important system signals

**Cream is primarily for:**
- environment
- backgrounds
- warm surfaces
- contextual grouping

**Do NOT make the application predominantly burgundy.**

### Semantic Color Usage

Normal: neutral/cream
Active/action: Burgundy 500
Selected: Burgundy 100 background + Burgundy 600 foreground/border
Success/verified: Burgundy 700 / Burgundy 100
Warning/uncertainty: Cream 500–700 / neutral tones
Error/failed: Burgundy 700–900
Inconclusive: neutral grey

**Do not create a rainbow semantic palette.**

**Semantic state must never be interpreted as arbitrary decorative color.**

**If accessibility or conventional semantic communication absolutely requires a separate state color in a future implementation, that is an explicit exception requiring design review. Do not silently add new colors.**

#### Flexibility Visual Language

Represent:

Potential → Expected → Trusted → Delivered

using tonal progression rather than four unrelated colors.

Potential: Burgundy 200
Expected: Burgundy 400
Trusted: Burgundy 600
Delivered: Burgundy 800

The visual progression should communicate increasing concreteness/verification.

**Do NOT automatically use green for Trusted.**

#### Baseline vs Trust-Aware

Baseline: Neutral grey
Trust-aware: Burgundy

**Do NOT visually imply that Trust-aware automatically means "better" or "successful".**

Experiment results determine whether it is an improvement, neutral, regression, or inconclusive.

#### Color Usage Rules

Do not use green to automatically imply trust-aware wins. Experiment outcomes may be improvement, neutral, regression, or inconclusive.

Do not use red for all negative-looking numbers. Some negative values may be meaningful directional differences and need domain context.

Do not rely on color alone. Pair state color with text, icons, patterns, labels, or position.

Do not make the entire interface a single-color theme. The palette must support operational distinction across flexibility, dispatch, verification, and experiment comparison.

---

## 7. Shape Language and Surfaces

### 7.1 Shape Language
GridFlex is structured, not bubbly.
Radius: Controls 6px, Panels 8px, Drawers 10px, Inputs 6px, Status pills 999px only when semantically appropriate. Do not make everything pill-shaped.
### 7.2 Surface Purpose

Surfaces should group operationally related information, not decorate the page.

Acceptable surface uses:

- System snapshot groups.
- Portfolio summary groups.
- Resource tables.
- Dispatch plan and constraint check groups.
- Baseline vs. trust-aware comparison groups.
- Detail drawers.
- Empty/error/loading state containers.

### 7.2 Panel Rules

Panels should have clear titles, compact supporting labels, and visible relationship to the operator question they answer.

Do not nest cards inside cards.

Do not create decorative floating cards that are unrelated to a workflow.

Do not use hero sections, oversized marketing cards, or promotional banners.

### 7.3 Status Visibility

Simulation mode should be visible from the shell or page header across relevant pages.

System status may be represented in the global shell/header and should not become a large dashboard section unless product scope changes.

---

## 8. Tables and Lists

### 8.1 Resource Portfolio Table

The Flexibility page resource portfolio is expected to use a dense table or table-like list.

Required row information from the product spec:

- Resource identity: ID, type, location_id.
- Potential: `potential_kw`.
- Expected: `expected_kw`.
- Trusted: `trusted_kw`.
- Confidence: `confidence`.
- Availability/status: available, dispatched, completed, unavailable.
- Key constraint indicator.

### 8.2 Table Design Rules

Tables must support rapid scanning and comparison.

Numeric columns should align consistently. Units should be visible in headers or cells.

Rows should have stable height and enough spacing for legibility.

Sorting/filtering affordances may be used where product-approved, but they must remain lightweight.

Resource rows should be selectable to open the resource detail drawer.

### 8.3 Table Prohibitions

Do not hide required resource trust values behind hover-only interactions.

Do not convert dense operational tables into oversized cards on desktop.

Do not introduce add/edit/delete resource actions.

Do not introduce manual trust or confidence controls.

---

## 9. Drawers and Detail Interactions

### 9.1 Resource Detail Drawer

The Flexibility page uses a drawer, not a new primary page, for resource detail.

The drawer should show:

- Current resource state.
- Potential / expected / trusted / confidence.
- Relevant constraints.
- Compact response history.
- Recent actual vs. dispatched information where available.
- Override occurrences where available.

### 9.2 Drawer Rules

Drawers should preserve page context. The operator should be able to inspect details without losing the portfolio view.

Drawers should avoid becoming full resource-management screens.

Drawer metadata should be quiet and inspectable, not visually dominant.

### 9.3 Experiment Detail

Experiment/event detail may be inline or drawer-based. It must not create a fifth primary page in MVP.

DEFERRED - TO BE DECIDED: Exact interaction pattern for experiment/event detail.

---

## 10. Controls and Actions

### 10.1 Primary Action

The primary MVP action is Simulate Dispatch on the Dispatch page.

This action must visually communicate that it triggers simulation of a recommended dispatch plan, not real-world dispatch.

### 10.2 Filters

Flexibility page filters must remain minimal:

- Type.
- Status.
- Location only if justified by portfolio scale.
- Text search by resource ID is allowed.

### 10.3 Control Rules

Controls must be clear, restrained, and attached to the workflow they affect.

Controls must not expose backend-owned configuration such as solver parameters, objective weights, ML model settings, trust formulas, API settings, or physical device controls.

### 10.4 Deferred Control Decisions

DEFERRED - TO BE DECIDED: Exact global scenario-selection interaction.

DEFERRED - TO BE DECIDED: Exact control styling.

DEFERRED - TO BE DECIDED: Exact disabled/loading interaction for Simulate Dispatch.

---

## 11. State Representation

### 11.1 Required General States

All pages/components must account for:

- Loading.
- Populated / success.
- Empty.
- Error.

### 11.2 Dispatch Page States

The Dispatch page must account for:

- Recommendation ready.
- Simulation running.
- Simulation complete.
- Simulation failed.

These are UI-facing approximations until backend canonical Dispatch State and Simulation Run State values are finalized.

### 11.3 Experiments Page States

The Experiments page must account for:

- Ready.
- Running.
- Completed.
- Failed.

These are UI-facing approximations until backend canonical Experiment Run State values are finalized.

### 11.4 State Design Rules

State labels must use canonical language where available.

Errors must be explicit and local to the failing section where possible.

Empty states must describe the missing condition without inventing product features.

Loading states must not imply fake real-time system behavior.

### 11.5 Deferred State Decisions

DEFERRED - TO BE DECIDED: Canonical Simulation Run State values.

DEFERRED - TO BE DECIDED: Canonical Dispatch State values.

DEFERRED - TO BE DECIDED: Canonical Experiment Run State values.

DEFERRED - TO BE DECIDED: Exact loading skeleton/spinner/progress pattern.

---

## 12. Metric Presentation

### 12.1 Metric Rules

Every metric must show:

- A clear canonical label.
- A value.
- A unit when applicable.
- Enough context to prevent kW/kWh confusion.
- Provenance through contract-aligned data or canonical fields.

### 12.2 Required Metric Families

Operational snapshot metrics:

- Renewable opportunity in kWh where energy over a window is shown.
- Trusted flexibility in kW where deliverable capacity is shown.
- Grid headroom in kW.

Resource trust metrics:

- `potential_kw`.
- `expected_kw`.
- `trusted_kw`.
- `confidence`.

Experiment primary metrics:

- Flexibility delivery error.
- Overcommitment.
- Renewable absorption.

Experiment secondary metrics:

- Constraint violations.
- Deadline violations.
- Rebound.
- Committed flexibility.
- Actual flexibility.
- Actual/committed reliability.

### 12.3 Metric Prohibitions

Do not introduce Available Flexibility as an independent metric.

Do not introduce Average AI Confidence as a required portfolio metric.

Do not show unlabeled numbers.

Do not mix kW and kWh in a single visual without explicit labels.

Do not invent frontend-only calculations for domain authority.

---

## 13. Data Visualization

### 13.1 Visual Metaphor: FLOW
The interface should visually reinforce:
Renewable Opportunity → Flexibility → Trust → Dispatch → Response → Verification → Learning
This should influence charts, timelines, dispatch visualization, event replay, and comparison views.
Do not use generic energy imagery as the primary visual language.

### 13.2 Visualization Purpose

Charts and visualizations must answer an operator question. They are not decoration.

Acceptable visualization purposes include:

- Show renewable opportunity over a decision window.
- Compare potential, expected, and trusted flexibility.
- Show recommended dispatch over time.
- Show actual vs. committed response.
- Compare baseline vs. trust-aware scheduling.
- Show delivery error, overcommitment, renewable absorption, and reliability outcomes.
- Show event replay across the canonical loop.
- Show trust update effects after verification.

### 13.2 Preferred Encoding Hierarchy
1. position
2. length
3. line
4. area
5. color
Use color sparingly. Avoid rainbow charts.
Charts must communicate operational meaning rather than decorate empty space.

### 13.3 Chart Rules

Use consistent series identities across pages.

Keep axis labels, units, and time resolution visible.

Use the 15-minute time-step context where relevant.

Make baseline vs. trust-aware comparisons visually symmetric, without implying a predetermined winner.

Use annotations for constraint violations, deadline violations, override events, failure events, and rebound events only when contract data supports them.

### 13.3 Visualization Prohibitions

No decorative charts.

No maps in MVP.

No Sankey, geographic, correlation, or advanced historical visualizations unless explicitly approved post-MVP.

No fake real-time animation.

No chart that obscures whether values are forecast, dispatched, simulated, verified, or learned.

### 13.6 Still Implementation-Level
DEFERRED - TO BE DECIDED: Exact chart library.
DEFERRED - TO BE DECIDED: Exact chart component inventory.
DEFERRED - TO BE DECIDED: Exact visual treatment for confidence bands and uncertainty.
DEFERRED - TO BE DECIDED: Exact event replay interaction pattern.

---

## 14. Page-Specific Design Guidance

### 14.1 Overview

Overview should answer: What is happening right now?

Design emphasis:

- System-level snapshot.
- Renewable opportunity summary.
- Aggregate flexibility state.
- Next or most recent dispatch summary.
- Recent activity.

Avoid:

- Resource management.
- Weather dashboard.
- Tariff dashboard.
- Maps.
- Device controls.
- Generic historical analytics.

### 14.2 Flexibility

Flexibility should answer: What flexible resources exist, and how trustworthy are they?

Design emphasis:

- Dense resource portfolio table.
- Potential / expected / trusted comparison.
- Resource-level confidence.
- Availability/status.
- Constraint indicators.
- Detail drawer.

Avoid:

- Add/edit/delete controls.
- Manual trust edits.
- Manual confidence edits.
- Device provisioning.

### 14.3 Dispatch

Dispatch should answer: What should the system dispatch for this renewable opportunity?

Design emphasis:

- Decision window.
- Renewable opportunity detail.
- Relevant flexibility only.
- Recommended dispatch plan `x[i,t]`.
- Rationale.
- Constraint check.
- Simulate Dispatch action and result.

Avoid:

- Full portfolio duplication.
- Physical dispatch approval language.
- Solver configuration.
- Raw optimizer logs.

### 14.4 Experiments

Experiments should answer: Did the trust-aware approach actually work?

Design emphasis:

- Baseline vs. trust-aware comparison.
- Outcome interpretation: improvement, neutral, regression, inconclusive.
- Primary and secondary metrics.
- Delivery visualization.
- Event replay.
- Trust update.

Avoid:

- Automatically declaring trust-aware the winner.
- ML training controls.
- Dataset exploration.
- Infrastructure monitoring.

---

## 15. Accessibility Principles

The design must be accessible enough for operational use under pressure.

Rules:

- Text must remain legible across desktop, tablet, and mobile.
- Interactive targets must be large enough for reliable selection.
- Keyboard navigation must support primary workflows.
- Focus states must be visible.
- Color must not be the only indicator of status or comparison.
- Tables must preserve readable headers and associations.
- Error states must be readable by assistive technology.
- Motion, if used, must be restrained and non-essential.

DEFERRED - TO BE DECIDED: Exact accessibility acceptance checklist and testing tooling.

---

## 16. Responsive Principles

Desktop should provide the richest comparison experience.

Tablet should preserve all primary workflows with adjusted layout density.

Mobile should prioritize the current operator question and allow inspection through stacking, drawers, or accordions as needed.

Required information must not disappear on smaller screens. It may be reorganized, summarized, or moved behind explicit detail interactions.

Tables on mobile may transform into compact row groups only if required values remain visible and comparable.

DEFERRED - TO BE DECIDED: Exact breakpoints.

DEFERRED - TO BE DECIDED: Exact mobile table/list pattern.

---

## 17. Anti-AI-Slop Rules

The frontend must avoid generic AI-generated dashboard patterns.

### Hard Prohibitions
- purple AI gradients
- blue/purple SaaS gradients
- neon glow
- glassmorphism
- excessive rounded cards
- giant card grids
- excessive shadows
- decorative charts
- AI robot imagery
- generic energy illustrations
- floating blobs
- gradient text
- AI-powered badges
- excessive icon usage
- random colors
- rainbow charts
- giant hero sections
- fake real-time indicators
- fake live-data animation
- gamification
- consumer-app aesthetics
- visual noise disguised as sophistication

### Do Not Create
- A landing page instead of the operational app.
- Hero sections.
- Marketing copy blocks.
- Decorative gradients with no operational meaning.
- Abstract AI illustrations.
- Generic KPI cards unrelated to GridFlex questions.
- Random trend charts.
- Chatbot or conversational UI.
- Gamification.
- Fake live status indicators.
- Notification center.
- Settings/preferences page.
- User profile UI.
- Role/permission UI.
- Arbitrary fifth primary page.

### Do Create
- Clear operational hierarchy.
- Contract-aligned metrics.
- Dense resource comparison.
- Honest simulation status.
- Decision rationale presentation.
- Constraint visibility.
- Verification visibility.
- Learning outcome visibility.

---

## 18. Terminology Rules

Use canonical terminology from NAMING_AND_CONVENTIONS.md.

Required terms include:

- FlexibilityResource.
- Trust State.
- Renewable Forecast.
- Opportunity.
- Dispatch Plan.
- Actual Response.
- Verification.
- Learning.
- Scenario.
- Simulation Run.
- Experiment Run.
- Behavior Record.

Resource states:

- available.
- dispatched.
- completed.
- unavailable.

Trust fields:

- `potential_kw`.
- `expected_kw`.
- `trusted_kw`.
- `confidence`.

Core loop:

```
Observe -> Represent -> Estimate -> Trust -> Match -> Dispatch -> Simulate -> Verify -> Learn
```

Frontend product story:

```
Understand -> Trust -> Decide -> Simulate -> Verify -> Learn
```

Do not rename domain concepts for style.

---

## 19. Still Implementation-Level

The design system must distinguish between:

**LOCKED:**
- color system
- typography
- shape language
- density
- surfaces
- visualization language
- motion philosophy
- iconography philosophy
- anti-slop rules

**STILL IMPLEMENTATION-LEVEL:**
- exact component CSS
- exact spacing values where not already specified
- breakpoint implementation
- charting library
- exact component dimensions
- exact animation durations
- exact icon library

Do not invent those implementation details unless the existing document already specifies them.

---

## 20. Contradictions and Unresolved Items

### Contradictions Found During Authoring

No contradiction was found between this design-system document and FRONTEND_PRODUCT_SPEC.md.

This document preserves the four-page MVP, simulation-first boundary, product information hierarchy, data ownership boundary, and prohibited feature list from FRONTEND_PRODUCT_SPEC.md.

### Related Existing Status Note

FRONTEND_PRODUCT_SPEC.md was updated to LOCKED during the final frontend implementation preparation phase. Its Current Status and Document Status both now read LOCKED. This design-system document preserves its earlier authoritative relationship with the product spec.

### Unresolved Items Carried Forward

The following unresolved items affect future design and implementation:

- API JSON field naming remains pending.
- Simulation Run State values remain TBD.
- Dispatch State values remain TBD.
- Experiment Run State values remain TBD.
- Timezone handling remains TBD.
- Exact trust and confidence formulas remain backend/AI/ML-owned and TBD.
- Optimization objective weights remain pending.
- Specific ML model remains TBD.

---

## 21. Files Consulted

1. `frontend/FRONTEND_PRODUCT_SPEC.md` - frontend product scope, page inventory, hierarchy, states, MVP boundary, and deferred decisions.
2. `NAMING_AND_CONVENTIONS.md` - canonical terminology, states, fields, units, and unresolved naming decisions.
3. `CONTRACTS.md` - backend-to-frontend shapes, data boundary, metrics, and frozen contract concepts.

---

## Document Status

LOCKED — VISUAL DESIGN SYSTEM v1.0

This document is the finalized visual identity for MVP implementation. Future visual identity changes require an explicit design decision.

---

*End of FRONTEND_DESIGN_SYSTEM.md*
