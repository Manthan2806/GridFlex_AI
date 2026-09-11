# RESEARCH

## Purpose

Record research findings, evidence, sources, research-derived constraints, competitor/solution landscape, and technical research conclusions for GridFlex AI.

## Scope

This document maintains the evidence discipline for the project. Statements are classified by confidence level so that assumptions are not presented as facts. Research findings guide project direction but do not override product decisions established in PROJECT.md.

## Authority

This document is the authoritative source for research findings, evidence, sources, research-derived constraints, competitor/solution landscape, and technical research conclusions. Other documents must not redefine research findings; they may reference them.

## Current Status

DRAFT

---

## 1. Evidence Classification

Statements in this document are classified as:

| Classification | Definition |
|---|---|
| **VERIFIED FACT** | Confirmed by evidence or documentation within this project's scope. |
| **RESEARCH FINDING** | Supported by research but not independently re-verified in this project. |
| **ENGINEERING INFERENCE** | A reasoned conclusion drawn from verified facts and research findings. |
| **ASSUMPTION** | Accepted without current evidence; may be revisited. |
| **UNKNOWN** | Not yet determined. |
| **CONTESTED** | Disputed or with conflicting evidence. |

Do not present assumptions as facts. Every claim carries its classification.

---

## 2. Problem Research

### Finding: Theoretical flexibility overestimates deliverable flexibility

- **Claim:** Flexible resources have theoretical shiftable capacity that exceeds what they can reliably deliver under real operational constraints.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** This is the foundational insight of GridFlex AI. Without it, the project has no differentiation.
- **Design implication:** The system must compute trusted flexibility separately from theoretical flexibility and use trusted flexibility for dispatch.
- **Confidence/limitations:** Well-established across multiple studies; specific quantitative gaps vary by resource type and context.

### Finding: Aggregators bear risk from under-delivery

- **Claim:** Demand-response aggregators face financial and reliability risk when contracted flexibility does not materialize.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** Establishes the primary user's need for quantified reliability, not just capacity.
- **Design implication:** Trust computation must produce metrics that aggregators can use for risk assessment and settlement.
- **Confidence/limitations:** Broadly supported; specific risk magnitudes are context-dependent.

### Finding: Current DR systems rely on static capacity ratings

- **Claim:** Many demand-response programs schedule against nameplate or static ratings rather than dynamic, context-aware deliverable capacity.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** Confirms the gap between current practice and what GridFlex AI proposes.
- **Design implication:** The system must explicitly represent operational constraints and compute time-dependent trust, not just use static ratings.
- **Confidence/limitations:** General finding; degree of static-rating usage varies by program.

---

## 3. Demand-Response Research

### Finding: Behavioral and automated DR are mature

- **Claim:** Behavioral demand-response programs and automated DR (direct load control, smart thermostats) are well-established and widely deployed.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** The project cannot claim novelty in demand-response participation itself; the differentiation must be elsewhere.
- **Design implication:** GridFlex AI does not need to replicate DR program mechanics; it focuses on reliability estimation and verification.
- **Confidence/limitations:** Mature category; well-documented in literature and industry.

### Finding: EV smart charging is mature

- **Claim:** Smart charging for electric vehicles is a well-researched and commercially deployed area.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** EV charging is one of three MVP resource types, but the project must not position itself as just an EV charging solution.
- **Design implication:** EV charging implementation must be competent but not the sole focus; the system's value is cross-resource trust computation.
- **Confidence/limitations:** Mature; many commercial solutions exist.

### Finding: DR program settlement often uses metered response vs. baseline

- **Claim:** Settlement in DR programs typically compares actual consumption against a baseline or agreed-upon target.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** Verification (comparing actual vs. dispatched) aligns with existing settlement practices.
- **Design implication:** The verification stage must produce metrics compatible with or derivable from settlement-relevant measures.
- **Confidence/limitations:** General finding; settlement methodologies vary significantly by program and jurisdiction.

---

## 4. Renewable Integration Research

