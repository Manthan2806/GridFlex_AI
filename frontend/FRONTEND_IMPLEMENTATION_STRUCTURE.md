# FRONTEND IMPLEMENTATION STRUCTURE

## 1. Purpose

This document defines the concrete implementation structure for the GridFlex AI frontend. It bridges the gap between the locked frontend specifications (PRODUCT_SPEC.md, DESIGN_SYSTEM.md, ARCHITECTURE.md, COMPONENTS.md) and actual source code. This is a blueprint for F1 (Shell + Navigation + Overview) and subsequent phases.

---

## 2. Relationship to Locked Frontend Documents

```
FRONTEND_PRODUCT_SPEC.md     (WHAT — locked product scope, page inventory, hierarchy, data boundary, states)
FRONTEND_DESIGN_SYSTEM.md    (HOW it looks and feels — locked visual design system, colors, typography, components)
FRONTEND_ARCHITECTURE.md     (HOW it is technically structured — locked layers, patterns, boundaries)
FRONTEND_COMPONENTS.md       (The conceptual UI vocabulary — locked 39-component inventory)
        ↓
FRONTEND_IMPLEMENTATION_STRUCTURE.md (WHERE each file lives, how they connect)
        ↓
Implementation (actual React/TypeScript code — F1, F2, F3, F4, F5, F6)
```

---

## 3. Implementation Principles

### 3.1 Layered Architecture
- **Presentation Layer**: React components, pages, visualization
- **Feature Layer**: Page composition, feature-specific logic
- **State Layer**: View/UI state management
- **Data Layer**: API adapters, normalization, type contracts

### 3.2 Separation of Concerns
- UI components NEVER call `fetch()` or `axios()` directly
- All HTTP calls go through data-access boundary
- Mock and real API share the same frontend interface
- No backend/domain logic in presentation components

### 3.3 Team Ownership
- **T1 (Frontend)** owns `frontend/src/` entirely
- **T2 (Backend)** owns `backend/`
- **T3 (AI/ML)** owns `ai_ml/`
- **T4 (Simulation/Experiments)** owns `simulation/`, `experiments/`
- Contract files are shared and require cross-team review

### 3.4 Mock ↔ Real Transition
- Same TypeScript types for mock and real data
- Adapter pattern: `src/data/adapters/mock/` and `src/data/adapters/api/`
- Environment variable to select adapter at build time
- No UI changes needed for mock→real transition

---

## 4. Final Folder Tree

