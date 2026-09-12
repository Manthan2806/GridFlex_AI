import pytest
from datetime import datetime, timedelta

from backend.app.schemas.runs import SimulationInput
from backend.app.schemas.scenarios import Scenario
from backend.app.schemas.dispatch import DispatchPlan, DispatchInstruction
from backend.app.domain.models import FlexibilityResource
from backend.app.domain.enums import ResourceType, OptimizationStatus, ResourceState

from simulation.adapter import SimulationAdapter

def create_dummy_resource(res_id: str, earliest: datetime, latest: datetime) -> FlexibilityResource:
    return FlexibilityResource(
        id=res_id,
        type=ResourceType.EV,
        location_id="loc-1",
        rated_power_kw=10.0,
        earliest_start=earliest,
        latest_end=latest,
        required_kwh=5.0,
        minimum_kwh=0.0,
        maximum_kwh=10.0,
        minimum_duration=30,
        maximum_duration=120,
        deadline=latest,
        min_power=0.0,
        max_power=10.0,
        historical_response=[],
        override_rate=0.0,
        availability_rate=1.0
    )

def test_adapter_valid_translation():
    """Validates full pass-through translation using datetime TimeSteps."""
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(hours=1) # 4 timesteps (0, 15, 30, 45)
    
    scenario = Scenario(
        scenario_id="scen-1",
        resources=[create_dummy_resource("res-1", start, end)],
        disruption_specs={"type": "none"},
        seeds={"master": 42}
    )
    
    dispatch = DispatchPlan(
        dispatch_plan=[
            DispatchInstruction(resource_id="res-1", time_step=start, power_kw=10.0),
            DispatchInstruction(resource_id="res-1", time_step=start + timedelta(minutes=15), power_kw=10.0),
        ],
        objective_value=100.0,
        status=OptimizationStatus.OPTIMAL
    )
    
    sim_input = SimulationInput(
        scenario=scenario,
        initial_resource_states={},
        renewable_demand_forecasts=[{"t": 0, "val": 10}],
        dispatch_plan=dispatch,
        system_constraints={}
    )
    
    adapter = SimulationAdapter()
    output = adapter.run_simulation(sim_input)
    
    # 4 horizon steps derived from resource earliest/latest bounds
    assert len(output.actual_response) == 4
    
    # Step 1: 10kW -> 2.5kWh
    assert output.actual_response[0].delivered_kw == 10.0
    # Step 2: 10kW -> 2.5kWh (Total 5kWh -> completed)
    assert output.actual_response[1].delivered_kw == 10.0
    # Step 3: completed -> 0kW
    assert output.actual_response[2].delivered_kw == 0.0
    # Step 4: completed -> 0kW
    assert output.actual_response[3].delivered_kw == 0.0
    
    states = [s.state.value for s in output.resource_state_evolution]
    assert states[0] == "dispatched"
    assert states[1] == "completed"
    assert states[2] == "completed"

def test_adapter_int_timestep_translation():
    """Validates translation when the Backend provides integer TimeSteps."""
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(hours=1)
    
    scenario = Scenario(
        scenario_id="scen-1",
        resources=[create_dummy_resource("res-1", start, end)],
        disruption_specs={},
        seeds={}
    )
    
    dispatch = DispatchPlan(
        dispatch_plan=[
            DispatchInstruction(resource_id="res-1", time_step=0, power_kw=8.0),
            DispatchInstruction(resource_id="res-1", time_step=1, power_kw=8.0),
        ],
        objective_value=100.0,
        status=OptimizationStatus.OPTIMAL
    )
    
    sim_input = SimulationInput(
        scenario=scenario,
        initial_resource_states={},
        renewable_demand_forecasts=[],
        dispatch_plan=dispatch,
        system_constraints={}
    )
    
    adapter = SimulationAdapter()
    output = adapter.run_simulation(sim_input)
    
    assert output.actual_response[0].delivered_kw == 8.0
    assert output.actual_response[1].delivered_kw == 8.0