### Finding: Solar generation is variable and partially unpredictable

- **Claim:** Solar photovoltaic output varies with weather, cloud cover, and time of day, and perfect forecasting is unachievable.
- **Classification:** VERIFIED FACT
- **Evidence/source:** Widely documented in energy literature and operational data.
- **Why it matters:** Renewable variability creates dispatch opportunities but also uncertainty that must be accounted for in trust computation.
- **Design implication:** Renewable forecasts are inputs but must carry uncertainty information; the system must not treat forecasts as certainties.
- **Confidence/limitations:** Fundamental physical characteristic; universally accepted.

### Finding: Renewable-aligned demand shifting is valuable but challenging

- **Claim:** Shifting flexible demand to coincide with renewable generation reduces curtailment and improves renewable utilization, but precise alignment is difficult due to forecast errors and load variability.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** The system must optimize for renewable alignment while acknowledging uncertainty in both supply and demand.
- **Design implication:** The optimization objective includes renewable absorption, but must also account for risk of misalignment.
- **Confidence/locations:** Broadly supported; specific benefits vary by grid and resource mix.

---

## 5. Flexibility Research

### Finding: Flexibility forecasting already exists

- **Claim:** Research and commercial solutions exist for forecasting the flexibility (shiftable capacity) of individual resources and portfolios.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** GridFlex AI does not need to invent flexibility forecasting; it must ensure its forecasting is trust-aware.
- **Design implication:** The estimation stage can build on or reference existing flexibility forecasting methods; the differentiator is incorporating reliability.
- **Confidence/limitations:** Flexible forecasting methods exist; quality and trust-awareness vary significantly.

### Finding: Credible capacity / reliable flexibility is already researched

- **Claim:** The concept of credible capacity — the capacity that can be reliably dispatched — has been studied in the context of demand-response and DER portfolios.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** GridFlex AI's "trusted flexibility" concept is related to but not identical to credible capacity; the relationship must be documented.
- **Design implication:** Trust computation can draw on credible capacity research but must be tailored to the system's specific loop (representation → estimation → trust → match → simulate → dispatch → verify → learn).
- **Confidence/limitations:** The concept is established; exact definitions and computation methods vary across literature.

### Finding: Local-grid-aware orchestration already exists

- **Claim:** Commercial and research solutions exist for orchestrating distributed energy resources with awareness of local distribution grid constraints.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** The project does not claim novelty in grid-aware orchestration; the MVP includes feeder capacity as a simple limit, not full power-flow simulation.
- **Design implication:** Feeder capacity constraints are included as hard limits; full distribution grid simulation is a future possibility, not an MVP requirement.
- **Confidence/limitations:** Grid-aware ORC is an active area; MVP scope is appropriately limited.

---

## 6. Flexible-Load Research

### Finding: Flexible resources have diverse operational constraints

- **Claim:** Different flexible load types (EV, water heaters, industrial processes) have fundamentally different operational constraints — deadlines, temperature bands, process windows, minimum run times.
- **Classification:** VERIFIED FACT
- **Evidence/source:** Engineering knowledge; device specifications and operational manuals.
- **Why it matters:** Heterogeneous constraint representation is essential; a one-size-fits-all capacity model cannot capture real flexibility.
- **Design implication:** The domain model must support type-specific constraints while maintaining a common representation for optimization and simulation.
- **Confidence/limitations:** Universally accepted; specific constraint parameters vary by manufacturer and model.

### Finding: User override and non-compliance reduce actual DR performance

- **Claim:** In real demand-response programs, a significant fraction of enrolled resources do not respond as dispatched due to user comfort preferences, override actions, or operational necessity.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** Override rate is a key factor in trust computation; ignoring it leads to overcommitment.
- **Design implication:** Override rate must be a parameter in behavior modeling and trust estimation; the simulator must model non-compliance.
- **Confidence/limitations:** Well-documented phenomenon; override rates vary widely (5–30%+ depending on program type and customer segment).

---

## 7. Forecast Uncertainty

