# FRONTEND ARCHITECTURE

## Purpose

Define the technical architecture for the GridFlex AI frontend: how the already-defined frontend product (FRONTEND_PRODUCT_SPEC.md) and design system (FRONTEND_DESIGN_SYSTEM.md) will be technically structured. This document establishes architectural style, layers, responsibilities, data flow, state ownership, API boundary, mock/fixture boundary, routing, feature boundaries, component principles, visualization boundary, error/state handling, dependency direction, testing, and integration strategy.

## Scope

This document covers frontend technical architecture only. It does not contain implementation code, React components, pages, routes in code, source files, CSS, Tailwind configuration, or package choices.

This document does not redefine product scope, visual design, backend contracts, domain logic, optimization, simulation, or learning. Those are owned by FRONTEND_PRODUCT_SPEC.md, FRONTEND_DESIGN_SYSTEM.md, and the backend/project documents respectively.

## Authority

FRONTEND_PRODUCT_SPEC.md is authoritative for frontend product scope, page responsibilities, information hierarchy, navigation, MVP boundary, and data boundary.

FRONTEND_DESIGN_SYSTEM.md is authoritative for frontend presentation rules.

NAMING_AND_CONVENTIONS.md is authoritative for canonical domain terminology, field names, units, and state naming.

CONTRACTS.md is authoritative for backend-to-frontend data shapes and contract boundaries.

This document owns frontend technical architecture only. Implementation details that remain undecided must remain deferred.

## Current Status

LOCKED

Frontend product and design are locked. Frontend architecture boundaries are defined. Most implementation-level decisions (folder structure, specific libraries, exact endpoint names, package versions) remain deferred.

---

## 1. Architectural Position

The frontend is a **presentation and interaction layer** that consumes GridFlex AI's backend/domain intelligence.

**Frontend owns:**

- Presentation (rendering data into UI).
- Interaction (user clicks, filters, navigation, simulation triggering).
- View state (selected resource, drawer open/closed, active tab, filter values).
- Navigation and routing.
- Visualization (transforming contract data into charts, tables, status indicators).
- Client-side orchestration of UI behavior (e.g., opening a drawer, triggering a simulation request).

**Frontend does NOT own authoritative:**

- Flexibility estimation.
- Trust calculation (potential_kw, expected_kw, trusted_kw, confidence).
- Optimization (dispatch plan formulation and solving, x[i,t]).
- Simulation behavior (device modeling, actual response generation, override/failure/rebellion).
- Verification (actual vs. dispatched comparison).
- Learning (trust parameter updates).
- Domain decision logic.

The frontend consumes contract-defined data. It does not duplicate backend intelligence.

---

## 2. Architectural Style

The frontend will use a **React + TypeScript** application with a layered, dependency-inverted structure. This technology direction is established by the project root README.md.

**Intended characteristics:**

- Single application, client-rendered, served by static hosting or the backend in MVP.
- REST-first communication with the backend (per project architecture).
- Contract-aligned mock data for early development.
- Component-based, presentational-leaning composition.
- Explicit data boundaries with no hidden domain logic in UI components.

**Intentionally NOT introduced:**

- Micro-frontends.
- Frontend service mesh.
- Unnecessary state-management frameworks (unless justified).
- Event buses without a real product requirement.
- Specular plugin architectures.
- Premature WebSocket architecture.
- Excessive abstraction layers.

The architecture should be strong enough for the MVP workflow but simple enough to implement and debug during a hackathon.

---

## 3. Logical Application Layers

This document defines **responsibilities** and **dependency direction**, not folder/file structure. The actual folder structure is a later task (FRONTEND_COMPONENTS.md or implementation).

### Layer 1: Presentation / UI Layer

- **Responsibility:** Renders UI primitives, presentational components, and visualization components.
- **Consumes:** Feature/view logic and view state.
- **Does not:** Fetch domain data directly. Calculate trust or optimization. Call backend transport directly.
- **Examples:** Metric displays, tables, charts, status badges, drawers, buttons, form controls.

### Layer 2: Page / Feature Composition

- **Responsibility:** Composes presentational components into the four MVP pages and manages feature-level view state.
- **Consumes:** Feature data and actions from the data-access layer.
- **Does not:** Own domain truth. Duplicate backend calculations. Contain transport logic.
- **Examples:** Overview page, Flexibility page, Dispatch page, Experiments page.