```
frontend/
├── src/
│   ├── app/                      # Application root, global providers
│   │   ├── App.tsx               # Main App component with routing
│   │   ├── providers/            # Context providers, state managers
│   │   └── routes/               # Route definitions
│   │
│   ├── pages/                    # Four MVP pages (entry points)
│   │   ├── OverviewPage/
│   │   │   ├── OverviewPage.tsx
│   │   │   └── index.ts
│   │   ├── FlexibilityPage/
│   │   │   ├── FlexibilityPage.tsx
│   │   │   └── index.ts
│   │   ├── DispatchPage/
│   │   │   ├── DispatchPage.tsx
│   │   │   └── index.ts
│   │   └── ExperimentsPage/
│   │       ├── ExperimentsPage.tsx
│   │       └── index.ts
│   │
│   ├── features/                 # Page-specific composable logic
│   │   ├── overview/             # Overview composition, metrics logic
│   │   ├── flexibility/          # Portfolio management, resource logic
│   │   ├── dispatch/             # Dispatch workflow, simulation logic
│   │   └── experiments/          # Experiment comparison, metrics
│   │
│   ├── components/               # Shared UI components (from COMPONENTS.md)
│   │   ├── Shell/                # App Shell, Navigation, Header
│   │   ├── Indicators/           # Status, Metric displays
│   │   ├── Layout/               # Drawer, Data Table, Section Header
│   │   ├── Controls/             # Buttons, State Message
│   │   └── Scenario/             # Scenario Context, Simulation Mode Indicator
│   │
│   ├── visualization/            # Charts, comparison views, delivery viz
│   │   ├── charts/
│   │   └── comparison/
│   │
│   ├── data/                     # Data access layer (MOCK ↔ REAL API BOUNDARY)
│   │   ├── adapters/             # Mock and real API implementations
│   │   │   ├── mock/             # Contract-aligned mock data
│   │   │   └── api/              # Real backend API client
│   │   ├── types/                # Shared TypeScript types (contracts)
│   │   │   ├── api/              # API request/response shapes
│   │   │   ├── domain/           # Normalized frontend data models
│   │   │   └── ui/               # View-specific type helpers
│   │   ├── services/             # Normalization, transformation
│   │   └── queries/              # Query functions for data fetching
│   │
│   ├── hooks/                    # Custom React hooks
│   │   ├── useScenario.ts        # Scenario context hook
│   │   ├── useSimulation.ts        # Simulation lifecycle hook
│   │   ├── useExperiment.ts      # Experiment state hook
│   │   └── useApi.ts             # General API data hooks
│   │
│   ├── lib/                      # Utilities, constants, helpers
│   │   ├── constants.ts          # Status enums, constants
│   │   ├── utils.ts              # Formatting, date helpers
│   │   └── config.ts             # Environment-based config
│   │
│   ├── styles/                   # Design system implementation
│   │   ├── tokens/               # Design tokens (colors, spacing, etc.)
│   │   ├── components/           # Component-specific styles
│   │   └── global.css            # Global styles, reset
│   │
│   └── index.tsx                 # Application entry point
│
├── mocks/                        # Contract-aligned mock fixtures
│   ├── scenarios/
│   ├── resources/
│   └── fixtures.ts               # Mock data factory functions
│
├── tests/                        # Testing structure
│   ├── unit/
│   ├── component/
│   ├── integration/
│   └── e2e/
│
└── env/                          # Environment configuration templates
    ├── .env.example
    └── .env.development
```

---

## 5. Directory Responsibilities

| Directory | Responsibility | May Contain | Must NOT Contain |
|-----------|---------------|-------------|------------------|
| `app/` | Application root, providers, routing setup | App entry point, global providers, route config | UI components, business logic |
| `pages/` | Four page entry points | Page components, page-level composition | Detailed component logic, data fetching |
| `features/` | Page-specific domain logic | Feature composition, state management, use cases | UI presentation, generic utilities |
| `components/` | Shared UI vocabulary (39 conceptual components) | React components matching COMPONENTS.md | Page-specific logic, CSS-in-JS abstractions |
| `visualization/` | Charts and data visualizations | Chart components, comparison views | Business logic, data fetching |
| `data/` | Mock ↔ Real API boundary | Adapters, types, normalization services | React components, UI logic |
| `adapters/mock/` | Mock implementation | Static fixtures, mock functions | Real API calls, HTTP clients |
| `adapters/api/` | Real API implementation | Axios/fetch wrappers, real endpoints | Mock data definitions |
| `types/` | Shared TypeScript contracts | API shapes, domain models | CSS, inline styles |
| `services/` | Data transformation | Normalization functions, mappers | HTTP requests directly |
| `hooks/` | React data hooks | useScenario, useSimulation, useExperiment | State management libraries |
| `lib/` | Utilities and constants | Helper functions, environment utils | Components, CSS |
| `styles/` | Design system implementation | Tokens, component styles, global CSS | Business logic |
| `mocks/` | Fixture data files | Scenario JSON, resource fixtures | API client code |
| `tests/` | Test files | Unit, component, integration, e2e tests | Production code |

---

## 6. Page Structure

Each page follows the pattern defined in FRONTEND_PRODUCT_SPEC.md sections E-H:

### 6.1 Overview Page (`/overview`)
**File**: `src/pages/OverviewPage/OverviewPage.tsx`

Composes:
- PageHeader (with Scenario Context)
- System Snapshot (Metric Display components)
- Renewable Opportunity Summary
- Flexibility State Summary
- Next Dispatch Summary
- Recent Activity Summary

### 6.2 Flexibility Page (`/flexibility`)
**File**: `src/pages/FlexibilityPage/FlexibilityPage.tsx`