### Finding: Renewable forecast error is systematic and time-dependent

- **Claim:** Solar forecast errors are not random noise; they exhibit systematic patterns related to cloud type, ramp events, and time of day.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** Trust computation must account for forecast uncertainty, and the uncertainty is not uniform across time periods.
- **Design implication:** Forecast uncertainty inputs to estimation should carry time-dependent information, not just a single scalar error estimate.
- **Confidence/limitations:** Well-documented; specific error patterns depend on forecasting method and geographic location.

### Finding: Demand forecast uncertainty compounds with renewable uncertainty

- **Claim:** The combination of uncertain renewable supply and uncertain demand creates compounding effects on the available dispatch opportunity.
- **Classification:** ENGINEERING INFERENCE
- **Evidence/source:** Logical consequence of renewable variability and demand variability research findings.
- **Why it matters:** Scenarios must test combined uncertainty, not just individual sources in isolation.
- **Design implication:** Scenario categories include "combined uncertainty" to test both sources simultaneously.
- **Confidence/limitations:** Inference from individual uncertainty research; specific compounding effects need empirical validation.

---

## 8. Rebound Effects

### Finding: Demand rebound after shifting is observed

- **Claim:** After flexible demand is shifted to an earlier or different time window, a portion of the demand may return (rebound), partially or fully negating the shift.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** Rebound reduces net demand reduction and must be modeled in simulation and accounted for in the objective function.
- **Design implication:** The simulator must model rebound behavior; the optimization objective includes rebound as a cost category.
- **Confidence/limitations:** Documented in energy efficiency and DR literature; magnitude varies by resource type and context.

---

## 9. User Override / Non-Compliance

### Finding: Non-compliance is heterogeneous across resource types

- **Claim:** Different resource types exhibit different override patterns — EV drivers may override departure deadlines, homeowners may override thermostat setpoints, industrial processes may be interruptible only at certain stages.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** Override modeling must be resource-type-specific, not a single aggregate override rate.
- **Design implication:** Each resource type in the domain model should support type-specific override parameters and behaviors.
- **Confidence/limitations:** General finding; specific patterns need validation per resource type and population.

---

## 10. Flexibility Reliability

### Finding: Reliability of flexible resources varies over time

- **Claim:** The reliability of a flexible resource is not constant; it depends on state of charge, temperature, process stage, time of day, season, and other factors.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** Trust must be time-dependent, not a static property of the resource.
- **Design implication:** Trust state is recomputed each cycle from current evidence, as stated in DOMAIN_MODEL.md and ALGORITHM_SPEC.md.
- **Confidence/locations:** Broadly supported; specific drivers vary by resource type.

### Finding: Historical response is a predictor of future response

- **Claim:** A resource's historical response accuracy (how closely it followed dispatch instructions in the past) is informative about its future reliability.
- **Classification:** ENGINEERING INFERENCE
- **Evidence/source:** Logical inference from behavioral data principles; supported by DR program experience.
- **Why it matters:** Historical response data feeds the estimation stage to produce confidence-weighted trust.
- **Design implication:** The estimation stage uses historical_response as a key input.
- **Confidence/limitations:** Generally true but subject to state changes (e.g., a battery degrading, a water heater aging).

---

## 11. Baseline and Measurement / Verification

### Finding: M&V standards exist but are not part of MVP

- **Claim:** Measurement and verification protocols (e.g., IPMVP) exist for quantifying energy savings and demand response impacts.
- **Classification:** VERIFIED FACT
- **Evidence/source:** IPMVP and related standards documentation.
- **Why it matters:** The system's verification stage is conceptually related to M&V but is not required to comply with M&V protocols in the MVP.
- **Design implication:** Verification in the MVP is simulation-based; regulatory M&V compliance is a future possibility, not an MVP requirement.
- **Confidence/limitations:** Standards exist and are well-known; compliance scope is intentionally excluded from MVP per PROJECT.md.

---

## 12. Local Grid Constraints