### Layer 3: View-State / Interaction Orchestration

- **Responsibility:** Manages UI-specific state (selected resource, drawer state, filter values, search text, active tabs) and orchestrates interaction flows (e.g., triggering a simulation and handling the running/complete/failed progression).
- **Consumes:** Data from the data-access layer; emits actions to the data-access layer.
- **Does not:** Own server/domain state. Implement domain intelligence.
- **Examples:** Drawer toggle state, search/filter state, Dispatch simulator action lifecycle.

### Layer 4: Data-Access / API Adapter

- **Responsibility:** Provides a stable frontend-facing data interface backed by either mock data or real backend API. Fetches, caches, and exposes data and commands to features.
- **Consumes:** Backend contracts (through API adapter) or mock fixtures (through mock adapter).
- **Does not:** Implement domain logic. Transform domain meaning. Invent fields.
- **Examples:** Resource portfolio loader, dispatch recommendation loader, simulation runner, experiment results loader.

### Layer 5: Contract Mapping / Normalization

- **Responsibility:** Adapts incoming data from one or more sources to a single frontend-facing data shape. Ensures canonical terminology, units (kW vs kWh), and field names are enforced at this boundary.
- **Consumes:** Raw backend responses or mock fixtures.
- **Does not:** Invent domain semantics. Change the meaning of canonical fields.
- **Examples:** Mapping backend response to canonical field names. Ensuring kW/kWh units are labeled.

The mock adapter and API adapter satisfy a shared interface at Layer 4, so the rest of the frontend does not distinguish between mock and real data.

> **Note:** Layers 4 and 5 may be combined into a single cohesive boundary during implementation. This document defines the principle of a stable frontend-facing boundary regardless of source.

---

## 4. Data Flow

Conceptually:

```
Backend / Mock Source
        ↓
Data-Access / API Adapter          (Layer 4)
        ↓
Contract Mapping / Normalization   (Layer 5)
        ↓
Feature / View Model               (Layer 3)
        ↓
Page Composition                   (Layer 2)
        ↓
Components / Visualization         (Layer 1)
        ↓
User Interaction
        ↓
API / Simulation Request
        ↓
Updated Backend Result
        ↓
Updated View State
```

The frontend must not bypass the data boundary to directly implement domain logic.

Data flow direction rule:

- Data flows inward through the adapter boundary.
- Actions flow outward through the adapter boundary.
- UI components receive already-normalized, canonical data.
- No component below the presentation layer receives raw unvalidated backend data structures without normalization.

---

## 5. Contract-First Boundary

The frontend must align with the project's established contracts.

**Frontend should consume authoritative backend data through a defined adapter boundary.**

The frontend does not invent domain concepts. The following are authoritative and must not be re-implemented or re-defined in frontend code:

- Flexibility estimation
- Trust calculation (potential_kw, expected_kw, trusted_kw, confidence)
- Optimization (dispatch plan x[i,t])
- Simulation execution
- Verification (delivered vs. dispatched, error, overcommitment)
- Learning (trust parameter updates)

**Frontend-facing transformation rules:**

The frontend may:

- Format, group, sort, filter, and visualize data.
- Derive display-only aggregates for presentation (with clear documentation that these are visual groupings, not authoritative domain values).
- Map backend responses to canonical fields.

The frontend must not:

- Re-calculate potential_kw, expected_kw, trusted_kw, or confidence.
- Re-implement dispatch optimization.
- Re-derive overcommitment or delivery error from raw values (unless the backend contract explicitly returns raw data and delegates the comparison — in which case only presentation logic is permitted).
- Invent new domain fields that conflict with NAMING_AND_CONVENTIONS.md.

A transformation must not change domain meaning. If a calculation feels like "real logic," it belongs in the backend contract, not the frontend.

---

## 6. Mock / Fixture Boundary and Adapter Pattern

During early implementation, the frontend will use contract-aligned mock/fixture data. This is required because backend contracts and implementation may lag.

**Architecture principle:**

The rest of the frontend should not care whether its data is mock or real.

```
                ┌── Mock Adapter
Feature Data ←──┤
                └── API Adapter
```

Both adapters satisfy the same frontend-facing interface (Layer 5).

### 6.1 Mock Data Requirements