Composes:
- PageHeader
- Portfolio Snapshot (Metric Displays)
- Resource Search / Filters
- Resource Portfolio/Table (Data Table + Resource Row)
- Resource Detail Drawer (Drawer component)
- Constraint Indicators (Status Indicator)

### 6.3 Dispatch Page (`/dispatch`)
**File**: `src/pages/DispatchPage/DispatchPage.tsx`

Composes:
- PageHeader (with Scenario Context)
- Renewable Opportunity Detail
- Relevant Flexibility (Subset of portfolio with trust)
- Recommended Dispatch (x[i,t])
- Decision Rationale
- Constraint Check
- Simulation Action (Button)
- Simulation Result

### 6.4 Experiments Page (`/experiments`)
**File**: `src/pages/ExperimentsPage/ExperimentsPage.tsx`

Composes:
- Experiment Context
- Experiment Summary
- Baseline vs Trust-Aware Comparison
- Outcome Metrics
- Delivery Visualization
- Event Replay
- Trust Update

**Key Principle**: Pages are composition-only. They consume data from hooks (which call adapters) and compose shared components.

---

## 7. Shared Component Structure

Components map to the 39 conceptual components from COMPONENTS.md:

### 7.1 Shell Group (Border/Frame)
- `AppShell.tsx` — Layout wrapper, nav container
- `PrimaryNavigation.tsx` — 4-page nav items
- `PageHeader.tsx` — Page title + context

### 7.2 Scenario Group
- `ScenarioContext.tsx` — Active scenario display
- `SimulationModeIndicator.tsx` — SIMULATION badge/notice

### 7.3 Presentation Group
- `MetricDisplay.tsx` — Value + label + unit
- `StatusIndicator.tsx` — State badges (available/dispatched/etc)
- `StateMessage.tsx` — Loading/empty/error/success
- `Action/Button.tsx` — Interactive controls

### 7.4 Layout Group
- `DataTable.tsx` — Resource portfolio table
- `Drawer.tsx` — Detail overlay
- `SectionHeader.tsx` — Section labels
- `ResourceFilters.tsx` — Filter controls

**Note**: "Conceptual component ≠ implementation file". Multiple related concepts may live in a single file for tight coupling, or be split if complexity warrants.

---

## 8. Feature Boundaries

Frontend features MAY own:
- page composition
- UI/view state
- interaction state
- filtering/search state
- selected resource state
- simulation lifecycle presentation state
- experiment replay interaction state
- request orchestration through the data boundary
- display-only formatting/aggregation where explicitly presentation-only

Frontend features MUST NOT own authoritative:
- dispatch optimization
- dispatch recommendations
- constraint validation
- trust calculation
- confidence calculation
- flexibility estimation
- simulation
- verification
- learning
- experiment outcome calculation

These remain authoritative outside the frontend (backend, AI/ML, optimization, simulation, verification, learning, experiment frameworks).

```
features/
├── overview/       → Page composition, UI/view state, display-only formatting of authoritative metrics
├── flexibility/    → Portfolio state, resource selection, drawer state, filtering/search state
├── dispatch/       → Page composition, UI/view state, presentation of authoritative dispatch recommendation, simulation lifecycle presentation state
└── experiments/    → Page composition, UI/view state, presentation of authoritative baseline/trust-aware comparison, experiment replay interaction state
```

Each feature directory contains:
- `types.ts` — Feature-specific view types (presentation-only)
- `useXxx.ts` — Hook for feature data/state (via data boundary)
- `xxxSlice.ts` or `xxxStore.ts` — Feature state (if local)
- `xxxAPI.ts` — Feature request orchestration through the data boundary
- `xxxUtils.ts` — Feature helper functions (display-only transformations)

---

## 9. Routing Structure

**File**: `src/app/routes/Router.tsx`

```typescript
// Four primary routes only
const routes = [
  { path: '/', element: <OverviewPage /> },
  { path: '/overview', element: <OverviewPage /> },
  { path: '/flexibility', element: <FlexibilityPage /> },
  { path: '/dispatch', element: <DispatchPage /> },
  { path: '/experiments', element: <ExperimentsPage /> },
  { path: '*', element: <Navigate to="/" replace /> }
]
```

