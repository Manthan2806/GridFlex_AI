import pytest
from datetime import datetime, timedelta

from simulation.models.generic import EnergyConstrainedResourceModel
from simulation.interfaces import ProvisionalDispatchInstruction
from simulation.engine import SimulationEngine

def test_zero_dispatch_produces_zero_energy():
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(hours=2)
    model = EnergyConstrainedResourceModel(
        resource_id="res-1",
        min_power=0.0,
        max_power=10.0,
        required_kwh=5.0,
        earliest_start=start,
        latest_end=end
    )
    
    inst = ProvisionalDispatchInstruction("res-1", 0.0)
    result = model.step(start, inst, {})
    
    assert result.delivered_kw == 0.0
    assert model.remaining_kwh == 5.0
    assert result.state_updates["lifecycle_state"] == "available"

def test_valid_dispatch_15_min_accounting():
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(hours=2)
    model = EnergyConstrainedResourceModel(
        resource_id="res-1",
        min_power=0.0,
        max_power=10.0,
        required_kwh=5.0,
        earliest_start=start,
        latest_end=end
    )
    
    inst = ProvisionalDispatchInstruction("res-1", 8.0)
    result = model.step(start, inst, {})
    
    assert result.delivered_kw == 8.0
    # 8.0 kW * 0.25 h = 2.0 kWh
    assert model.remaining_kwh == 3.0
    assert result.state_updates["lifecycle_state"] == "dispatched"

def test_repeated_timesteps_reduce_remaining_correctly():
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(hours=2)
    model = EnergyConstrainedResourceModel(
        resource_id="res-1",
        min_power=0.0,
        max_power=10.0,
        required_kwh=5.0,
        earliest_start=start,
        latest_end=end
    )
    
    # Step 1: 4kW -> 1kWh
    inst1 = ProvisionalDispatchInstruction("res-1", 4.0)
    res1 = model.step(start, inst1, {})
    assert res1.delivered_kw == 4.0
    assert model.remaining_kwh == 4.0
    
    # Step 2: 8kW -> 2kWh
    inst2 = ProvisionalDispatchInstruction("res-1", 8.0)
    res2 = model.step(start + timedelta(minutes=15), inst2, {})
    assert res2.delivered_kw == 8.0
    assert model.remaining_kwh == 2.0

def test_outside_availability_window():
    start = datetime(2026, 1, 1, 8, 0, 0)
    end = datetime(2026, 1, 1, 10, 0, 0)
    model = EnergyConstrainedResourceModel(
        resource_id="res-1",
        min_power=0.0,
        max_power=10.0,
        required_kwh=5.0,
        earliest_start=start,
        latest_end=end
    )
    
    inst = ProvisionalDispatchInstruction("res-1", 10.0)
    
    # Before earliest start
    res_before = model.step(datetime(2026, 1, 1, 7, 45, 0), inst, {})
    assert res_before.delivered_kw == 0.0
    assert res_before.state_updates["lifecycle_state"] == "unavailable"
    assert model.remaining_kwh == 5.0

    # After latest end
    res_after = model.step(datetime(2026, 1, 1, 10, 0, 0), inst, {})
    assert res_after.delivered_kw == 0.0
    assert res_after.state_updates["lifecycle_state"] == "unavailable"
    assert model.remaining_kwh == 5.0

def test_power_limits_respected():
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(hours=2)
    model = EnergyConstrainedResourceModel(
        resource_id="res-1",
        min_power=2.0,
        max_power=8.0,
        required_kwh=10.0,
        earliest_start=start,
        latest_end=end
    )
    
    # Below min power
    res_below = model.step(start, ProvisionalDispatchInstruction("res-1", 1.0), {})
    assert res_below.delivered_kw == 2.0 # Clipped to min
    
    # Above max power
    res_above = model.step(start + timedelta(minutes=15), ProvisionalDispatchInstruction("res-1", 12.0), {})
    assert res_above.delivered_kw == 8.0 # Clipped to max

def test_completion_and_no_accumulation():
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(hours=2)
    model = EnergyConstrainedResourceModel(
        resource_id="res-1",
        min_power=0.0,
        max_power=10.0,
        required_kwh=2.0,
        earliest_start=start,
        latest_end=end
    )
    
    # Dispatched for 10kW -> 2.5kWh. But only 2kWh required.
    # Should deliver 8kW (8 * 0.25 = 2.0 kWh).
    res1 = model.step(start, ProvisionalDispatchInstruction("res-1", 10.0), {})
    assert res1.delivered_kw == 8.0
    assert model.remaining_kwh == 0.0
    assert res1.state_updates["lifecycle_state"] == "completed"
    
    # Next step, try to dispatch again. Should return 0.
    res2 = model.step(start + timedelta(minutes=15), ProvisionalDispatchInstruction("res-1", 10.0), {})
    assert res2.delivered_kw == 0.0
    assert model.remaining_kwh == 0.0
    assert res2.state_updates["lifecycle_state"] == "completed"

def test_deterministic_replay():
    start = datetime(2026, 1, 1, 0, 0, 0)
    end = start + timedelta(hours=2)
    
    def run_scenario():
        model = EnergyConstrainedResourceModel(
            resource_id="res-1",
            min_power=0.0,
            max_power=10.0,
            required_kwh=5.0,
            earliest_start=start,
            latest_end=end
        )
        r1 = model.step(start, ProvisionalDispatchInstruction("res-1", 6.0), {})
        r2 = model.step(start + timedelta(minutes=15), ProvisionalDispatchInstruction("res-1", 12.0), {})
        return r1.delivered_kw, r2.delivered_kw, model.remaining_kwh

    run1 = run_scenario()
    run2 = run_scenario()
    
    assert run1 == run2

def test_engine_integration():
    start = datetime(2026, 1, 1, 8, 0, 0)
    engine = SimulationEngine(start, 4)
    model = EnergyConstrainedResourceModel(
        resource_id="res-1",
        min_power=0.0,
        max_power=10.0,
        required_kwh=3.0,
        earliest_start=start,
        latest_end=start + timedelta(hours=1)
    )
    engine.register_resource(model)
    
    plans = [
        [ProvisionalDispatchInstruction("res-1", 8.0)],  # 2kWh
        [ProvisionalDispatchInstruction("res-1", 0.0)],  # 0kWh
        [ProvisionalDispatchInstruction("res-1", 8.0)],  # Wants 2kWh, but only 1kWh left -> 4.0kW
        [ProvisionalDispatchInstruction("res-1", 8.0)],  # Completed -> 0kW
    ]
    
    results = engine.run(plans, {})
    
    assert results[0]["resource_results"][0].delivered_kw == 8.0
    assert results[1]["resource_results"][0].delivered_kw == 0.0
    assert results[2]["resource_results"][0].delivered_kw == 4.0
    assert results[3]["resource_results"][0].delivered_kw == 0.0
    assert model.remaining_kwh == 0.0
