"""Integration tests for AI/ML → TrustState → MVPOptimizer → DispatchPlan pipeline.

These tests verify:
1. AI/ML inference outputs map correctly to TrustState.
2. TrustState hydration populates context["trust_data"] keyed by resource ID.
3. MVPOptimizer consumes trust_data correctly for both baseline and trust-aware strategies.
4. The resulting DispatchPlan is compatible with Team 4's SimulationAdapter.
5. Resource ID alignment is deterministic and unambiguous.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from backend.app.domain.enums import ResourceType, OptimizationStatus
from backend.app.domain.models import FlexibilityResource, TrustState
from backend.app.integrations.ai_ml_client import (
    ExperimentalEVModelClient,
    _trust_state_from_output,
)
from backend.app.schemas.scenarios import Scenario
from backend.app.services.dispatch_service import MVPOptimizer
from backend.app.services.trust_hydration import hydrate_trust_context, build_optimizer_context
from simulation.adapter import SimulationAdapter
from backend.app.schemas.runs import SimulationInput
from backend.app.schemas.dispatch import DispatchPlan


def _make_resource(res_id: str, max_power: float = 7.2, required_kwh: float = 4.0) -> FlexibilityResource:
    start = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
    return FlexibilityResource(
        id=res_id,
        type=ResourceType.EV,
        location_id="test-loc",
        rated_power_kw=max_power,
        earliest_start=start,
        latest_end=start + timedelta(hours=2),
        required_kwh=required_kwh,
        minimum_kwh=0.0,
        maximum_kwh=20.0,
        minimum_duration=15,
        maximum_duration=120,
        deadline=start + timedelta(hours=2),
        min_power=0.0,
        max_power=max_power,
        historical_response=[],
        override_rate=0.0,
        availability_rate=1.0,
    )


# ──────────────────────────────────────────────
# 1. AI/ML output → TrustState mapping
# ──────────────────────────────────────────────

def test_trust_state_from_raw_output():
    """Verify _trust_state_from_output maps the AI/ML dict to canonical TrustState."""
    output = {
        "requested_dispatch_kw": 7.2,
        "expected_kw": 5.0,
        "trusted_kw": 3.5,
        "dispatch_group": "medium",
        "safety_coverage": 0.85,
        "expected_ratio": 0.694,
        "trusted_ratio": 0.486,
    }
    ts = _trust_state_from_output(output)
    assert ts.potential_kw == 7.2
    assert ts.expected_kw == 5.0
    assert ts.trusted_kw == 3.5
    assert ts.confidence == 0.85
    assert ts.trusted_kw <= ts.expected_kw <= ts.potential_kw


def test_trust_state_ordering_invariant():
    """The TrustState model_validator enforces trusted_kw <= expected_kw <= potential_kw."""
    with pytest.raises(ValueError, match="Trust ordering invariant violated"):
        TrustState(potential_kw=5.0, expected_kw=6.0, trusted_kw=3.0, confidence=0.5)


# ──────────────────────────────────────────────
# 2. Batch hydration from live AI/ML client
# ──────────────────────────────────────────────

def test_hydrate_trust_context_single_resource():
    """Live inference produces a TrustState keyed by resource ID."""
    client = ExperimentalEVModelClient(demo_mode=True)
    res = _make_resource("ev-test-001")
    event_time = res.earliest_start

    trust_data = hydrate_trust_context(client, [res], event_time)

    assert "ev-test-001" in trust_data
    ts = trust_data["ev-test-001"]
    assert isinstance(ts, TrustState)
    assert ts.trusted_kw <= ts.expected_kw <= ts.potential_kw
    assert 0.0 <= ts.confidence <= 1.0


def test_hydrate_trust_context_multiple_resources():
    """Multiple resources produce one TrustState each, keyed correctly."""
    client = ExperimentalEVModelClient(demo_mode=True)
    resources = [_make_resource(f"ev-{i:03d}") for i in range(3)]
    event_time = resources[0].earliest_start

    trust_data = hydrate_trust_context(client, resources, event_time)

    assert len(trust_data) == 3
    for i in range(3):
        assert f"ev-{i:03d}" in trust_data
        assert isinstance(trust_data[f"ev-{i:03d}"], TrustState)


def test_hydrate_rejects_duplicate_resource_ids():
    """Duplicate IDs must fail rather than silently overwrite."""
    client = ExperimentalEVModelClient(demo_mode=True)
    resources = [_make_resource("ev-dup"), _make_resource("ev-dup")]
    with pytest.raises(ValueError, match="Duplicate resource ID"):
        hydrate_trust_context(client, resources, datetime(2026, 9, 12, tzinfo=timezone.utc))


def test_build_optimizer_context_structure():
    """build_optimizer_context produces a dict with trust_data key."""
    client = ExperimentalEVModelClient(demo_mode=True)
    res = _make_resource("ev-ctx-001")
    ctx = build_optimizer_context(client, [res], res.earliest_start)

    assert "trust_data" in ctx
    assert "ev-ctx-001" in ctx["trust_data"]


# ──────────────────────────────────────────────
# 3. MVPOptimizer with live trust data
# ──────────────────────────────────────────────

def test_optimizer_baseline_with_trust_context():
    """Baseline strategy uses potential_kw from TrustState when context is available."""
    client = ExperimentalEVModelClient(demo_mode=True)
    res = _make_resource("ev-base-001", max_power=7.2, required_kwh=3.0)
    scenario = Scenario(scenario_id="scen-baseline", resources=[res], disruption_specs={}, seeds={})
    ctx = build_optimizer_context(client, [res], res.earliest_start)

    optimizer = MVPOptimizer()
    plan = optimizer.generate_dispatch_plan(scenario, "potential_kw", ctx)

    assert len(plan.dispatch_plan) > 0
    assert plan.status == OptimizationStatus.OPTIMAL
    # Baseline uses potential_kw which equals requested_dispatch_kw (clamped to max_power)
    for inst in plan.dispatch_plan:
        assert inst.resource_id == "ev-base-001"
        assert inst.power_kw <= res.max_power


def test_optimizer_trust_aware_with_trust_context():
    """Trust-aware strategy uses trusted_kw from live AI/ML inference."""
    client = ExperimentalEVModelClient(demo_mode=True)
    res = _make_resource("ev-trust-001", max_power=7.2, required_kwh=3.0)
    scenario = Scenario(scenario_id="scen-trust", resources=[res], disruption_specs={}, seeds={})
    ctx = build_optimizer_context(client, [res], res.earliest_start)

    optimizer = MVPOptimizer()
    plan = optimizer.generate_dispatch_plan(scenario, "trusted_kw", ctx)

    trusted_kw = ctx["trust_data"]["ev-trust-001"].trusted_kw
    assert len(plan.dispatch_plan) > 0
    for inst in plan.dispatch_plan:
        assert inst.resource_id == "ev-trust-001"
        # Dispatched power must not exceed the trust-aware bound (clamped to max_power)
        assert inst.power_kw <= min(trusted_kw + 0.001, res.max_power)


def test_optimizer_trust_aware_fails_without_context():
    """Trust-aware must fail cleanly when no trust data is available."""
    res = _make_resource("ev-no-trust")
    scenario = Scenario(scenario_id="scen-no-trust", resources=[res], disruption_specs={}, seeds={})
    optimizer = MVPOptimizer()

    with pytest.raises(ValueError, match="Trusted data unavailable"):
        optimizer.generate_dispatch_plan(scenario, "trusted_kw", {})


def test_baseline_does_not_depend_on_trusted_kw():
    """Baseline fallback must work even without any trust context at all."""
    res = _make_resource("ev-fallback", max_power=5.0, required_kwh=2.5)
    scenario = Scenario(scenario_id="scen-fallback", resources=[res], disruption_specs={}, seeds={})
    optimizer = MVPOptimizer()

    plan = optimizer.generate_dispatch_plan(scenario, "potential_kw", {})

    assert len(plan.dispatch_plan) > 0
    # Falls back to res.max_power when no trust context is present
    assert plan.dispatch_plan[0].power_kw == 5.0


# ──────────────────────────────────────────────
# 4. End-to-end: AI/ML → Optimizer → SimulationAdapter
# ──────────────────────────────────────────────

def test_end_to_end_dispatch_plan_to_simulation_adapter():
    """Full pipeline: AI/ML inference → TrustState → MVPOptimizer → DispatchPlan → SimulationAdapter."""
    client = ExperimentalEVModelClient(demo_mode=True)
    res = _make_resource("ev-e2e-001", max_power=7.2, required_kwh=3.0)
    scenario = Scenario(scenario_id="scen-e2e", resources=[res], disruption_specs={}, seeds={"master": 42})
    ctx = build_optimizer_context(client, [res], res.earliest_start)

    optimizer = MVPOptimizer()

    # Generate both plans from the same scenario
    baseline_plan = optimizer.generate_dispatch_plan(scenario, "potential_kw", ctx)
    trust_plan = optimizer.generate_dispatch_plan(scenario, "trusted_kw", ctx)

    # Feed baseline plan into SimulationAdapter
    adapter = SimulationAdapter()
    sim_input = SimulationInput(
        scenario=scenario,
        initial_resource_states={},
        renewable_demand_forecasts=[],
        dispatch_plan=baseline_plan,
        system_constraints={},
    )
    sim_output = adapter.run_simulation(sim_input)

    assert len(sim_output.actual_response) > 0
    assert len(sim_output.resource_state_evolution) > 0

    # Feed trust-aware plan into SimulationAdapter
    sim_input_trust = SimulationInput(
        scenario=scenario,
        initial_resource_states={},
        renewable_demand_forecasts=[],
        dispatch_plan=trust_plan,
        system_constraints={},
    )
    sim_output_trust = adapter.run_simulation(sim_input_trust)

    assert len(sim_output_trust.actual_response) > 0


def test_deterministic_replay():
    """Same inputs produce identical trust_data and DispatchPlans."""
    client = ExperimentalEVModelClient(demo_mode=True)
    res = _make_resource("ev-det-001", max_power=7.2, required_kwh=3.0)
    scenario = Scenario(scenario_id="scen-det", resources=[res], disruption_specs={}, seeds={})
    event_time = res.earliest_start

    ctx1 = build_optimizer_context(client, [res], event_time)
    ctx2 = build_optimizer_context(client, [res], event_time)

    assert ctx1["trust_data"]["ev-det-001"].trusted_kw == ctx2["trust_data"]["ev-det-001"].trusted_kw
    assert ctx1["trust_data"]["ev-det-001"].expected_kw == ctx2["trust_data"]["ev-det-001"].expected_kw

    optimizer = MVPOptimizer()
    plan1 = optimizer.generate_dispatch_plan(scenario, "trusted_kw", ctx1)
    plan2 = optimizer.generate_dispatch_plan(scenario, "trusted_kw", ctx2)

    assert len(plan1.dispatch_plan) == len(plan2.dispatch_plan)
    for i1, i2 in zip(plan1.dispatch_plan, plan2.dispatch_plan):
        assert i1.resource_id == i2.resource_id
        assert i1.power_kw == i2.power_kw
        assert i1.time_step == i2.time_step