- **Entry**: `src/index.tsx` renders Router
- **Deep linking**: Enabled by React Router or equivalent
- **Unknown routes**: Redirect to Overview

---

## 10. State Ownership

### 10.1 Server/Domain State (Owned by Backend, Consumed)
- `potential_kw`, `expected_kw`, `trusted_kw`, `confidence`
- `x[i,t]` dispatch plans
- Renewable forecasts
- Simulation results
- Verification outcomes

### 10.2 UI/View State (Frontend-Owned)
- `selectedResourceId` — Currently selected resource in drawer
- `isDrawerOpen` — Resource detail drawer state
- `filters` — Type, status, location filters
- `searchQuery` — Text search by resource ID
- `simulationLifecycle` — idle/running/complete/failed
- `experimentLifecycle` — ready/running/complete/failed
- `scenarioContext` — Active scenario ID and mode
- `isLoading` — Per-request loading states

### 10.3 State Management Choice
**Decision**: Start with React Context + useReducer for UI state, local component state for isolated interaction state. Global store (Redux/Zustand) deferred until demonstrable need.

---

## 11. Data / Contract Boundaries

### 11.1 Type Ownership Model

There is **one** type authority in the frontend. Types are not duplicated across `core/`, `data/`, or feature directories.

- **API-facing types** (`src/data/types/api/`): Request/response shapes that mirror backend contracts. These are the only types that know about API wire formats.
- **Normalized domain types** (`src/data/types/domain/`): Frontend-facing data models after normalization. This is the single source of truth for domain data consumed by features and components.
- **View-specific types** (`src/data/types/ui/`): Presentation-only types (e.g., table row display, filter options). These must not duplicate or compete with domain types.

`src/core/types.ts` is **not** part of the structure. Domain types live in `src/data/types/domain/` only. No type duplication exists between `core/` and `data/`.

### 11.2 API Types (`src/data/types/api/`)
- `resources.ts` — Resource list, detail shapes
- `scenarios.ts` — Scenario configuration, results
- `dispatch.ts` — Dispatch plan, simulation request/response
- `experiments.ts` — Experiment results, metrics

### 11.3 Normalized Domain Types (`src/data/types/domain/`)
- `flexibilityResource.ts` — Normalized FlexibilityResource
- `trustState.ts` — Normalized trust state view
- `dispatchPlan.ts` — Normalized dispatch plan view
- `simulationResult.ts` — Normalized simulation output

### 11.4 Normalization Services (`src/data/services/`)
- `resourceNormalizer.ts` — Maps API response to domain types
- `dispatchNormalizer.ts` — Normalizes dispatch plan + rationale
- `experimentNormalizer.ts` — Prepares comparison data

**Key**: All external data passes through normalization BEFORE reaching components.

---

## 12. Mock ↔ Real API Structure

```
src/data/adapters/
├── mock/
│   ├── scenarios.ts      # Mock scenario factory
│   ├── resources.ts      # Mock resource factory
│   ├── dispatch.ts       # Mock dispatch/simulation
│   └── experiment.ts     # Mock experiment results
├── api/
│   ├── apiClient.ts      # Axios instance, env-based base URL
│   ├── resources.ts      # Real endpoint implementations
│   ├── scenarios.ts
│   └── index.ts
└── types.ts              # Shared interface (both implementations)
```

### 12.1 Selection Mechanism
```typescript
// src/lib/config.ts
export const isMockMode = import.meta.env.VITE_MOCK_MODE === 'true'

// src/data/index.ts
import * as mock from './adapters/mock'
import * as api from './adapters/api'

export const apiClient = isMockMode ? mock : api
```

### 12.2 Shared Interface (`src/data/adapters/types.ts`)
All functions in both mock and api implementations return identical types. TypeScript compilation fails if they diverge.

---

## 13. Normalization / Mapping Location

**File Location**: `src/data/services/normalizers/`

