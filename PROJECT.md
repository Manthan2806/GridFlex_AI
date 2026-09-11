# PROJECT

## Purpose

Define the identity, problem, product definition, goals, MVP boundary, and success criteria for GridFlex AI.

## Scope

This document is the authoritative source for the project's definition at the current phase. It establishes what the project is, who it is for, what it will and will not do, and how success will be measured. No other document may redefine project identity, problem statement, primary user, MVP scope, or non-goals.

## Authority

This document is the single source of truth for project identity, problem statement, product definition, primary user, goals, MVP boundary, non-goals, current project status, and high-level success criteria. Other documents must not re-state this information; they may reference it.

## Current Status

DRAFT

---

## 1. Project Identity

**Name:** GridFlex AI

**Theme:** Renewable Energy Intelligence

**Tagline:** Trusted Flexibility for Renewable-Aware Demand Orchestration

**Product type:** Flexibility Intelligence + Orchestration Layer

**Core mechanism:** A closed loop that converts optimistic capacity ratings into confidence-weighted, verified, learnable trust states — and uses those for dispatch.

---

## 2. Problem Statement

### 2.1 Core Problem

A utility or demand-response aggregator needs to coordinate flexible electricity demand with renewable-energy availability. The challenge is that **theoretical flexibility overestimates what can actually be delivered**: loads have operational constraints, deadlines, comfort limits, historical reliability, and behavior that deviates from plan. Dispatching against theoretical capacity produces overcommitment, constraint violations, and unreliable renewable alignment.

### 2.2 Problem Context

- Renewable energy generation (especially solar) is variable and partially unpredictable.
- Flexible loads (EV charging, water heating, industrial processes) exist but their actual shiftable capacity is obscured by operational reality.
- Current demand-response systems often use static capacity ratings or simple scheduling rules that ignore reliability.
- The gap between "theoretically shiftable" and "reliably deliverable" creates risk for grid operators and reduces renewable absorption.
- There is no standardized way to represent, estimate, and verify the trustworthiness of flexible capacity across heterogeneous resource types.

### 2.3 Why This Problem Matters

- **Grid reliability:** Overcommitting flexibility leads to unmet dispatch instructions and grid instability.
- **Renewable integration:** Unreliable flexibility means curtailment when renewables are abundant and shortage when they are not.
- **Economic efficiency:** Aggregators pay for flexibility that may not materialize; resources are underutilized due to conservative static ratings.
- **Scalability:** As DER penetration grows, the coordination problem becomes more complex and the cost of unreliability increases.

---

## 3. Primary User

**Utility / Demand-Response Aggregator**

The entity that:

- Manages a portfolio of flexible resources across residential, commercial, and industrial customers.
- Participates in wholesale energy markets, ancillary services, or utility demand-response programs.
- Needs to make dispatch decisions with quantified reliability.
- Bears the risk of under-delivery or constraint violation.

---

## 4. Secondary Stakeholders

| Stakeholder | Interest |
|---|---|
| Resource owners (EV drivers, homeowners, factories) | Comfort, process continuity, compensation |
| Grid operators (DSOs, TSOs) | Grid stability, congestion management, voltage control |
| Regulators / market operators | Market integrity, measurement & verification standards |
| Retail energy providers | Portfolio balancing, customer retention |

---

## 5. Current Workflow / Problem Mechanism (Today)

1. **Resource enrollment:** Aggregator enrolls resources with static capacity ratings (e.g., "7 kW EV charger").
2. **Availability reporting:** Resources report availability windows (often manually or via simple schedules).
3. **Dispatch optimization:** Aggregator optimizes against theoretical capacity + simple constraints.
4. **Dispatch issuance:** Instructions sent to resources (or customers).
5. **Partial observation:** Actual response measured at meter level (if at all), often delayed.
6. **Settlement:** Based on metered response vs. baseline; disputes common.
7. **No systematic learning:** Historical response rarely feeds back into future capacity estimates.

