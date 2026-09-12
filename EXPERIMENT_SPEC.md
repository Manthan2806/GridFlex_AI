# EXPERIMENT SPEC

## Purpose

Define the experimental methodology, baseline scheduler, trust-aware scheduler, scenario definitions, evaluation methodology, metrics, comparison methodology, reproducibility requirements, and hypotheses for GridFlex AI.

## Scope

This document governs how the system's scheduling approaches will be evaluated in simulation. It defines the comparison, scenarios, and metrics. It must not claim outcomes before running experiments.

## Authority

This document is the authoritative source for experimental methodology, baseline scheduler, trust-aware scheduler, scenario definitions, evaluation methodology, metrics, comparison methodology, reproducibility requirements, and hypotheses. Other documents must not redefine experimental parameters or metrics.

## Current Status

DRAFT

---

## 1. Evaluation Objective

Determine whether dispatching against trusted flexibility (accounting for operational constraints, historical response reliability, and current uncertainty) produces more reliable demand-response decisions under uncertainty than dispatching against theoretical (potential) flexibility alone.

---

## 2. Core Hypothesis

> If flexible loads are represented using actual operational constraints and historical response reliability rather than theoretical shiftable capacity alone, renewable-aligned demand shifting can make more reliable dispatch decisions under uncertainty.

---

## 3. Secondary Hypotheses

1. **H2:** Trust-aware scheduling reduces overcommitment and constraint violations compared to theoretical-capacity scheduling.
2. **H3:** Actual response outcomes change future trust estimates (verification closes the learning loop).
3. **H4:** Trust-aware scheduling produces more reliable renewable-aligned demand shifting, even if raw renewable absorption is not always higher.

**Important:** The experiment must not claim that trust-aware scheduling will always produce higher renewable absorption. The experiment is intended to determine whether trust-aware scheduling produces more reliable decisions under uncertainty.

---

## 4. Baseline vs. Trust-Aware

### 4.1 Baseline Scheduler

**Uses:** Theoretical flexibility (potential_kw) — the maximum shiftable capacity implied by resource physical limits, ignoring reliability and trust.

**What it represents:** Current practice of dispatching against static ratings or nameplate capacity.

### 4.2 Trust-Aware Scheduler

**Uses:** Trusted flexibility (trusted_kw) — the confidence-weighted deliverable capacity from the trust computation.

**What it represents:** GridFlex AI's approach of using trust-computed capacity for dispatch decisions.

### 4.3 Controlled Comparison

Both schedulers must run on equivalent scenarios with:

- Identical resource sets (same resources, same constraints).
- Identical forecasts (same solar, demand, weather).
- Identical disruption scenarios (same failures, overrides, rebound instances).
- Identical time horizon and resolution (15-minute).
- Same random seeds.

The only difference between the two schedulers is the capacity input: potential_kw (baseline) vs. trusted_kw (trust-aware).

---

## 5. Controlled Variables

| Variable | Control Method |
|---|---|
| Resource set | Same resources in both schedulers per scenario |
| Forecast data | Identical forecast inputs to both schedulers |
| Disruption instances | Same random seeds for failures, overrides, rebound |
| Time horizon | Same start and end times |
| Time resolution | 15-minute for both |
| Objective categories | Same categories (weights may differ as they are TBD) |
| Scenario parameters | Identical parameter sets |

---

## 6. Independent Variables

| Variable | Values |
|---|---|
| Scheduler type | Baseline (theoretical) vs. Trust-aware (trusted) |
| Confidence threshold | TBD (sensitivity analysis range) |
| Uncertainty level | Normal, elevated, extreme (scenario-dependent) |
| Override rate | Low, medium, high (scenario-dependent) |
| Renewable variability | Normal, high variance (scenario-dependent) |

---

## 7. Scenario Categories

Each scenario category must be parameterized and reproducible (fixed seeds, documented parameters).