- Must follow project contracts (CONTRACTS.md domain contract and backend-to-frontend shapes).
- Must represent realistic states: available, dispatched, completed, unavailable resources; varying confidence levels; recommendation ready, simulation running/complete/failed states.
- Must clearly indicate simulation/mock context.
- Must not invent frontend-only domain models.
- Must not present mock values as live utility data.
- Must not pretend to implement trust calculation or optimization.

**Do NOT:**

- Build a fake backend inside the frontend.
- Invent unsupported domain fields in mock data.
- Make mock data indistinguishable from real backend data without a clear simulation-mode indicator.

### 6.2 Adapter Pattern (Mock ↔ Real API Strategy)

The frontend must support both mock data and real API data through a single, unified interface. This is a hard architectural requirement, not a convenience.

#### 6.2.1 Mock and Real Data Share One Contract

- **One frontend-facing interface**: Mock data and real API data must conform to the same TypeScript interfaces/types.
- **No dual models**: Do not create separate data shapes for mock vs. real data. The mock layer must implement the exact same contract as the real API layer.
- **Contract-first**: Define shared types in `src/types/contracts/` and have both mock and real implementations import from them.
- **Type safety**: Any divergence between mock and real data shapes is a build-time failure, not a runtime surprise.

#### 6.2.2 Adapter Pattern Implementation

- **Data-access boundary**: All API calls (mock or real) must go through a dedicated data-access/adapter layer.
- **No direct HTTP in presentation components**: React components must never call `fetch`, `axios`, or any HTTP client directly.
- **Adapter responsibility**: The adapter translates between the external API contract and the frontend's internal domain model.
- **Swap mechanism**: Switching between mock and real data is done by changing the adapter implementation or configuration, not by modifying components.
- **Single source of truth**: The adapter is the only place where data source selection logic lives.

#### 6.2.3 Mock Data Guidelines

- **Realistic fidelity**: Mock data must be realistic enough to exercise all UI states, edge cases, and interactions defined in FRONTEND_PRODUCT_SPEC.md.
- **State coverage**: Mock data must include examples of all status values, empty states, error states, and boundary conditions.
- **Deterministic**: Mock data should be deterministic for reproducible testing and demos.
- **Versioned**: Mock data should be versioned alongside the contracts it implements.

#### 6.2.4 Real API Guidelines

- **Contract compliance**: Real API responses must validate against the same shared contracts as mock data.
- **Runtime validation**: Use runtime schema validation (e.g., Zod) at the adapter boundary to catch contract violations from the backend.
- **Error normalization**: Backend errors must be normalized into the frontend's standard error shape at the adapter boundary.
- **Graceful degradation**: The UI must handle partial failures, stale data, and unavailable services gracefully.

#### 6.2.5 Configuration

- **Environment-based selection**: Use environment variables or build-time configuration to select mock vs. real data source.
- **No hardcoded switches in components**: Data source selection must never be hardcoded in presentation components.
- **Explicit override**: Provide an explicit development override for demos and local testing, but keep it out of production builds.

### 6.3 Backend Integration and Merge-Conflict Rules

#### 6.3.1 Integration Boundary

- **Frontend owns presentation**: The frontend owns UI composition, interaction logic, and presentation state.
- **Backend owns data**: The backend owns persistence, business logic, and data authority.
- **Contract is the boundary**: The shared API contract is the integration boundary between frontend and backend.
- **No shared implementation**: Do not share runtime code between frontend and backend unless explicitly agreed and versioned.

#### 6.3.2 Merge-Conflict Prevention

- **Contract files are single-owned**: Shared contract files must have a single, clearly designated owner to prevent merge conflicts.
- **API changes are explicit**: Any API change must be accompanied by a corresponding contract update and must be reviewed by both frontend and backend owners.
- **No silent contract drift**: Mock data must never drift from the real API contract. Any divergence must be treated as a bug.
- **Version contracts**: Use explicit contract versioning for breaking changes.
- **Changelog discipline**: API and contract changes must be documented in a changelog with migration notes.

#### 6.3.3 Integration Testing

- **Contract tests**: Maintain contract tests that validate mock data, real API responses, and frontend consumption against the same shared schema.
- **End-to-end coverage**: Critical user journeys must be covered by end-to-end tests that exercise the full data flow.
- **Failure injection**: Test error handling, timeouts, and partial failures in the integration layer.