**Result:** Conservative static derating, frequent under-delivery, limited renewable alignment.

---

## 6. Core Insight

> **Theoretical flexible capacity ≠ Deliverable flexible capacity.**

The deliverable capacity of a flexible resource at a given time depends on:

- Its operational constraints (power, energy, duration, deadlines)
- Its current state (state of charge, temperature, process stage)
- Its historical reliability (override rate, availability rate, response accuracy)
- External uncertainty (renewable forecast error, price signal changes)
- Behavioral factors (user comfort preferences, process requirements)

GridFlex AI makes this distinction explicit, quantifiable, and actionable.

---

## 7. Product Definition

**Flexibility Intelligence + Orchestration Layer**

GridFlex AI is not a forecasting model and not a generic VPP. It is a layer that:

1. **Represents** heterogeneous flexible loads using real operational constraints (not just nameplate ratings).
2. **Estimates** how reliably each resource can deliver flexibility given its behavior history and current uncertainty.
3. **Computes** a time-dependent **trust state** (potential, expected, trusted capacity + confidence).
4. **Matches** trusted flexibility with renewable-aware dispatch opportunities.
5. **Simulates** dispatch execution before commitment.
6. **Dispatches** instructions and records actual response.
7. **Verifies** actual response against dispatched instructions.
8. **Learns** from verification to update future trust estimates.

---

## 8. Core Hypothesis

> If flexible loads are represented using actual operational constraints and historical response reliability rather than theoretical shiftable capacity alone, renewable-aligned demand shifting can make more reliable dispatch decisions under uncertainty.

---

## 9. Core Loop

```
Observe → Represent → Estimate → Trust → Match → Dispatch → Simulate → Verify → Learn
```

Each stage is a distinct computational step with defined inputs and outputs. The loop operates at 15-minute resolution in simulation.

The loop is also documented with the full stage names in ALGORITHM_SPEC.md and ARCHITECTURE.md.

---

## 10. MVP Scope

### 10.1 MVP Mode: Simulation-First

- No real IoT hardware integration.
- No real utility integration.
- No production VPP deployment.
- No claim of production validation.
- Public/system-level energy data where appropriate.
- Synthetic device-level flexibility and behavior data.

### 10.2 MVP Resource Types

1. **EV Charging** — residential and fleet, with departure deadlines, SOC targets, charging power limits.
2. **Water Heaters** — electric resistance and heat pump, with temperature bands, recovery time, draw profiles.
3. **Flexible Industrial Batch/Process Loads** — interruptible batches, thermal storage, process windows, minimum run times.

### 10.3 MVP Capabilities

- Normalize heterogeneous resources into a common flexibility representation.
- Compute time-dependent trust states from constraints + behavior + uncertainty.
- Detect renewable-aligned dispatch opportunities from forecasts.
- Formulate and solve dispatch optimization using trusted (not theoretical) capacity.
- Simulate actual device response to dispatch (including overrides, failures, rebound).
- Verify delivered vs. dispatched flexibility.
- Update trust estimates from verification outcomes.
- Compare baseline (theoretical) vs. trust-aware scheduling on equivalent scenarios.

### 10.4 MVP Assumptions

- 15-minute time resolution is sufficient for the target use cases.
- Synthetic behavior models can capture essential reliability patterns.
- Public renewable/weather/demand data is available for the simulation horizon.
- The aggregator has sufficient visibility into resource constraints (via enrollment data).
- OR-Tools CP-SAT can solve the dispatch problem within acceptable time for MVP scale.

### 10.5 MVP Non-Goals

The following are explicitly out of scope for the MVP:

- Real IoT deployment or device communication protocols (OCPP, OpenADR, Modbus).
- Real utility integration (SCADA, EMS, market interfaces).
- Full production VPP with 24/7 operations.
- Full electrical power-flow simulation (no AC/DC load flow).
- Blockchain or distributed ledger for settlement.
- LLM-based control or natural-language dispatch.
- Reinforcement learning for core dispatch (unless later justified).
- Microservice architecture (modular monolith only).
- Multi-aggregator coordination or peer-to-peer flexibility trading.
- Ancillary service market bidding (frequency regulation, voltage support).
- Customer-facing mobile apps or engagement platforms.
- Distribution grid constraints beyond simple feeder capacity limits.
- Regulatory measurement & verification (M&V) protocol compliance.
- Market price optimization (renewable absorption is the primary objective).

---

## 11. WHAT GRIDFLEX AI IS NOT

| Misconception | Reality |
|---|---|
| "Just a renewable forecasting system" | Forecasting is an input; the product is flexibility orchestration with trust. |
| "Just an EV smart charging app" | EV is one of three MVP resource types; the system handles heterogeneity. |
| "Just a generic VPP" | VPPs aggregate capacity; GridFlex AI quantifies and verifies *trusted* capacity. |
| "Just an optimization dashboard" | Optimization is one stage; the loop includes estimation, simulation, verification, learning. |
| "Just an AI prediction system" | AI/ML is used for confidence/reliability estimation, not end-to-end control. |
| "A production utility control platform" | MVP is simulation-first; production deployment is a later phase. |

**The actual product mechanism:** A closed loop that converts optimistic capacity ratings into confidence-weighted, verified, learnable trust states — and uses those for dispatch.

---

## 12. Success Criteria

| Criterion | Measurement |
|---|---|
| Heterogeneous flexibility normalization | All three resource types map to common representation with constraints. |
| Theoretical vs. trusted flexibility gap | Trusted capacity measurably differs from theoretical for each resource type. |
| Trust affects dispatch | Trust-aware scheduler produces different dispatch than baseline on same scenarios. |
| Verification updates trust | Post-verification trust estimates differ from pre-verification estimates. |
| Renewable-aligned shifting demonstrated | Simulation shows demand shifted into renewable-rich windows. |
| Baseline vs. trust-aware comparison | Statistically meaningful difference in reliability metrics on equivalent scenarios. |

---

## 13. Demonstration Goals (MVP)

1. **Heterogeneous normalization:** EV, water heater, and industrial batch resources all represented in the same flexibility schema.
2. **Trust computation:** For a given resource at time t, show potential_kw, expected_kw, trusted_kw, confidence.
3. **Dispatch difference:** Show two dispatch plans for the same scenario — one using theoretical capacity, one using trusted capacity.
4. **Verification loop:** Simulate actual response (with overrides/failures), compute verification error, update trust.
5. **Scenario comparison:** Run 6 scenario categories; report 7 metrics for both schedulers.

---

## 14. Known Limitations (MVP)

- Synthetic behavior may not capture all real-world failure modes.
- No real-time latency or communication failure modeling.
- No market price optimization (renewable absorption is the primary objective).
- Single aggregator; no multi-party coordination.
- No distribution grid constraints (feeder capacity only as a simple limit).
- Trust computation formulas are TBD — initial version will use heuristic/statistical approach.
- No regulatory measurement & verification (M&V) protocol compliance.
- No claim of production validation.

---

## 15. Current Project Status

**Phase:** Foundation documentation complete; moving to detailed specification phase.

**Next Phase:** Contract freezing → team parallelization → implementation.

---

## 16. Future Possibilities (Post-MVP, Clearly Separated from MVP)

The following are NOT part of the MVP. They are possibilities for later phases.

- Real IoT integration (OCPP for EV, OpenADR for DR, Modbus/REST for industrial).
- Real utility integration (market interfaces, SCADA data feeds).
- Distribution grid awareness (power flow, voltage, congestion).
- Multi-aggregator flexibility markets.
- Ancillary service co-optimization.
- Reinforcement learning for adaptive trust estimation.
- Customer engagement / comfort preference learning.
- Regulatory M&V protocol alignment (IPMVP, etc.).
- Microservice extraction for independent scaling.
- Geographic expansion beyond initial scope.

---

## 17. Current Status

DRAFT
