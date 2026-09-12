import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from backend.app.schemas.scenarios import Scenario
from backend.app.schemas.dispatch import DispatchPlan, DispatchInstruction
from backend.app.domain.models import FlexibilityResource
from backend.app.domain.enums import ResourceType, OptimizationStatus

from simulation.adapter import SimulationAdapter
from tests.validation.verifier import SimulationVerifier
from experiments.runner import ExperimentRunner, StrategyBoundary

class DummyStrategy(StrategyBoundary):
    def __init__(self, reject_trust: bool = False):
        self.reject_trust = reject_trust
        
    def generate_dispatch_plan(self, scenario: Scenario, strategy_basis: str, context: Dict[str, Any]) -> DispatchPlan:
        if strategy_basis == "trusted_kw" and self.reject_trust:
            raise ValueError("Trusted data unavailable")
            
        # Generates a safe dummy plan dispatching 10kW at t=0
        start = scenario.resources[0].earliest_start
        return DispatchPlan(
            dispatch_plan=[DispatchInstruction(resource_id=scenario.resources[0].id, time_step=start, power_kw=10.0)],
            objective_value=100.0,
            status=OptimizationStatus.OPTIMAL
        )

def create_valid_scenario() -> Scenario:
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(hours=1)
    res = FlexibilityResource(
        id="res-1",
        type=ResourceType.EV,
        location_id="loc-1",
        rated_power_kw=10.0,
        earliest_start=start,
        latest_end=end,
        required_kwh=2.5,
        minimum_kwh=0.0,
        maximum_kwh=10.0,
        minimum_duration=30,
        maximum_duration=120,
        deadline=end,
        min_power=0.0,
        max_power=10.0,
        historical_response=[],
        override_rate=0.0,
        availability_rate=1.0
    )
    return Scenario(
        scenario_id="scen-1",
        resources=[res],
        disruption_specs={},
        seeds={"master": 42}
    )

def test_runner_paired_experiment_success():
    runner = ExperimentRunner(
        strategy=DummyStrategy(),
        verifier=SimulationVerifier(),
        adapter=SimulationAdapter()
    )
    
    scenario = create_valid_scenario()
    result = runner.run_paired_experiment(
        scenario=scenario,
        renewable_demand_forecasts=[],
        tolerance_kw=0.0
    )
    
    assert result.horizon_validated is True
    assert result.experiment_seed == 42
    assert result.scenario_id == "scen-1"
    
    # Both baseline and trust_aware should have passed the verification
    assert result.baseline_result is not None
    assert result.baseline_result.passed is True
    assert result.baseline_result.delivered_flexibility_error == 0.0 # Delivered exactly 10kW as dispatched
    
    assert result.trust_aware_result is not None
    assert result.trust_aware_result.passed is True

def test_runner_handles_missing_trusted_kw():
    runner = ExperimentRunner(
        strategy=DummyStrategy(reject_trust=True),
        verifier=SimulationVerifier(),
        adapter=SimulationAdapter()
    )
    
    result = runner.run_paired_experiment(
        scenario=create_valid_scenario(),
        renewable_demand_forecasts=[]
    )
    
    assert result.baseline_result is not None
    assert result.trust_aware_result is None # Gracefully handled missing AI/ML data

def test_runner_invalid_horizon_rejected():
    runner = ExperimentRunner(
        strategy=DummyStrategy(),
        verifier=SimulationVerifier(),
        adapter=SimulationAdapter()
    )
    
    scenario = create_valid_scenario()
    # Break the temporal bounds
    scenario.resources[0].latest_end = scenario.resources[0].earliest_start
    
    with pytest.raises(ValueError, match="invalid or insufficient to cover resource deadlines"):
        runner.run_paired_experiment(scenario=scenario, renewable_demand_forecasts=[])

def test_runner_empty_scenario_rejected():
    runner = ExperimentRunner(
        strategy=DummyStrategy(),
        verifier=SimulationVerifier(),
        adapter=SimulationAdapter()
    )
    
    scenario = create_valid_scenario()
    scenario.resources = []
    
    with pytest.raises(ValueError, match="invalid or insufficient to cover resource deadlines"):
        runner.run_paired_experiment(scenario=scenario, renewable_demand_forecasts=[])
