from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Dict

from backend.app.domain.enums import OptimizationStatus, ResourceType
from backend.app.domain.models import FlexibilityResource
from backend.app.integrations.ai_ml_client import ExperimentalEVModelClient
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


def build_ev_scenario(event_time: datetime | None = None) -> Scenario:
    earliest_start = event_time or datetime.now(timezone.utc)
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


@lru_cache(maxsize=1)
def get_ev_model_client() -> ExperimentalEVModelClient:
    """Load the rejected candidate only in its explicitly allowed demo mode."""
    return ExperimentalEVModelClient(demo_mode=True)


def run_integrated_simulation() -> dict:
    """Run the demo from ML trust estimation through dispatch and simulation."""
    scenario = build_ev_scenario()
    model_client = get_ev_model_client()
    predictions = {
        resource.id: model_client.predict_resource(
            resource,
            scenario.resources[0].earliest_start,
            requested_dispatch_kw=resource.rated_power_kw,
        )
        for resource in scenario.resources
    }
    trusted_kw_values = {
        resource_id: prediction.trust_state.trusted_kw
        for resource_id, prediction in predictions.items()
    }
    dispatch_plan = build_dispatch_plan(trusted_kw_values)
    simulation_input = SimulationInput(
        scenario=scenario,
        initial_resource_states={},
        renewable_demand_forecasts=[],
        dispatch_plan=dispatch_plan,
        system_constraints={},
    )
    simulation_output: SimulationOutput = SimulationAdapter().run_simulation(simulation_input)
    first_prediction = next(iter(predictions.values()))

    return {
        "demo_mode": True,
        "label": first_prediction.label,
        "release_status": first_prediction.release_status,
        "warning": "Experimental EV estimate; not approved for real grid dispatch.",
        "trust_states": [
            {
                "resource_id": resource_id,
                **prediction.trust_state.model_dump(),
                "dispatch_group": prediction.dispatch_group,
                "used_demo_fallbacks": list(prediction.used_demo_fallbacks),
            }
            for resource_id, prediction in predictions.items()
        ],
        "dispatch_plan": dispatch_plan.model_dump(mode="json"),
        "simulation": simulation_output.model_dump(mode="json"),
    }