### 6.4 Contract Safety

#### 6.4.1 Type Safety

- **Shared types**: Use shared TypeScript types for all API contracts.
- **No `any`**: Avoid `any` in contract boundaries. Use explicit, well-defined types.
- **Runtime validation**: Validate all external data at the boundary with a runtime schema validator.
- **Type generation**: Prefer generating types from a single source of truth (e.g., OpenAPI schema) where feasible.

#### 6.4.2 Data Integrity

- **Immutable by default**: Treat API data as immutable once received. Use immutable updates for state.
- **Normalization**: Normalize nested API responses into a consistent internal shape.
- **Null handling**: Explicitly handle `null` and `undefined` values. Do not assume fields are always present.
- **Default values**: Provide safe, explicit defaults for optional fields at the adapter boundary.

#### 6.4.3 Contract Evolution

- **Backward compatibility**: Prefer additive changes to breaking changes.
- **Deprecation policy**: Mark deprecated fields and provide a migration path.
- **Feature flags**: Use feature flags for gradual rollout of contract changes when needed.
- **Monitoring**: Monitor contract validation failures in production to detect drift early.

#### 6.4.4 Security at the Boundary

- **Input sanitization**: Sanitize and validate all data entering the frontend from external sources.
- **Output encoding**: Ensure data is safely rendered to prevent injection attacks.
- **Credential handling**: Never expose API keys, tokens, or sensitive credentials in frontend code or mock data.
- **Access control**: Respect backend authorization decisions; do not duplicate or bypass access control in the frontend.

The exact mock-data loading strategy (inline fixtures, mock service worker, etc.) is deferred. The boundary principle is established.

---

## 7. Routing Architecture

**MVP routes (exactly four):**

- `/` or `/overview` — Overview
- `/flexibility` — Flexibility
- `/dispatch` — Dispatch
- `/experiments` — Experiments

**Routing responsibilities:**

- Client-side routing with clean, deep-linkable URLs.
- Route-to-page mapping is one-to-one for MVP.
- No nested routes required for MVP.

**Detail routing:**

- Resource detail uses a Resource Detail Drawer (not a new primary route).
- Experiment/event detail uses inline/detail interaction or a drawer (not a new primary route).

**Scenario context:**

- Scenario context is a product requirement (FRONTEND_PRODUCT_SPEC.md section K).
- The exact scenario-selection interaction is explicitly DEFERRED.
- Do NOT assume a global dropdown, sidebar, modal, drawer, page-specific selector, or command palette.
- The routing architecture must support the *concept* of an active scenario without prematurely locking the selection interaction.

**Defer:**

- Exact routing library is deferred.
- Exact deep-linking structure for drawers/detail is deferred.

---

## 8. State Ownership

Two distinct categories of state must be kept separate.

### 8.1 Server / Domain State

Authoritative state originating from backend/domain systems.

| Example | Source |
|--------|--------|
| Renewable opportunity | Backend |
| Trusted flexibility (per resource and aggregate) | Backend (AI/ML) |
| Potential / expected flexibility | Backend |
| Confidence | Backend |
| Resource portfolio | Backend |
| Dispatch recommendation (x[i,t]) | Backend (Optimization) |
| Simulation results | Backend (Simulation) |
| Verification results | Backend (Verification) |
| Trust updates / learning outcomes | Backend (Learning) |
| Experiment results (baseline vs trust-aware) | Backend |

Rules:

- These must never be duplicated into uncontrolled frontend state.
- When modified, frontend state must be reconciled against authoritative sources.
- UI state must not be treated as a source of truth for domain decisions.

### 8.2 UI / View State

Frontend-owned interaction state.

| Example | Owner |
|--------|-------|
| Active route / page | Frontend |
| Resource detail drawer open/closed | Frontend |
| Selected resource | Frontend |
| Search text | Frontend |
| Filter values (type, status, location) | Frontend |
| Loading state per request | Frontend |
| Simulation-running / complete / failed UI state | Frontend |
| Experiment running / completed / failed UI state | Frontend |
| Visualization selection (e.g., which series to highlight) | Frontend |
| Active tabs in detail views | Frontend |

Rules:

- UI state must not be promoted to domain state.
- UI state should be local to where it is consumed unless cross-feature sharing is necessary.
- Avoid global stores for purely local interaction state.