| Category | Description | Purpose |
|---|---|---|
| **Normal operation** | Standard conditions, no disruptions | Baseline performance comparison |
| **Renewable forecast error** | Introduced solar forecast errors of varying magnitude | Test robustness to supply uncertainty |
| **User non-compliance** | Resource operators override dispatch commands at varying rates | Test robustness to demand-side uncertainty |
| **Device failures** | Resources become unavailable during dispatch | Test robustness to device unavailability |
| **Rebound** | Demand returns after shifting | Test accuracy of net demand reduction |
| **Combined uncertainty** | Multiple uncertainty sources active simultaneously | Test performance under realistic compound conditions |

### 7.1 Scenario Parameters

Each scenario category must document:

- Parameter values (e.g., override rate range, failure frequency, forecast error magnitude).
- Random seed(s).
- Resource count and type distribution.
- Time horizon.
- Renewable variability level.

---

## 8. Evaluation Metrics

| Metric | Definition | Unit | Direction |
|---|---|---|---|
| **Renewable absorption** | Amount of renewable energy aligned with dispatched flexibility | kWh | Higher is better |
| **Delivered flexibility error** | Difference between dispatched and actually delivered flexibility | kWh | Lower is better |
| **Overcommitment** | Total dispatch beyond what resources can reliably deliver (dispatched > actual + tolerance) | kWh | Lower is better |
| **Constraint violations** | Number of operational constraint breaches (power, duration, deadline) | Count | Lower is better |
| **Deadline violations** | Resources not meeting energy requirements within deadlines | Count | Lower is better |
| **Rebound** | Demand rebound effects after shifting | kWh | Lower is better |
| **Actual/committed reliability** | Ratio of actual delivered to committed flexibility over a scenario | Ratio (0-1) | Higher is better |

### 8.1 Metric Notes

- **Renewable absorption** may be lower for trust-aware if conservative dispatch reduces absorption. This is an expected possible outcome; the hypothesis is about reliability, not necessarily absorption magnitude.
- **Overcommitment** is the key differentiator — trust-aware should reduce overcommitment even at the cost of some absorption.
- **Actual/committed reliability** directly measures the core hypothesis: are dispatched commitments more reliably fulfilled?

---

## 9. Comparison Methodology

1. Both schedulers run on identical scenario configurations.
2. Differences in outcomes are attributed to the scheduling approach (theoretical vs. trust-aware).
3. Statistical comparison of metric distributions across multiple scenario runs (not just averages).
4. Sensitivity analysis on confidence thresholds and uncertainty levels.
5. Each comparison is documented with scenario parameters, seeds, and full metric breakdowns.

---

## 10. Reproducibility Requirements

- All experiments use fixed seeds for synthetic data generation and scenario parameters.
- Scenario configurations are versioned and stored.
- Scheduler versions and algorithm parameters are recorded with each run.
- Results are stored with full provenance.
- Random number generator states are recordable for each simulation step.

---

## 11. Random Seeds

| Seed Type | Purpose |
|---|---|
| Synthetic data generation | Reproducible device profiles and behavior |
| Scenario parameter generation | Reproducible disruption instances |
| Per-experiment run | Reproducible simulation outcomes |
| Per-scheduler | Same seed → same results (determinism check) |

Seeds must be recorded in experiment results and scenario configurations.

---

## 12. Number of Runs

The number of runs per scenario category is TBD but must be sufficient for:

- Statistical significance testing (e.g., ≥30 runs per configuration for central limit theorem applicability).
- Distribution comparison (not just mean comparison).
- Sensitivity analysis robustness.

**TBD — requires decision once experimental framework is established.**

---

## 13. Aggregation Methodology

| Level | Method |
|---|---|
| Per-run metrics | Compute all metrics for individual simulation runs |
| Per-scenario aggregation | Mean, median, standard deviation, percentiles across runs in same scenario category |
| Per-metric comparison | Compare metric distributions between baseline and trust-aware using statistical tests |
| Overall summary | Summarize across all scenario categories with per-category and aggregate views |

---

## 14. Interpretation Rules

### 14.1 Improvement