Files:
- `resourceNormalizer.ts` — Resource data shaping
- `dispatchNormalizer.ts` — Dispatch plan shaping
- `simulationNormalizer.ts` — Result shaping
- `experimentNormalizer.ts` — Comparison data shaping

**Responsibilities**:
- Map API field names to canonical names
- Convert units (kW ↔ kWh)
- Handle missing/null fields safely
- Combine multiple API calls into single domain view
- Add computed display-only aggregates (clearly documented)

**NOT responsible for**:
- Calculating trust, confidence
- Optimizing dispatch
- Simulating behavior
- Verifying results
- Learning updates

---

## 14. Configuration Boundary

**File**: `src/lib/config.ts`

```typescript
const config = {
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
  },
  mock: {
    enabled: import.meta.env.VITE_MOCK_MODE === 'true'
  },
  environment: {
    isDevelopment: import.meta.env.NODE_ENV === 'development',
    isProduction: import.meta.env.NODE_ENV === 'production'
  }
}
```

**Environment Variables**:
- `VITE_API_BASE_URL` — Backend base URL (development: http://localhost:8000)
- `VITE_MOCK_MODE` — Set to "true" for mock mode, omitted for real API

---

## 15. Styling Structure

**Root Directory**: `src/styles/`

### 15.1 Design Tokens (`src/styles/tokens/`)
Derived from locked FRONTEND_DESIGN_SYSTEM.md:
- `colors.ts` — Burgundy (#6B1E2E), Warm Cream (#F1E7D6), neutrals, semantic colors
- `typography.ts` — Inter/Space Grotesk/JetBrains Mono scales
- `spacing.ts` — 4px grid system
- `radii.ts` — Surface corner radiuses
- `layers.ts` — Z-index layer definitions

### 15.2 Component Styles (`src/styles/components/`)
One file per major component group. Uses CSS Modules or styled-components.

### 15.3 Global Styles (`src/styles/global.css`)
- CSS reset
- Base typography
- Semantic color utilities

---

## 16. Responsive Structure

- **Mobile queries**: Start with progressive enhancement
- **Breakpoint placeholders**: Document as DEFERRED — exact values TBD in implementation
- **Components**: Use CSS Grid/Flexbox with responsive tokens
- **Tables**: Transform on mobile (compact rows) if space constraints require

---

## 17. Testing Structure

```
tests/
├── unit/              # Pure functions, utils, normalizers
├── component/         # Component rendering, state responses
├── integration/       # Feature + adapter integration
└── e2e/               # Core journey tests (Playwright/Cypress style)
```

**Test Categories per Architecture**:
- Unit: Transformation utilities, display formatting
- Component: Render states, interaction behavior
- Integration: Feature + adapter behavior, page data flow
- E2E: Navigation through 4 pages, simulation trigger, experiment comparison

---

## 18. Error / Loading / Empty State Structure

**Shared Components** (from COMPONENTS.md):
- `StateMessage.tsx` — Wrapper for loading/empty/error/success
- `LoadingSpinner.tsx` — Shared loading primitive
- `ErrorMessage.tsx` — Error state display
- `EmptyState.tsx` — Configurable empty messaging

**Usage Pattern**:
```tsx
const { data, isLoading, error } = useResources()

if (isLoading) return <StateMessage type="loading" />
if (error) return <StateMessage type="error" message={error.message} />
if (!data || data.length === 0) return <StateMessage type="empty" />
return <DataTable data={data} />
```

---

## 19. Team Ownership / Merge Safety

### 19.1 Frontend-Owned Files
```
frontend/src/
frontend/tests/
frontend/mocks/
frontend/styles/
frontend/env/
```

### 19.2 Shared Contract Files
```
frontend/src/data/types/           ← T1 (but touched with backend changes)
CONTRACTS.md                       ← Requires T1 + T2 review
NAMING_AND_CONVENTIONS.md          ← Requires all-team review
```

### 19.3 File Ownership Matrix
| File/Directory | Owner | Coordination Required |
|----------------|-------|----------------------|
| `frontend/src/*` | T1 | When modifying contracts/types |
| `frontend/src/data/adapters/mock/*` | T1 | Backend contract changes |
| `frontend/src/data/types/*` | T1 | Contract schema changes |
| `FRONTEND_COMPONENTS.md` | T1 | For component vocabulary |
| `FRONTEND_ARCHITECTURE.md` | T1 | For technical architecture |
| `CONTRACTS.md` section 8.6 | T1 + T2 | API changes |
| `NAMING_AND_CONVENTIONS.md` | T1 + T2 + T3 | Field naming decisions |

### 19.4 Integration Handoff

When backend is ready:

1. The frontend **selects** the real API adapter by setting `VITE_MOCK_MODE=false` in configuration.
2. The mock adapter remains available in the codebase for development and testing.
3. Run contract validation tests to verify conformance between mock and real implementations.
4. No UI/page/component rewrite should be necessary — the stable frontend-facing interface is shared by both implementations.

The intended architecture is:

```
UI
 ↓
stable frontend-facing interface
 ↓
adapter selection
 ├── Mock adapter (VITE_MOCK_MODE=true)
 └── Real API adapter (VITE_MOCK_MODE=false)
```

The environment/configuration determines which implementation is active. Integration means **selecting** the real adapter and validating contract conformance, not deleting or replacing the mock adapter.

---

## 20. Implementation Phase Mapping

| Phase | Description | Files Created |
|-------|-------------|---------------|
| **F1** | Shell + Navigation + Overview | `app/*`, `components/Shell/*`, `pages/OverviewPage/*`, page-specific visual components |
| **F2** | Flexibility | `pages/FlexibilityPage/*`, `features/flexibility/*`, Resource portfolio components |
| **F3** | Dispatch | `pages/DispatchPage/*`, `features/dispatch/*`, dispatch-related visualization |
| **F4** | Experiments | `pages/ExperimentsPage/*`, `features/experiments/*`, comparison visualization |
| **F5** | Backend Integration | `data/adapters/api/*`, contract types, real endpoint integration |
| **F6** | Validation + Polish | Responsive refinement, accessibility, edge case handling |

---

## 21. Deferred Decisions

| Decision | Rationale | When to Decide |
|----------|-----------|----------------|
| TypeScript props interfaces | Implementation | Component design phase |
| Tailwind vs CSS Modules | Implementation | Styling toolkit decision |
| State management library | Need-based | When local/context insufficient |
| Routing library | Implementation | F1 setup |
| Testing framework | T1 decision | Pre-F5 |
| Charting library | F1/F2 planning | When visualization needed |
| Breakpoint values | Design system phase | Responsive implementation |
| Scenario selection UI | Interaction design | After F4, before F5 |
| Experiment detail pattern | Product design | F4 iteration |
| Exact import paths | Implementation | During F1 (structure is approved) |

The overall structure (folder layout, file responsibilities, naming conventions) is now approved. Implementation-level details such as exact import paths and file naming within approved directories remain flexible during F1.

---

## 22. Final Readiness Checklist

- [x] Matches locked PRODUCT_SPEC (4 pages, data boundary, states)
- [x] Matches locked DESIGN_SYSTEM (colors, typography, components)
- [x] Matches locked ARCHITECTURE (layers, adapter pattern, mock/real boundary)
- [x] Maps to locked COMPONENTS vocabulary (39 conceptual components)
- [x] Exactly four MVP pages (no additional pages)
- [x] No invented APIs or backend fields
- [x] No duplicated backend intelligence
- [x] UI never directly depends on HTTP/URLs
- [x] Mock and real API share stable frontend interface
- [x] Normalization boundary is explicit and isolated
- [x] Feature ownership is clear for team development
- [x] Team ownership documented for merge safety
- [x] Implementation supports F1 → F6 phase order

---

## 23. Document Status

This document is **LOCKED** and serves as the final planning document before source-code implementation.

**Author**: [To be signed]  
**Date**: 2026-09-12  
**Status**: LOCKED — FRONTEND IMPLEMENTATION STRUCTURE v1.0

F1 (Shell + Navigation + Overview Foundation) implementation can begin immediately upon this document being approved.

---

*End of FRONTEND_IMPLEMENTATION_STRUCTURE.md*