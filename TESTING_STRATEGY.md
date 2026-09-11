# TESTING STRATEGY

## Purpose

Define the testing philosophy, unit testing, integration testing, end-to-end testing, simulation validation, benchmarking, real-data validation, reproducibility, and quality gates for GridFlex AI.

## Scope

This document governs how the system will be tested across all layers. It distinguishes clearly between different kinds of validation, including the critical distinction between real-data validated and production validated.

## Authority

This document is the authoritative source for testing philosophy, unit testing, integration testing, end-to-end testing, simulation validation, benchmarking, real-data validation, reproducibility, and quality gates. Other documents must not redefine testing requirements.

## Current Status

DRAFT

---

## 1. Testing Philosophy

Testing validates:

1. **Correctness** — the system does what it is supposed to do per CONTRACTS.md, DOMAIN_MODEL.md, and ALGORITHM_SPEC.md.
2. **Reliability** — the system produces consistent, trustworthy results.
3. **Core hypothesis** — representing flexibility with actual constraints and historical response reliability produces more reliable dispatch decisions under uncertainty than theoretical capacity alone (per EXPERIMENT_SPEC.md).

The testing strategy is designed to answer:

- Does theoretical flexibility differ from trusted flexibility for each resource type?
- Does trust affect dispatch? (Do baseline and trust-aware schedulers produce different plans?)
- Does verification update trust? (Do post-verification estimates differ from pre-verification?)
- Is the simulation physically plausible?
- Are results reproducible?

---

## 2. Testing Layers

### 2.1 Unit Testing

| Aspect | Detail |
|---|---|
| **Scope** | Individual functions and classes in isolation |
| **Targets** | Domain model invariants, constraint extraction, trust computation helpers, optimization formulation, simulation device models, utility functions |
| **Speed** | Fast, deterministic |
| **External dependencies** | None |
| **Coverage goal** | All domain invariants; all trust computation branches; all constraint validation paths |
| **Who owns** | Each team owns unit tests for their components |

**Specific test targets:**

- Domain invariants (per DOMAIN_MODEL.md section 6): availability window, power limits, energy requirement, trust ordering, state consistency, duration, feeder capacity, deadline.
- Trust pipeline: potential → expected → trusted ordering invariant.
- Confidence bounds: confidence ∈ [0.0, 1.0].
- x[i,t] constraint satisfaction (per ALGORITHM_SPEC.md section 6).
- Simulation device models produce physically plausible outputs.
- Scenario generation produces valid scenarios.

### 2.2 Integration Testing

| Aspect | Detail |
|---|---|
| **Scope** | Interactions between modules |
| **Targets** | Backend ↔ AI/ML, Backend ↔ Optimization, Backend ↔ Simulation, Backend ↔ Persistence |
| **Contract basis** | CONTRACTS.md |
| **Speed** | Medium (may use in-memory databases, mock services) |
| **External dependencies** | Minimal (mocked where possible) |
| **Who owns** | Backend team leads integration tests; contributing teams provide test fixtures |

**Specific integration tests:**

- Estimation interface: resource representation → confidence + trust output conforms to model I/O contract.
- Optimization interface: trusted flexibility + constraints → dispatch plan conforms to output contract.
- Simulation interface: scenario + dispatch plan → actual response conforms to output contract.
- Persistence: data can be stored and retrieved correctly.

### 2.3 End-to-End Testing

| Aspect | Detail |
|---|---|
| **Scope** | Complete user flows through the system |
| **Targets** | Scenario configuration → simulation run → results → dispatch review |
| **Loop coverage** | Full loop: Observe → Represent → Estimate → Trust → Match → Dispatch → Simulate → Verify → Learn |
| **Speed** | Slow (full simulation runs) |
| **External dependencies** | All components integrated |
| **Who owns** | Backend team orchestrates; all teams contribute test scenarios |

### 2.4 Simulation Validation

| Aspect | Detail |
|---|---|
| **Scope** | Physical plausibility of simulation output |
| **Targets** | Device behavior, synthetic data consistency, scenario evolution |
| **Validation criteria** | Simulated device behavior is consistent with DOMAIN_MODEL.md constraints; synthetic resources satisfy domain invariants; scenarios evolve correctly at 15-minute resolution |
| **Who owns** | Simulation team leads; AI/ML and Domain contribute |