Trust-aware is better than baseline if:

- Primary reliability metrics (actual/committed reliability, overcommitment, constraint violations, deadline violations, delivered flexibility error) are significantly better.
- Renewable absorption is not significantly worse OR is significantly better.

### 14.2 Neutral Result

Trust-aware and baseline are statistically indistinguishable on primary metrics, with no consistent direction of difference.

### 14.3 Regression

Trust-aware is worse than baseline on one or more primary metrics with statistical significance.

### 14.4 Inconclusive Result

- Results have high variance relative to mean differences.
- Sample size is insufficient for statistical significance.
- Results conflict across scenario categories.

---

## 15. What Would Count as Success

The core hypothesis is supported if:

1. Trust-aware dispatch produces significantly lower overcommitment than baseline.
2. Trust-aware dispatch produces significantly higher actual/committed reliability.
3. Trust-aware dispatch does not significantly reduce renewable absorption (or improves it).
4. Verification updates trust estimates (learning loop demonstrably changes future trust).
5. Results are statistically significant across multiple scenario categories.

---

## 16. What Would Falsify the Hypothesis

The core hypothesis is falsified if:

1. Trust-aware dispatch produces significantly higher overcommitment than baseline.
2. Trust-aware dispatch produces significantly lower actual/committed reliability.
3. Trust-aware dispatch significantly reduces renewable absorption without reliability improvement.
4. Trust computation does not meaningfully differ from potential (no trust gap).
5. Learning does not measurably update trust estimates from verification.

---

## 17. Sensitivity Analysis

Parameters to vary:

| Parameter | Range | Purpose |
|---|---|---|
| Confidence threshold | TBD | Determine if trust-aware benefits are robust to threshold choice |
| Uncertainty level | Normal, elevated, extreme | Determine if trust-aware is more valuable under higher uncertainty |
| Override rate | Low, medium, high | Determine if trust-aware is more valuable with higher non-compliance |
| Number of resources | TBD | Determine scalability of trust-aware benefit |

---

## 18. Failure Analysis

When a scheduler fails (high overcommitment, constraint violation, deadline violation):

1. Identify which resources contributed most to the failure.
2. Determine whether failure was due to:
   - Overcommitment (dispatched more than could be delivered).
   - Constraint violation (dispatched outside operational limits).
   - Deadline miss (energy not delivered in time).
   - Override (resource did not comply).
   - Failure (device became unavailable).
3. Record failure patterns per scenario category.
4. Compare failure patterns between baseline and trust-aware.

---

## 19. What Would Count as Improvement vs. Neutral vs. Regression vs. Inconclusive

| Outcome | Criteria |
|---|---|
| **Improvement** | Primary reliability metrics significantly better; renewable absorption not significantly worse |
| **Neutral** | No statistically significant difference in primary metrics |
| **Regression** | Primary reliability metrics significantly worse |
| **Inconclusive** | High variance, insufficient sample size, or conflicting results across categories |

**The experiment must not assume trust-aware will win every metric.** The experiment is designed to determine the actual relationship, which may be neutral or even regressive in some dimensions.

---

## 20. Scenario Parameter Definitions

Each scenario category must define:

| Parameter | Normal | Renewable Error | Non-Compliance | Failure | Rebound | Combined |
|---|---|---|---|---|---|---|
| Forecast error magnitude | TBD | TBD | — | — | — | TBD |
| Override rate | TBD | — | TBD | — | — | TBD |
| Failure frequency | TBD | — | — | TBD | — | TBD |
| Rebound magnitude | — | — | — | — | TBD | TBD |
| Renewable variability | TBD | TBD | — | — | — | TBD |
| Resource count | TBD | TBD | TBD | TBD | TBD | TBD |
| Random seed(s) | TBD | TBD | TBD | TBD | TBD | TBD |
| Number of runs | TBD | TBD | TBD | TBD | TBD | TBD |

All TBD values will be set during experimental framework implementation.

---

## 21. Current Status

DRAFT
