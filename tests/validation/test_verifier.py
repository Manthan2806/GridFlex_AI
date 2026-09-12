import pytest
from datetime import datetime
from pydantic import BaseModel

from backend.app.schemas.runs import SimulationInput, SimulationOutput, ActualResponse
from backend.app.schemas.scenarios import Scenario
from backend.app.schemas.dispatch import DispatchPlan, DispatchInstruction
from backend.app.domain.models import FlexibilityResource
from backend.app.domain.enums import ResourceType, OptimizationStatus
from backend.app.schemas.core import TimeStep

from experiments.metrics import (
    calculate_renewable_absorption,
    calculate_delivered_flexibility_error,
    calculate_overcommitment,
    calculate_reliability,
    calculate_rebound
)
from backend.app.services.verification_service import SimulationVerifier

# --- Metrics Unit Tests ---

def test_renewable_absorption():
    actuals = [
        ActualResponse(resource_id="res-1", time_step=0, delivered_kw=10.0),
        ActualResponse(resource_id="res-1", time_step=1, delivered_kw=10.0),
        ActualResponse(resource_id="res-1", time_step=2, delivered_kw=10.0)
    ]
    # Excess at t=0 and t=2, but not t=1
    series = {0: 50.0, 1: -10.0, 2: 20.0}
    absorption = calculate_renewable_absorption(actuals, series)
    # (10 * 0.25) + (10 * 0.25) = 5.0
    assert absorption == 5.0

def test_delivered_flexibility_error():
    dispatched = {"res-1": {0: 10.0, 1: 10.0}}
    actuals = {"res-1": {0: 10.0, 1: 8.0, 2: 2.0}}
    
    error = calculate_delivered_flexibility_error(dispatched, actuals)
    # t=0: abs(10-10) = 0
    # t=1: abs(10-8) = 2
    # t=2: abs(0-2) = 2
    # total = 4
    assert error == 4.0

def test_overcommitment():
    dispatched = {"res-1": {0: 10.0, 1: 10.0, 2: 10.0}}
    actuals = {"res-1": {0: 10.0, 1: 8.0, 2: 5.0}}
    
    # tolerance = 1.0
    oc = calculate_overcommitment(dispatched, actuals, 1.0)
    # t=0: 10 - (10+1) < 0 -> 0
    # t=1: 10 - (8+1) = 1
    # t=2: 10 - (5+1) = 4
    assert oc == 5.0

def test_overcommitment_zero_tolerance():
    dispatched = {"res-1": {0: 10.0}}
    actuals = {"res-1": {0: 8.0}}
    oc = calculate_overcommitment(dispatched, actuals, 0.0)
    assert oc == 2.0

def test_reliability():
    # Normal
    r1 = calculate_reliability({"r1": {0: 10.0}}, {"r1": {0: 8.0}})
    assert r1 == 0.8
    
    # Zero committed
    r2 = calculate_reliability({"r1": {0: 0.0}}, {"r1": {0: 0.0}})
    assert r2 == 1.0 # Safe fallback
    
    # Unreliable zero committed
    r3 = calculate_reliability({"r1": {0: 0.0}}, {"r1": {0: 5.0}})
    assert r3 == 0.0

def test_rebound():
    # Explicitly uncomputable for now
    assert calculate_rebound() is None

# --- Verifier Integration Tests ---

def create_scenario_input(min_p, max_p, req_kwh):
    start = datetime(2026, 1, 1)
    res = FlexibilityResource(
        id="res-1",
        type=ResourceType.EV,
        location_id="loc",
        rated_power_kw=10.0,
        earliest_start=start,
        latest_end=start,
        required_kwh=req_kwh,
        minimum_kwh=0.0,
        maximum_kwh=10.0,
        minimum_duration=0,
        maximum_duration=0,
        deadline=start,
        min_power=min_p,
        max_power=max_p,
        historical_response=[],
        override_rate=0.0,
        availability_rate=1.0
    )
    return SimulationInput(
        scenario=Scenario(scenario_id="1", resources=[res], disruption_specs={}, seeds={}),
        initial_resource_states={},
        renewable_demand_forecasts=[],
        dispatch_plan=DispatchPlan(dispatch_plan=[], objective_value=0, status=OptimizationStatus.OPTIMAL),
        system_constraints={}
    )

def test_verifier_pass():
    sim_input = create_scenario_input(0.0, 10.0, 5.0)
    sim_input.dispatch_plan.dispatch_plan = [
        DispatchInstruction(resource_id="res-1", time_step=0, power_kw=10.0),
        DispatchInstruction(resource_id="res-1", time_step=1, power_kw=10.0),
    ]
    
    sim_output = SimulationOutput(
        actual_response=[
            ActualResponse(resource_id="res-1", time_step=0, delivered_kw=10.0),
            ActualResponse(resource_id="res-1", time_step=1, delivered_kw=10.0)
        ],
        resource_state_evolution=[],
        renewable_outcomes=[],
        system_outcomes=[],
        event_records={}
    )
    
    verifier = SimulationVerifier()
    res = verifier.verify(sim_input, sim_output, tolerance_kw=0.5)
    
    assert res.passed
    assert res.constraint_violation_count == 0
    assert res.deadline_violation_count == 0
    assert res.overcommitment == 0.0
    assert res.reliability == 1.0

def test_verifier_deadline_violation():
    sim_input = create_scenario_input(0.0, 10.0, 5.0) # Requires 5 kWh
    sim_output = SimulationOutput(
        actual_response=[
            ActualResponse(resource_id="res-1", time_step=0, delivered_kw=10.0) # 2.5 kWh delivered
        ],
        resource_state_evolution=[],
        renewable_outcomes=[],
        system_outcomes=[],
        event_records={}
    )
    
    verifier = SimulationVerifier()
    res = verifier.verify(sim_input, sim_output, tolerance_kw=0.5)
    
    assert not res.passed
    assert res.deadline_violation_count == 1
    assert "missed required 5.0 kWh" in res.violations[0]

def test_verifier_constraint_violation():
    sim_input = create_scenario_input(5.0, 10.0, 5.0) # Min 5, Max 10
    sim_output = SimulationOutput(
        actual_response=[
            ActualResponse(resource_id="res-1", time_step=0, delivered_kw=4.0), # Below min
            ActualResponse(resource_id="res-1", time_step=1, delivered_kw=12.0) # Above max
        ],
        resource_state_evolution=[],
        renewable_outcomes=[],
        system_outcomes=[],
        event_records={}
    )
    
    verifier = SimulationVerifier()
    res = verifier.verify(sim_input, sim_output, tolerance_kw=0.5)
    
    assert not res.passed
    assert res.constraint_violation_count == 2
    assert "below min power 5.0" in res.violations[0]
    assert "exceeded max power 10.0" in res.violations[1]