### 2.5 Benchmarking (Baseline vs. Trust-Aware)

| Aspect | Detail |
|---|---|
| **Scope** | Comparison of baseline and trust-aware schedulers |
| **Reference** | EXPERIMENT_SPEC.md |
| **Metrics** | Renewable absorption, delivered flexibility error, overcommitment, constraint violations, deadline violations, rebound, actual/committed reliability |
| **Methodology** | Both schedulers on identical scenarios; statistical comparison |
| **Who owns** | AI/ML + Backend jointly; Experiment framework manages runs |

### 2.6 Real-Data Validation

| Aspect | Detail |
|---|---|
| **Scope** | Validation against real public/system-level energy data |
| **Targets** | Solar, weather, demand data plausibility; synthetic device behavior plausibility against known device characteristics |
| **Who owns** | Backend + AI/ML |

---

## 3. Real-Data Validated vs. Production Validated

This distinction is critical and must be maintained in all testing and reporting:

| Status | Definition | Achievable in MVP | Claimable? |
|---|---|---|---|
| **Real-Data Validated** | Checked against real public/system-level energy data and plausible synthetic device behavior | Yes | Yes, with caveats |
| **Production Validated** | Deployed and operated against real IoT hardware and real utility systems in a live environment | No | NEVER without explicit evidence |

**Rules:**

1. The project must never claim production validation without real deployment evidence.
2. Real-data validated status requires documented evidence of testing against real data.
3. Simulation success alone does NOT constitute real-data validation.
4. MVP results are reported as "simulation-first, real-data validated where tested."
5. Any report, presentation, or document that mentions validation status must specify which category applies.

---

## 4. Core Hypothesis Testing

The following tests specifically address the core hypothesis:

### 4.1 Theoretical Flexibility

- **Test:** For each resource type (EV, water heater, industrial), compute potential_kw and verify it matches theoretical maximum from physical constraints.
- **Pass criteria:** potential_kw = resource-rated maximum under ideal conditions.

### 4.2 Trusted Flexibility

- **Test:** For each resource type at representative time steps, compute trusted_kw and verify trusted_kw ≤ expected_kw ≤ potential_kw.
- **Pass criteria:** Trust ordering invariant holds; confidence ∈ [0, 1]; trusted differs from potential for at least some resources and time steps.

### 4.3 Trust Affects Dispatch

- **Test:** Run baseline (potential) and trust-aware (trusted) schedulers on identical scenario; compare dispatch plans.
- **Pass criteria:** At least one dispatch decision differs between schedulers (different x[i,t] values).

### 4.4 Verification Updates Trust

- **Test:** Run simulation with verification; compare pre-verification and post-verification trust estimates for each resource.
- **Pass criteria:** Post-verification trust estimates differ from pre-verification for at least some resources.

### 4.5 Learning Closes the Loop

- **Test:** Run multiple simulation cycles; verify that trust estimates in cycle N+1 are informed by verification outcomes in cycle N.
- **Pass criteria:** Trust estimates change in response to verification outcomes across cycles.

---

## 5. Reproducibility

| Requirement | Detail | Reference |
|---|---|---|
| Fixed seeds | All tests using randomness use fixed seeds | DATA_SPEC.md, EXPERIMENT_SPEC.md |
| Synthetic data provenance | Generator version, seed, parameters recorded | DATA_SPEC.md |
| Experiment provenance | Full provenance per run | EXPERIMENT_SPEC.md |
| Test environment documentation | Documented and versioned | This document |
| Deterministic results | Given same inputs and seeds, same outputs | Core principle |

---

## 6. Regression Testing

| Aspect | Detail |
|---|---|
| **Scope** | Detecting reintroduction of fixed bugs and regressions in behavior |
| **Targets** | Domain invariants, trust ordering, simulation consistency, optimization feasibility |
| **Trigger** | Any code change to domain, AI/ML, simulation, optimization, or backend |
| **Process** | Full unit test suite + affected integration tests on every change |
| **Who owns** | Each team maintains regression tests for their components |

---

## 7. Failure Testing