### 8.3 State Management Approach

- The frontend should use a simple, maintainable state approach appropriate for the MVP.
- Prefer local component state for UI/view state where the scope is genuinely local.
- Use a minimal shared state mechanism only where multiple features genuinely need to coordinate (e.g., scenario context).
- **Do NOT impose a single global store for all state** unless justified by demonstrated need.
- **Do NOT introduce speculative Redux/Zustand/Jotai architecture before the need is established.**

**Deferred:** Exact state-management approach (local state, context, or a minimal shared store).

---

## 9. Error / Loading / Empty / Success Architecture

A consistent approach is required for all four general states and the feature-specific states.

### 9.1 General States

| State | Architecture Requirement |
|-------|------------------------|
| Loading | A shared loading primitive. Components should not invent per-component loading logic when a shared pattern suffices. |
| Success / Populated | Standard success rendering path. |
| Empty | Shared empty-state primitive with configurable messaging. Must not imply missing features. |
| Error | Shared error primitive. Errors must be local to the failing section where possible. Backend error codes/messages must be surfaced (per CONTRACTS.md error categories). |

### 9.2 Dispatch States

- Recommendation ready
- Simulation running
- Simulation complete
- Simulation failed

These are **UI-facing approximations** until backend canonical Simulation Run State values are finalized (NAMING_AND_CONVENTIONS.md section 10.5, TBD).

### 9.3 Experiments States

- Ready
- Running
- Completed
- Failed

Also **UI-facing approximations** until backend canonical Experiment Run State values are finalized.

### 9.4 State Design Rules

- State labels must use canonical language where available.
- Error states must be explicit and local to the failing section.
- Empty states must describe the missing condition without inventing product features.
- Loading states must not imply fake real-time system behavior.

**Deferred:** Exact canonical state enum mapping, exact skeleton/spinner pattern.

---

## 10. API Integration Boundary

The architecture should define a clear API boundary.

**Principles:**

- The frontend should not scatter HTTP calls throughout UI components.
- A centralized feature/data-access layer should own all backend interactions.
- Components should consume appropriate frontend-facing data/functions rather than knowing backend transport details.

**API characteristics (conceptual, from project ARCHITECTURE.md):**

- REST-first communication.
- Version prefix on paths (e.g., `/v1/`).
- Frontend initiates; backend responds.

**Do NOT finalize:**

- Exact endpoint names.
- Exact JSON field naming (snake_case vs. camelCase is still PENDING DECISION).
- Exact pagination strategy.
- Authentication implementation.

**Error handling (per CONTRACTS.md error categories):**

| Error Category | Frontend Handling |
|----------------|-------------------|
| Validation error (400) | Surface field-level error messages inline. |
| Infeasible dispatch (422) | Show constraint analysis from backend; do not force fallback. |
| Infeasible scenario (422) | Reject before processing; surface validation error. |
| Not found (404) | Show not-found state. |
| Solver timeout (504) | Surface timeout state; do not silently degrade. |
| Internal server error (500) | Show error state; no silent degradation. |
| Low confidence (206) | Surface low-confidence flag alongside results. |

---

## 11. Feature Boundaries

The architecture should align with the four MVP product areas:

| Feature | Page | Owns |
|--------|------|------|
| Overview | Overview | System snapshot, renewable opportunity summary, next dispatch summary, recent activity |
| Flexibility | Flexibility | Resource portfolio, resource-level trust, resource detail drawer, filtering/search |
| Dispatch | Dispatch | Current opportunity, relevant flexibility, recommended dispatch, simulation trigger/result |
| Experiments | Experiments | Baseline vs. trust-aware comparison, metrics, delivery visualization, event replay, trust update |

**Rules:**

- Shared feature logic should only become shared when there is a genuine, demonstrated need.
- Avoid creating a giant global utility layer.
- Avoid putting all logic into one global store.
- Each feature should own its data loading and its view state.
- Cross-feature coordination (e.g., scenario context) should be explicit and minimal.

---

## 12. Component Responsibility

This section defines principles, not individual component files. The later FRONTEND_COMPONENTS.md (or implementation phase) will define the concrete UI vocabulary.

**Component roles:**