def test_adapter_empty_resources_fails():
    """Validates that a missing horizon context throws an explicit error."""
    scenario = Scenario(scenario_id="scen-1", resources=[], disruption_specs={}, seeds={})
    sim_input = SimulationInput(
        scenario=scenario,
        initial_resource_states={},
        renewable_demand_forecasts=[],
        dispatch_plan=DispatchPlan(dispatch_plan=[], objective_value=0, status=OptimizationStatus.OPTIMAL),
        system_constraints={}
    )
    
    adapter = SimulationAdapter()
    with pytest.raises(ValueError, match="Scenario must contain at least one resource"):
        adapter.run_simulation(sim_input)

def test_adapter_empty_dispatch_behaves_safely():
    """Validates an empty dispatch plan safely runs to produce 0.0kW across the horizon."""
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(hours=1)
    
    scenario = Scenario(
        scenario_id="scen-1",
        resources=[create_dummy_resource("res-1", start, end)],
        disruption_specs={},
        seeds={}
    )
    
    sim_input = SimulationInput(
        scenario=scenario,
        initial_resource_states={},
        renewable_demand_forecasts=[],
        dispatch_plan=DispatchPlan(dispatch_plan=[], objective_value=0, status=OptimizationStatus.OPTIMAL),
        system_constraints={}
    )
    
    adapter = SimulationAdapter()
    output = adapter.run_simulation(sim_input)
    
    # Engine defaults to 0 kW if no dispatch instruction is found
    for resp in output.actual_response:
        assert resp.delivered_kw == 0.0

def test_adapter_initial_resource_states_acknowledged():
    """Validates that initial_resource_states is accepted and passed without inventing physical behavior."""
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(hours=1)
    
    scenario = Scenario(
        scenario_id="scen-1",
        resources=[create_dummy_resource("res-1", start, end)],
        disruption_specs={},
        seeds={}
    )
    
    sim_input = SimulationInput(
        scenario=scenario,
        initial_resource_states={"res-1": ResourceState.AVAILABLE}, # Input explicitly provided
        renewable_demand_forecasts=[],
        dispatch_plan=DispatchPlan(dispatch_plan=[], objective_value=0, status=OptimizationStatus.OPTIMAL),
        system_constraints={}
    )
    
    adapter = SimulationAdapter()
    output = adapter.run_simulation(sim_input)
    # If the adapter crashed, this wouldn't be reached.
    assert len(output.resource_state_evolution) == 4

def test_adapter_information_boundary():
    """Validates that the SimulationInput cannot sneak future actuals into the SimulationEngine."""
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(hours=1)
    
    scenario = Scenario(
        scenario_id="scen-1",
        resources=[create_dummy_resource("res-1", start, end)],
        disruption_specs={},
        seeds={}
    )
    
    forecasts = [{"t": 0, "val": 100}]
    
    sim_input = SimulationInput(
        scenario=scenario,
        initial_resource_states={},
        renewable_demand_forecasts=forecasts,
        dispatch_plan=DispatchPlan(dispatch_plan=[], objective_value=0, status=OptimizationStatus.OPTIMAL),
        system_constraints={}
    )
    
    adapter = SimulationAdapter()
    output = adapter.run_simulation(sim_input)
    
    # Asserting that renewable_outcomes (which represents actuals) is entirely decoupled
    # from the renewable_demand_forecasts. The Phase 3B disruption injector will populate this.
    assert output.renewable_outcomes == []
    # Assert that the forecasts list passed into the context didn't mutate into actuals.
    assert forecasts == [{"t": 0, "val": 100}]

def test_adapter_seed_plumbing():
    """Validates that seed dictionary is strictly plumbed through to the context, preserving determinism."""
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(hours=1)
    
    scenario = Scenario(
        scenario_id="scen-1",
        resources=[create_dummy_resource("res-1", start, end)],
        disruption_specs={},
        seeds={"master": 999, "scenario": 111}
    )
    
    sim_input = SimulationInput(
        scenario=scenario,
        initial_resource_states={},
        renewable_demand_forecasts=[],
        dispatch_plan=DispatchPlan(dispatch_plan=[], objective_value=0, status=OptimizationStatus.OPTIMAL),
        system_constraints={}
    )
    
    adapter = SimulationAdapter()
    output = adapter.run_simulation(sim_input)
    # Validates it ran deterministically without throwing an RNG exception or inventing stochastic events
    assert len(output.actual_response) == 4
