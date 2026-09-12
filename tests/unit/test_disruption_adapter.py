from datetime import datetime, timedelta, timezone

from backend.app.domain.enums import OptimizationStatus, ResourceType
from backend.app.domain.models import FlexibilityResource
from backend.app.schemas.dispatch import DispatchInstruction, DispatchPlan
from backend.app.schemas.runs import SimulationInput
from backend.app.schemas.scenarios import Scenario
from experiments.disruption_adapter import SeededEVDisruptionAdapter


def _simulation_input(*, availability_rate: float, override_rate: float) -> SimulationInput:
    start = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
    resource = FlexibilityResource(
        id="ev-test",
        type=ResourceType.EV,
        location_id="test-loc",
        rated_power_kw=7.2,
        earliest_start=start,
        latest_end=start + timedelta(minutes=30),
        required_kwh=3.6,
        minimum_kwh=0.0,
        maximum_kwh=3.6,
        minimum_duration=15,
        maximum_duration=30,
        deadline=start + timedelta(minutes=30),
        min_power=0.0,
        max_power=7.2,
        historical_response=[],
        override_rate=override_rate,
        availability_rate=availability_rate,
    )
    return SimulationInput(
        scenario=Scenario(
            scenario_id="seeded-disruption-test",
            resources=[resource],
            disruption_specs={},
            seeds={"master": 42},
        ),
        initial_resource_states={},
        renewable_demand_forecasts=[],
        dispatch_plan=DispatchPlan(
            dispatch_plan=[
                DispatchInstruction(
                    resource_id=resource.id,
                    time_step=start,
                    power_kw=7.2,
                ),
                DispatchInstruction(
                    resource_id=resource.id,
                    time_step=start + timedelta(minutes=15),
                    power_kw=7.2,
                ),
            ],
            objective_value=0.0,
            status=OptimizationStatus.FEASIBLE,
        ),
        system_constraints={},
    )


def test_same_seed_replays_identical_disruptions():
    sim_input = _simulation_input(availability_rate=0.5, override_rate=0.25)

    first = SeededEVDisruptionAdapter(seed=42).run_simulation(sim_input)
    second = SeededEVDisruptionAdapter(seed=42).run_simulation(sim_input)

    assert first.actual_response == second.actual_response
    assert first.event_records == second.event_records


def test_same_seed_applies_same_interruption_mask_to_different_dispatch_power():
    baseline_input = _simulation_input(availability_rate=0.5, override_rate=0.25)
    trust_input = baseline_input.model_copy(deep=True)
    for instruction in trust_input.dispatch_plan.dispatch_plan:
        instruction.power_kw = 3.6

    adapter = SeededEVDisruptionAdapter(seed=42)
    baseline = adapter.run_simulation(baseline_input)
    trust_aware = adapter.run_simulation(trust_input)

    baseline_interrupted = [
        response.delivered_kw == 0.0 for response in baseline.actual_response
    ]
    trust_interrupted = [
        response.delivered_kw == 0.0 for response in trust_aware.actual_response
    ]
    assert baseline_interrupted == trust_interrupted


def test_unavailable_ev_delivers_zero_and_records_event():
    result = SeededEVDisruptionAdapter(seed=42).run_simulation(
        _simulation_input(availability_rate=0.0, override_rate=0.0)
    )

    assert all(response.delivered_kw == 0.0 for response in result.actual_response)
    assert len(result.event_records["ev_disruptions"]) == 2
    assert all(
        event["reason"] == "unavailable"
        for event in result.event_records["ev_disruptions"]
    )


def test_fully_available_ev_preserves_ideal_delivery():
    result = SeededEVDisruptionAdapter(seed=42).run_simulation(
        _simulation_input(availability_rate=1.0, override_rate=0.0)
    )

    assert [response.delivered_kw for response in result.actual_response] == [7.2, 7.2]
    assert result.event_records["ev_disruptions"] == []