- **Application shell:** Layout, header, navigation rail, scenario context display, simulation-mode indicator.
- **Navigation:** Primary navigation between the four pages.
- **Page composition:** Assembling sections into each page.
- **Domain presentation:** Displaying resources, trust state, dispatch plans, metrics.
- **Data visualization:** Charts, comparison views, delivery visualization.
- **Interaction/control:** Filters, search, Simulate Dispatch button, drawer triggers.
- **Feedback/state:** Loading, empty, error, success indicators.
- **Overlay/drawer:** Resource detail drawer, inline detail drawers.

**Principles:**

- A component should have a clear, single responsibility.
- Avoid giant page components that do everything.
- Avoid components that fetch arbitrary data across unrelated domains.
- Avoid components that calculate domain intelligence.
- Avoid components directly calling multiple unrelated backend endpoints.
- Avoid duplicated domain logic across components.
- Avoid excessive generic abstraction ("one-size-fits-all" components).

---

## 13. Data Visualization Boundary

Visualization components may transform authoritative data into visual representations.

**Visualization components must not:**

- Calculate trust (potential_kw, expected_kw, trusted_kw, confidence).
- Calculate optimization decisions (x[i,t]).
- Invent metrics.
- Reinterpret domain truth.
- Manufacture "AI insights."
- Show fake real-time animation.
- Hide whether values are forecast, dispatched, simulated, verified, or learned.

**Visualization components may:**

- Format authoritative data into charts, tables, and status indicators.
- Provide comparison views (baseline vs. trust-aware).
- Show time-series of dispatched vs. delivered (using backend-provided values).
- Annotate events only when contract-supported.

Charts should consume prepared, meaningful data from the data-access boundary, not raw unprocessed values.

**Deferred:** Exact charting library, exact chart component inventory.

---

## 14. Dispatch Flow Architecture

The Dispatch page is a decision/simulation interface. The frontend does not implement the optimizer, simulator, or verifier.

**Conceptual frontend flow:**

```
Load recommendation
        ↓
Present recommendation (read-only)
        ↓
User requests simulation (Simulate Dispatch)
        ↓
Submit simulation request through API boundary
        ↓
Show simulation-running state
        ↓
Receive simulation result
        ↓
Present result (actual response, verification preview, constraint adherence)
```

**Rules:**

- The frontend loads and displays the recommended dispatch plan. It does not calculate or modify it.
- The frontend triggers simulation via the API boundary. It does not simulate locally.
- The frontend shows the simulation result. It does not re-derive verification or trust updates.
- The frontend shows constraint check results from the backend. It does not re-implement constraint feasibility.
- The frontend must display contract-provided rationale only. It must not invent solver-level explanations.

**Deferred:** Exact backend endpoints for loading recommendation and triggering simulation.

---

## 15. Experiments Flow Architecture

Experiments consume experiment results produced by the simulation, experiments, and backend systems.

**Frontend responsibilities:**

- Load and present baseline vs. trust-aware comparison.
- Present primary and secondary metrics.
- Present delivery visualization (dispatched vs. delivered).
- Present event replay across the canonical loop.
- Present trust update outcomes where backend contract provides them.

**Rules:**

- The frontend does not implement experiment methodology.
- The frontend does not run the baseline vs. trust-aware comparison.
- The frontend does not calculate metrics.
- The frontend does not declare the winner; it presents backend-provided outcomes.

**Deferred:** Exact backend endpoints for experiment results loading.

---

## 16. Dependency Direction

Dependencies must flow in one direction:

```
UI Components / Pages
        ↓ (consume)
Feature / View Logic
        ↓ (consume)
Data-Access / API Boundary
        ↓ (consume)
Backend contracts (read-only reference)
```

**Dependency rules:**

- Frontend depends on backend contracts (REST API, per CONTRACTS.md).
- UI components depend on feature logic and view state; they do not depend on backend transport.
- Feature logic depends on data-access; data-access does not depend on UI components.
- No circular dependencies.
- Backend dependencies (domain, AI/ML, optimization, simulation) remain outside the frontend.

---

## 17. Testing Architecture

Defined at a conceptual layer (specific frameworks are deferred):

### Unit

For:

- Presentation-only transformation utilities (formatting kW, kWh, confidence labels).
- Simple interaction logic (drawer toggle, filter apply).
- Pure data-shape normalization functions.

Scope rule:

- Do not test implementation details of domain intelligence (that is not in the frontend).

### Component

For:

