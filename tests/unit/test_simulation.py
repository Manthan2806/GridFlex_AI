import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from simulation.clock import SimulationClock
from simulation.engine import SimulationEngine
from simulation.interfaces import ResourceBehaviorModel, ProvisionalDispatchInstruction, ProvisionalStepResult

class DummyResource(ResourceBehaviorModel):
    """A minimal dummy resource for testing the engine loop."""
    def __init__(self, resource_id: str):
        self._resource_id = resource_id
        self.call_count = 0
        self.last_instruction = None

    @property
    def resource_id(self) -> str:
        return self._resource_id

    def step(self, current_time: datetime, instruction: ProvisionalDispatchInstruction, context: Dict[str, Any]) -> ProvisionalStepResult:
        self.call_count += 1
        self.last_instruction = instruction
        # Dummy behavior: simply deliver exactly what was asked, up to 100kW
        delivered = min(instruction.power_kw, 100.0)
        return ProvisionalStepResult(self.resource_id, delivered_kw=delivered, state_updates={"call_count": self.call_count})


def test_clock_initialization_and_progression():
    start_time = datetime(2026, 1, 1, 0, 0, 0)
    horizon_steps = 4
    clock = SimulationClock(start_time, horizon_steps)

    assert clock.current_time == start_time
    assert not clock.is_complete()

    # Tick 1
    clock.tick()
    assert clock.current_time == start_time + timedelta(minutes=15)
    assert not clock.is_complete()

    # Tick 2, 3, 4
    clock.tick()
    clock.tick()
    clock.tick()

    assert clock.is_complete()
    assert clock.current_time == start_time + timedelta(minutes=60)

    with pytest.raises(RuntimeError):
        clock.tick()

def test_invalid_clock_initialization():
    start_time = datetime(2026, 1, 1, 0, 0, 0)
    with pytest.raises(ValueError):
        SimulationClock(start_time, -1)

def test_engine_execution_loop():
    start_time = datetime(2026, 1, 1, 0, 0, 0)
    horizon_steps = 3
    engine = SimulationEngine(start_time, horizon_steps)

    dummy_res = DummyResource("dummy-1")
    engine.register_resource(dummy_res)

    # Create dispatch plans for 3 steps
    dispatch_plans = [
        [ProvisionalDispatchInstruction("dummy-1", 50.0)],
        [ProvisionalDispatchInstruction("dummy-1", 120.0)],
        [] # Empty instructions for step 3, should default to 0
    ]

    context = {"temperature": 25.0}

    results = engine.run(dispatch_plans, context)

    assert len(results) == 3
    assert dummy_res.call_count == 3
    assert dummy_res.last_instruction.power_kw == 0.0 # Step 3 default

    # Verify step 1
    step_1 = results[0]
    assert step_1["step_index"] == 0
    assert step_1["time"] == start_time
    assert len(step_1["resource_results"]) == 1
    assert step_1["resource_results"][0].delivered_kw == 50.0

    # Verify step 2
    step_2 = results[1]
    assert step_2["step_index"] == 1
    assert step_2["time"] == start_time + timedelta(minutes=15)
    assert step_2["resource_results"][0].delivered_kw == 100.0 # Capped at 100 by DummyResource

    # Verify step 3
    step_3 = results[2]
    assert step_3["resource_results"][0].delivered_kw == 0.0

def test_engine_run_with_invalid_plan_length():
    start_time = datetime(2026, 1, 1, 0, 0, 0)
    engine = SimulationEngine(start_time, 2)
    
    # 3 plans provided but horizon is 2
    dispatch_plans = [[], [], []]
    
    with pytest.raises(ValueError, match="Expected 2 dispatch plans"):
        engine.run(dispatch_plans, {})

def test_deterministic_execution():
    start_time = datetime(2026, 1, 1, 0, 0, 0)
    horizon_steps = 2
    
    def run_sim():
        engine = SimulationEngine(start_time, horizon_steps)
        res = DummyResource("res-a")
        engine.register_resource(res)
        plans = [[ProvisionalDispatchInstruction("res-a", 10.0)], [ProvisionalDispatchInstruction("res-a", 20.0)]]
        return engine.run(plans, {})
        
    result_run1 = run_sim()
    result_run2 = run_sim()
    
    # Ensure exact same results
    assert len(result_run1) == len(result_run2)
    assert result_run1[0]["resource_results"][0].delivered_kw == result_run2[0]["resource_results"][0].delivered_kw
    assert result_run1[1]["resource_results"][0].delivered_kw == result_run2[1]["resource_results"][0].delivered_kw

def test_empty_resource_collection():
    start_time = datetime(2026, 1, 1, 0, 0, 0)
    horizon_steps = 2
    engine = SimulationEngine(start_time, horizon_steps)

    # No resources registered
    dispatch_plans = [[], []]
    
    results = engine.run(dispatch_plans, {})
    
    assert len(results) == 2
    assert len(results[0]["resource_results"]) == 0
    assert len(results[1]["resource_results"]) == 0