### Finding: Feeder capacity limits constrain dispatch

- **Claim:** Distribution feeders have thermal and voltage limits that constrain how much flexibility can be dispatched without causing infrastructure problems.
- **Classification:** VERIFIED FACT
- **Evidence/source:** Power systems engineering knowledge; grid codes and standards.
- **Why it matters:** Feeder capacity is included as a hard constraint in the optimization formulation (ALGORITHM_SPEC.md).
- **Design implication:** Feeder capacity is modeled as a simple limit in the MVP; full power-flow simulation is deferred.
- **Confidence/limitations:** Universally accepted; detailed modeling deferred per non-goals in PROJECT.md.

---

## 13. Existing Commercial Solutions

### Finding: Existing solution saturation is high

- **Claim:** The demand-response, VPP, smart charging, and flexibility management space has numerous commercial and open-source solutions.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** The project cannot succeed by being another general-purpose DR or VPP platform.
- **Design implication:** Differentiation must come from the trusted flexibility loop, not from generic DR features.
- **Confidence/limitations:** High confidence in saturation; specific competitor analysis requires further research.

---

## 14. Existing Academic Approaches

### Finding: Academic work on flexibility and trust-aware dispatch exists

- **Claim:** Academic research addresses optimization under uncertainty, stochastic programming for DR, and reliability-aware scheduling.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** The project can build on or reference these approaches; it does not need to invent new optimization theory.
- **Design implication:** Trust computation and optimization formulation can reference stochastic programming and robust optimization literature.
- **Confidence/limitations:** Broad academic base; applicability to specific resource types and contexts requires engineering judgment.

---

## 15. India-Specific Context

### Finding: India has growing renewable capacity and DR potential

- **Claim:** India has rapidly expanding solar and wind capacity and an evolving demand-response ecosystem with significant untapped potential.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** Provides context for why the project is relevant and where it could eventually be deployed.
- **Design implication:** The system should be designed with potential India deployment in mind (resource types, tariff structures, regulatory context).
- **Confidence/limitations:** General context is well-established; India-specific DR program details require further research.

### Finding: Gujarat has significant solar and industrial flexibility potential

- **Claim:** Gujarat, India, has substantial solar generation capacity and industrial load that could participate in demand-response programs.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Source reference needs to be transferred from the research workspace.
- **Why it matters:** Gujarat may be an initial target deployment region.
- **Design implication:** Dataset geographic scope must be documented explicitly; the system must not silently describe national data as Gujarat-specific (per DATA_SPEC.md).
- **Confidence/limitations:** General context is established; Gujarat-specific data and program details require validation.

---

## 16. Technical Technology Research

### Finding: OR-Tools CP-SAT is suitable for constraint-based scheduling

- **Claim:** Google's OR-Tools CP-SAT solver is well-suited for discrete scheduling problems with hard constraints and multi-category objectives.
- **Classification:** ENGINEERING INFERENCE
- **Evidence/source:** OR-Tools documentation; common practice in scheduling optimization.
- **Why it matters:** Validates the Decision Log choice to use OR-Tools CP-SAT for MVP optimization.
- **Design implication:** The optimization formulation must be designed to be compatible with CP-SAT's modeling approach.
- **Confidence/limitations:** CP-SAT is widely used and capable; solver performance depends on formulation quality.

### Finding: Statistical/ML approaches are appropriate for confidence estimation

- **Claim:** Statistical and machine learning methods are suitable for estimating flexibility confidence and reliability from historical data, without requiring LLMs or reinforcement learning.
- **Classification:** ENGINEERING INFERENCE
- **Evidence/source:** Logical inference from the nature of the estimation problem (regression, classification, probabilistic estimation on structured data).
- **Why it matters:** Supports Decision Log #8 (no LLMs in core control loop).
- **Design implication:** AI/ML scope is limited to statistical/ML methods for the MVP; the specific approach is TBD.
- **Confidence/locations:** Appropriate for structured, tabular data from device behavior; deep learning or LLMs may be overkill for MVP.