- Component rendering.
- State rendering (loading, empty, error, success).
- Interaction behavior.
- Accessibility-critical behavior.

Rule:

- Components must be testable in isolation from backend transport. The mock/API adapter duality enables this.

### Integration

For:

- Feature + adapter behavior.
- Page-level data loading and state transitions.
- API boundary behavior.

### End-to-End

For the critical product journey only:

- Navigation through the four pages.
- Resource portfolio viewing.
- Opening a resource detail drawer.
- Dispatch recommendation review.
- Triggering simulation.
- Dispatch simulation result display.
- Baseline vs. trust-aware experiment comparison.

Rule:

- Do not write E2E tests for every edge case. Tests should cover the core journey and critical state transitions.
- E2E tests should run against mock adapters initially and optionally against a real backend later.

**Deferred:** Exact testing frameworks, mock testing utilities.

---

## 18. Performance

MVP performance principles (no premature optimization):

**Prioritize:**

- Fast initial application load.
- Efficient rendering of the resource portfolio table.
- Reasonable rendering of comparison charts.
- Avoiding unnecessary re-renders of dense tables and charts.
- Efficient data fetching (no redundant requests when navigating between views of the same scenario).

**Do NOT:**

- Introduce complex performance infrastructure without evidence.
- Prematurely implement pagination unless portfolio scale requires it.
- Prematurely implement virtual scrolling unless portfolio scale requires it.

**Deferred:** Exact performance budgets, exact virtualization strategy, exact lazy-loading boundaries.

---

## 19. Accessibility

Architecture must support the design system's accessibility requirements:

- Semantic HTML and component composition.
- Keyboard navigation through primary workflows (four-page navigation, drawer open/close, filter).
- Visible focus states for interactive elements.
- Focus management when opening/closing drawers.
- Non-color-only status communication (states must also use text/labels/patterns).
- Meaningful labels for metrics and controls.
- Accessible tables with preserved headers and associations.
- Accessible loading/error/empty states.
- Accessible data visualizations (where applicable, provide text alternatives).

**Deferred:** Exact accessibility acceptance checklist and testing tooling.

---

## 20. Responsiveness

Respect the design system priorities:

1. Desktop — primary experience.
2. Tablet — fully supported.
3. Mobile — responsive and usable, but secondary.

Architecture should allow layouts to adapt without creating a separate mobile codebase.

Required information must remain available on smaller screens; it may be reorganized, summarized, or moved behind detail interactions.

Tables on mobile may transform into compact row groups only if required values remain visible and comparable.

**Deferred:** Exact breakpoints.

---

## 21. Build / Integration Strategy

The frontend is a React + TypeScript application.

**Conceptual build targets:**

- Development build (with mock data adapters enabled for early development).
- Production build (with real API adapter).

**Integration:**

- Initially, the frontend may use mock adapters so it can run standalone before backend integration.
- When the backend is ready, the same frontend-facing data interface is satisfied by the API adapter.
- Integration is verified via the frontend/backend handoff: API contract conformance.

**Do NOT create:**

- A separate mobile app codebase.
- A separate native app.
- Micro-frontend build pipeline.

**Deferred:** Exact build tool, exact deployment target, exact dev server configuration.

---

## 22. Security

Frontend security responsibilities (without inventing production infrastructure):

- Do not expose secrets, API keys, or credentials in frontend source code.
- Do not trust client-side validation as authoritative; backend remains authoritative.
- Treat all backend data as untrusted until normalized through the contract boundary.
- Safely handle and surfacing API errors without leaking internals.
- Avoid unsafe rendering of any external or user-provided content.

Production authentication/authorization architecture remains deferred (per PROJECT.md MVP scope and NAMING_AND_CONVENTIONS.md security boundary).

**Deferred:** Exact production authentication, exact authorization model, exact CSP policy.

---

## 23. What This Architecture Must NOT Do

Explicitly prohibit:

- Implementing backend domain logic in frontend code.
- Duplicating trust, optimization, simulation, verification, or learning logic.
- Inventing domain fields not in the contracts.
- Faking real-time data or real-time WebSocket behavior in MVP.
- Inventing API endpoints.
- Scattering direct HTTP calls across UI components.
- Creating giant global stores without a demonstrated need.
- Introducing speculative abstraction layers.
- Prematurely locking the scenario-selection interaction.
- Prematurely locking JSON field naming (snake_case vs camelCase).
- Prematurely locking exact state enums from backend.
- Inventing "AI" or "smart" behavior in the frontend.
- Creating fake live-control semantics.

