import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from backend.app.schemas.scenarios import Scenario
from backend.app.domain.models import FlexibilityResource, TrustState
from backend.app.domain.enums import ResourceType
from backend.app.services.dispatch_service import MVPOptimizer

def create_test_resource(res_id: str, max_p: float, req_kwh: float) -> FlexibilityResource:
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(hours=2)
    return FlexibilityResource(
        id=res_id,
        type=ResourceType.EV,
        location_id="loc",
        rated_power_kw=max_p,
        earliest_start=start,
        latest_end=end,
        required_kwh=req_kwh,
        minimum_kwh=0.0,
        maximum_kwh=10.0,
        minimum_duration=30,
        maximum_duration=120,
        deadline=end,
        min_power=0.0,
        max_power=max_p,
        historical_response=[],
        override_rate=0.0,
        availability_rate=1.0
    )

def test_optimizer_empty_scenario():
    optimizer = MVPOptimizer()
    scenario = Scenario(scenario_id="scen-1", resources=[], disruption_specs={}, seeds={})
    
    plan = optimizer.generate_dispatch_plan(scenario, "potential_kw", {})
    assert len(plan.dispatch_plan) == 0

def test_optimizer_baseline_potential_fallback():
    # Tests that when context lacks trust_data, potential_kw falls back to max_power bounds natively
    optimizer = MVPOptimizer()
    res1 = create_test_resource("res-1", max_p=10.0, req_kwh=5.0)
    scenario = Scenario(scenario_id="scen-1", resources=[res1], disruption_specs={}, seeds={})
    
    plan = optimizer.generate_dispatch_plan(scenario, "potential_kw", {})
    assert len(plan.dispatch_plan) == 2 # 10kW * 0.25h = 2.5kWh. Need 2 steps for 5kWh.
    assert plan.dispatch_plan[0].power_kw == 10.0
    assert plan.dispatch_plan[1].power_kw == 10.0

def test_optimizer_trust_aware_consumes_context():
    optimizer = MVPOptimizer()
    res1 = create_test_resource("res-1", max_p=10.0, req_kwh=5.0)
    scenario = Scenario(scenario_id="scen-1", resources=[res1], disruption_specs={}, seeds={})
    
    # Trust state dictates trusted_kw = 5.0kW
    trust_state = TrustState(potential_kw=10.0, expected_kw=8.0, trusted_kw=5.0, confidence=0.9)
    context = {"trust_data": {"res-1": trust_state}}
    
    plan = optimizer.generate_dispatch_plan(scenario, "trusted_kw", context)
    
    # Needs 4 steps (5kW * 0.25h = 1.25kWh per step) to reach 5.0kWh
    assert len(plan.dispatch_plan) == 4
    for inst in plan.dispatch_plan:
        assert inst.power_kw == 5.0
        assert inst.resource_id == "res-1"

def test_optimizer_clamps_to_hardware_limits():
    optimizer = MVPOptimizer()
    res1 = create_test_resource("res-1", max_p=10.0, req_kwh=5.0) # Hardware max is 10.0
    scenario = Scenario(scenario_id="scen-1", resources=[res1], disruption_specs={}, seeds={})
    
    # AI accidentally predicts potential > hardware bound
    trust_state = TrustState(potential_kw=15.0, expected_kw=12.0, trusted_kw=11.0, confidence=0.9)
    context = {"trust_data": {"res-1": trust_state}}
    
    # Optimizer must clamp to max_power (10.0)
    plan_trust = optimizer.generate_dispatch_plan(scenario, "trusted_kw", context)
    assert plan_trust.dispatch_plan[0].power_kw == 10.0
    
    plan_base = optimizer.generate_dispatch_plan(scenario, "potential_kw", context)
    assert plan_base.dispatch_plan[0].power_kw == 10.0

def test_optimizer_missing_trust_data_fails():
    optimizer = MVPOptimizer()
    res1 = create_test_resource("res-1", max_p=10.0, req_kwh=5.0)
    scenario = Scenario(scenario_id="scen-1", resources=[res1], disruption_specs={}, seeds={})
    
    with pytest.raises(ValueError, match="Trusted data unavailable"):
        optimizer.generate_dispatch_plan(scenario, "trusted_kw", {})

def test_optimizer_deterministic_ordering():
    optimizer = MVPOptimizer()
    res_b = create_test_resource("res-b", 10.0, 2.5)
    res_a = create_test_resource("res-a", 10.0, 2.5)
    
    scenario = Scenario(scenario_id="scen-1", resources=[res_b, res_a], disruption_specs={}, seeds={})
    plan = optimizer.generate_dispatch_plan(scenario, "potential_kw", {})
    
    # Should order by ID: res-a then res-b
    assert plan.dispatch_plan[0].resource_id == "res-a"
    assert plan.dispatch_plan[1].resource_id == "res-b"