| Failure Type | Test | Expected Behavior | Reference |
|---|---|---|---|
| Optimization infeasible | Feed infeasible scenario | Infeasibility report returned; no silent degradation | ARCHITECTURE.md 14 |
| Estimation data insufficient | Feed resource with no history | Low confidence flag; conservative trust | ARCHITECTURE.md 14 |
| Simulation divergence | Feed unstable scenario | Divergence recorded; loop continues | ARCHITECTURE.md 14 |
| Backend unavailable | Stop backend during frontend request | Frontend shows last-known state | ARCHITECTURE.md 14 |
| Missing critical data | Feed resource with missing fields | Validation error before processing | CONTRACTS.md |
| Override during simulation | High override rate scenario | Actual response < dispatched; recorded in verification | EXPERIMENT_SPEC.md |
| Device failure during simulation | Failure event in scenario | Resource unavailable for affected period | EXPERIMENT_SPEC.md |

---

## 8. Data-Quality Testing

| Test | Scope | Pass Criteria |
|---|---|---|
| Unit consistency | All datasets | Consistent units within domain |
| Time resolution | Simulation inputs | 15-minute resolution (or documented exception) |
| Missing critical fields | All datasets | No missing critical fields without documented imputation |
| Geographic scope | All datasets | Explicitly recorded |
| Classification | All datasets | Labeled REAL/PUBLIC, SYNTHETIC, or COMPUTED |
| Synthetic reproducibility | Synthetic datasets | Generator version, seed, parameters recorded |
| Leakage check | Train/validation/test, scenarios | No leakage at resource or scenario level |
| Forecast-vs-actual boundary | Simulation inputs | Optimizer sees only forecasts; no actual future outcomes |

---

## 9. Model Validation

| Aspect | Test | Detail |
|---|---|---|
| Trust output bounds | All trust estimates | trusted ≤ expected ≤ potential; confidence ∈ [0,1] |
| Estimation accuracy (synthetic) | Against known behavior | Where ground truth is known (synthetic), estimate is within tolerance |
| Learning update direction | Post-verification trust | Trust updates in direction consistent with verification outcome |
| Confidence calibration | Confidence vs. actual reliability | If confidence = 0.8, actual reliability should be approximately 0.8 on average |
| No overfitting | Cross-validation | Model tested on held-out resources/scenarios |

---

## 10. Optimization Validation

| Aspect | Test | Detail |
|---|---|---|
| Constraint satisfaction | All dispatch plans | All hard constraints from ALGORITHM_SPEC.md satisfied |
| Objective improvement | Trust-aware vs. baseline | Trust-aware produces feasible solution where baseline may not (or vice versa for controlled comparison) |
| Infeasibility reporting | Infeasible scenarios | Clear diagnostic information provided |
| Determinism | Same input → same output | CP-SAT solution reproducible with same parameters |
| Objective value | Both schedulers | Objective values comparable in scale; not directly compared (different constraints) |

---

## 11. Performance Testing

| Aspect | Target | Priority |
|---|---|---|
| Single simulation step | Complete in ≤ 1 second | High |
| Full simulation (typical scenario) | Complete in ≤ 5 minutes | High |
| Optimization solve (typical problem) | Complete in ≤ 30 seconds | High |
| Estimation (single resource, single step) | Complete in ≤ 100ms | Medium |
| API response time | ≤ 2 seconds for standard queries | Medium |
| Concurrent scenario runs | TBD | Low (MVP) |

**Note:** Performance targets are PROPOSED and require confirmation based on actual resource scale.

---

## 12. Quality Gates

The following gates must be passed in order:

```
Unit tests pass
    ↓
Integration tests pass
    ↓
Domain invariant tests pass
    ↓
Simulation validation passes
    ↓
Benchmarking runs (baseline vs. trust-aware)
    ↓
End-to-end tests pass
    ↓
Experiment results recorded with provenance
```

**Absolute gates:**

| Gate | Rule |
|---|---|
| Unit tests | Must pass before integration tests run |
| Integration tests | Must pass before end-to-end tests run |
| Simulation validation | Must pass before benchmarking runs |
| No provenance | No experiment result may be reported without recorded provenance |
| Production validation | No claim of production validation without explicit evidence |
| Domain invariants | Must be satisfied for any persisted data |
| Trust ordering | Must hold for all trust states in any result |

---

## 13. Current Status

DRAFT