---

## 17. Differentiation Research

### Finding: AI renewable forecasting + load shifting is not sufficiently differentiated

- **Claim:** The combination of "AI predicts renewable energy and shifts loads" is a common product narrative with many existing and emerging solutions.
- **Classification:** RESEARCH FINDING
- **Evidence/source:** Market research and competitor analysis documented in RESEARCH.md section 13.
- **Why it matters:** GridFlex AI must explicitly differentiate from generic renewable+load narratives.
- **Design implication:** The product differentiator is the trusted flexibility loop (represent → estimate → trust → match → simulate → dispatch → verify → learn), not just prediction+shifting.
- **Confidence/limitations:** High confidence; supported by market saturation findings.

---

## 18. Identified Opportunity Gap

### Finding: No existing product combines trusted flexibility with renewable-aligned constrained dispatch and verification-learning loop

- **Claim:** While individual components exist (flexibility forecasting, VPP orchestration, renewable alignment, verification), no widely deployed product integrates them into a closed trust-compute → simulate → dispatch → verify → learn loop across heterogeneous resources with a focus on reliability of delivered flexibility.
- **Classification:** ENGINEERING INFERENCE
- **Evidence/source:** Synthesis of research findings on solution saturation (section 13), flexibility forecasting (section 5), credible capacity (section 5), and grid-aware orchestration (section 5).
- **Why it matters:** This is the project's window of opportunity; it must be validated and not assumed.
- **Design implication:** The system must implement the full loop, not just one or two stages.
- **Confidence/limitations:** Inference from landscape analysis; could be contested as specific competitors may have similar integrated approaches that are not widely documented.

### Finding: The stronger mechanism is the combination, not any single algorithm

- **Claim:** The competitive advantage lies not in any single algorithm (forecasting, optimization, trust computation) but in the combination: trusted flexibility + renewable alignment + constrained dispatch + simulation + verification + learning.
- **Classification:** ENGINEERING INFERENCE
- **Evidence/source:** RESEARCH.md section 17 finding combined with RESEARCH.md sections 5, 13, and 14.
- **Why it matters:** Product strategy should emphasize the loop and integration, not individual algorithmic innovations.
- **Design implication:** Each component can use established methods; the integration and the trust-aware approach are the differentiators.
- **Confidence/limitations:** Inference; the degree of competitive advantage from integration vs. individual components needs empirical validation through experiments.

---

## 19. Remaining Unknowns

| Unknown | Why It Matters | Current Approach |
|---|---|---|
| Exact competitive landscape details | Affects differentiation claims | Marked as UNKNOWN; detailed analysis deferred |
| Optimal mathematical formulation for trust computation | Core algorithm | TBD; initial heuristic/statistical approach |
| Real-world performance characteristics of trust-aware approach | Core hypothesis validation | Requires experimentation per EXPERIMENT_SPEC.md |
| Specific ML model for confidence estimation | AI/ML implementation | TBD; statistical/ML approach confirmed, specific model TBD |
| Geographic scope of datasets | Data scope and claims | Must be documented per DATA_SPEC.md; no silent Gujarat-ification |
| Source references for research findings | Evidence traceability | To be transferred from research workspace |

---

## 20. Summary of Key Research-Derived Constraints

Research findings support the following constraints on the project direction (from PROJECT.md and RESEARCH.md combined):

1. Do not position the project as a generic renewable forecaster or load shifter.
2. Do not rely on LLM-based control or reinforcement learning unless later justified.
3. Focus the differentiation on the trusted flexibility loop: represent, estimate, trust, match, simulate, dispatch, verify, learn.
4. The utility/demand-response aggregator is the primary user.
5. MVP must be simulation-first.
6. No claim of production validation.
7. Modular monolith architecture.
8. OR-Tools CP-SAT for MVP optimization.
9. 15-minute time resolution for MVP.
10. Three resource types: EV charging, water heaters, flexible industrial batch/process loads.

---

## 21. Current Status

DRAFT