---

## 24. Deferred Technical Decisions

The following are explicitly unresolved and must not be invented in this document:

| Decision | Status |
|----------|--------|
| Exact folder/file structure | DEFERRED |
| Exact routing library | DEFERRED |
| Exact state-management approach | DEFERRED |
| Exact API client library | DEFERRED |
| Exact form library | DEFERRED |
| Exact testing frameworks and tools | DEFERRED |
| Exact charting library | DEFERRED |
| Exact component library/UI primitives | DEFERRED |
| Exact icon library | DEFERRED |
| Exact build tool | DEFERRED |
| Exact deployment target | DEFERRED |
| API JSON naming convention (snake_case vs camelCase) | PENDING (per NAMING_AND_CONVENTIONS.md) |
| Exact endpoint names | DEFERRED |
| API versioning convention | DEFERRED |
| Pagination strategy | DEFERRED |
| Exact simulation-state canonical values | TBD (per NAMING_AND_CONVENTIONS.md) |
| Exact dispatch-state canonical values | TBD (per NAMING_AND_CONVENTIONS.md) |
| Exact experiment-run-state canonical values | TBD (per NAMING_AND_CONVENTIONS.md) |
| Exact scenario-selection interaction | DEFERRED |
| Exact experiment/event detail interaction | DEFERRED |
| Exact loading/skeleton pattern | DEFERRED |
| Exact breakpoint values | DEFERRED |
| Exact accessibility checklist/tooling | DEFERRED |
| Production authentication implementation | DEFERRED |
| Real-time / WebSocket architecture | DEFERRED |
| Exact state management library choice | DEFERRED |

These decisions do not block the architecture from being defined; they are deferred to the implementation phase.

---

## 25. Architectural Principles

1. **Product boundaries before code boundaries.** The four-page product structure drives the architecture.
2. **Contracts before UI assumptions.** The frontend is built against contract shapes, not invented data.
3. **Backend/domain intelligence remains authoritative.** The frontend presents, never derives authoritative domain behavior.
4. **Mock and real data share a stable frontend boundary.** No component distinguishes mock from real.
5. **UI state is not domain truth.** Local interaction state must not become a source of domain authority.
6. **Features own their interactions.** Feature logic lives close to the feature it serves.
7. **Shared abstractions require demonstrated reuse.** No speculative global layers.
8. **Visualizations explain data; they do not create domain meaning.**
9. **Defer specific tooling until implementation.** Define structure and boundaries; do not lock libraries prematurely.
10. **Keep the MVP architecture simple.** Add complexity only when a real requirement demands it.

---

## 26. Relationship to Other Documents

This document bridges the gap between:

```
FRONTEND_PRODUCT_SPEC.md     (WHAT — locked product scope)
        ↓
FRONTEND_DESIGN_SYSTEM.md    (HOW it looks and feels — presentation rules)
        ↓
FRONTEND_ARCHITECTURE.md     (HOW it is technically structured — this document)
        ↓
FRONTEND_COMPONENTS.md       (concrete UI vocabulary — deferred)
        ↓
Implementation               (actual React/TypeScript code — deferred)
```

This document does not create React components, source files, or any implementation artifacts.

---

## 27. Current Status

LOCKED

Frontend product and design are locked (FRONTEND_PRODUCT_SPEC.md, FRONTEND_DESIGN_SYSTEM.md). This architecture document defines frontend technical boundaries. Most implementation-level decisions (exact libraries, folder structure, package versions, exact endpoints) remain deferred.

---

## FILES CONSULTED

1. `frontend/FRONTEND_PRODUCT_SPEC.md` — frontend product scope, page inventory, hierarchy, data boundary, MVP boundary, states, and deferred decisions.
2. `frontend/FRONTEND_DESIGN_SYSTEM.md` — operational visual principles, color/semantics roles, typography roles, surfaces/tables/drawers, visualization rules, state representation, responsive/accessible principles, anti-AI-slop rules, and explicitly deferred visual decisions.

---

## Document Status

LOCKED — FRONTEND ARCHITECTURE v1.0

*End of FRONTEND_ARCHITECTURE.md*
