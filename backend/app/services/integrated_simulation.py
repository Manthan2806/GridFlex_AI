from datetime import datetime, timedelta
from typing import Dict, Union

from backend.app.domain.enums import OptimizationStatus, ResourceType
from backend.app.domain.models import FlexibilityResource
from backend.app.schemas.dispatch import DispatchInstruction, DispatchPlan
from backend.app.schemas.runs import SimulationInput, SimulationOutput
from backend.app.schemas.scenarios import Scenario
from simulation.adapter import SimulationAdapter


FEEDER_CAPACITY_KW = 15.0
EV_DATA = (
    {
        "id": "ev-1",
        "rated_power_kw": 7.4,
        "required_kwh": 20.0,
        "availability_rate": 0.9,
        "override_rate": 0.05,
    },
    {
        "id": "ev-2",
        "rated_power_kw": 11.0,
        "required_kwh": 35.0,
        "availability_rate": 0.75,
        "override_rate": 0.2,
    },
    {
        "id": "ev-3",
        "rated_power_kw": 3.7,
        "required_kwh": 15.0,
        "availability_rate": 0.95,
        "override_rate": 0.02,
    },
)


def build_ev_scenario() -> Scenario:
    earliest_start = datetime.utcnow()
    latest_end = earliest_start + timedelta(hours=4)
    resources = [
        FlexibilityResource(
            id=ev["id"],
            type=ResourceType.EV,
            location_id="gridflex-feeder",
            rated_power_kw=ev["rated_power_kw"],
            earliest_start=earliest_start,
            latest_end=latest_end,
            required_kwh=ev["required_kwh"],
            minimum_kwh=0.0,
            maximum_kwh=ev["required_kwh"],
            minimum_duration=0,
            maximum_duration=240,
            deadline=latest_end,
            min_power=0.0,
            max_power=ev["rated_power_kw"],
            historical_response=[],
            override_rate=ev["override_rate"],
            availability_rate=ev["availability_rate"],
        )
        for ev in EV_DATA
    ]
    return Scenario(
        scenario_id="integrated-ev-scenario",
        resources=resources,
        disruption_specs={},
        seeds={},
    )


def build_dispatch_plan(trusted_kw_values: Dict[str, float]) -> DispatchPlan:
    total_trusted_kw = sum(trusted_kw_values.values())
    dispatch_scale = (
        1.0
        if total_trusted_kw <= FEEDER_CAPACITY_KW
        else FEEDER_CAPACITY_KW / total_trusted_kw
    )
    instructions = [
        DispatchInstruction(
            resource_id=ev["id"],
            # The adapter maps integer 0 to the scenario's earliest start.
            time_step=0,
            power_kw=trusted_kw_values[ev["id"]] * dispatch_scale,
        )
        for ev in EV_DATA
    ]
    return DispatchPlan(
        dispatch_plan=instructions,
        objective_value=sum(instruction.power_kw for instruction in instructions),
        status=OptimizationStatus.OPTIMAL,
    )


def _trusted_kw_values() -> Dict[str, float]:
    """Use the same trust calculation as the existing simplified endpoint."""
    values = {}
    for ev in EV_DATA:
        potential_kw = ev["rated_power_kw"]
        confidence = 1 - ev["override_rate"]
        expected_kw = potential_kw * ev["availability_rate"]
        values[ev["id"]] = potential_kw * ev["availability_rate"] * confidence
    return values


def run_integrated_simulation() -> Union[SimulationOutput, dict]:
    try:
        scenario = build_ev_scenario()
        dispatch_plan = build_dispatch_plan(_trusted_kw_values())
        simulation_input = SimulationInput(
            scenario=scenario,
            initial_resource_states={},
            renewable_demand_forecasts=[],
            dispatch_plan=dispatch_plan,
            system_constraints={},
        )
        return SimulationAdapter().run_simulation(simulation_input)
    except Exception as exc:
        return {"error": str(exc), "stage": "integrated_simulation"}
