from datetime import datetime, timedelta, timezone
from functools import lru_cache

from backend.app.domain.enums import OptimizationStatus, ResourceType
from backend.app.domain.models import FlexibilityResource
from backend.app.integrations.ai_ml_client import (
    EVModelIntegrationError,
    OfflineDemoEVModelClientV2,
)
from backend.app.schemas.runs import SimulationInput, SimulationOutput
from backend.app.schemas.scenarios import Scenario
from backend.app.services.dispatch_service import MVPOptimizer
from backend.app.services.verification_service import SimulationVerifier
from simulation.adapter import SimulationAdapter


FEEDER_CAPACITY_KW = 15.0
EV_DATA = (
    {
        "id": "ev-1",
        "rated_power_kw": 7.4,
        "required_kwh": 8.0,
        "availability_rate": 0.9,
        "override_rate": 0.05,
    },
    {
        "id": "ev-2",
        "rated_power_kw": 11.0,
        "required_kwh": 12.0,
        "availability_rate": 0.75,
        "override_rate": 0.2,
    },
    {
        "id": "ev-3",
        "rated_power_kw": 3.7,
        "required_kwh": 6.0,
        "availability_rate": 0.95,
        "override_rate": 0.02,
    },
)


def build_ev_scenario(event_time: datetime | None = None) -> Scenario:
    raw_start = event_time or datetime.now(timezone.utc)
    earliest_start = raw_start.replace(
        minute=(raw_start.minute // 15) * 15,
        second=0,
        microsecond=0,
    )
    latest_end = earliest_start + timedelta(hours=8)
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
            maximum_duration=480,
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


@lru_cache(maxsize=1)
def get_ev_model_client() -> OfflineDemoEVModelClientV2:
    """Load the source-disjoint-holdout-approved v2 artifact in demo mode."""
    return OfflineDemoEVModelClientV2(demo_mode=True)


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
    trust_data = {
        resource_id: prediction.trust_state
        for resource_id, prediction in predictions.items()
    }
    dispatch_plan = MVPOptimizer().generate_dispatch_plan(
        scenario,
        strategy_basis="trusted_kw",
        context={"trust_data": trust_data},
    )
    if dispatch_plan.status != OptimizationStatus.FEASIBLE:
        raise EVModelIntegrationError(
            "Trusted EV dispatch is infeasible: "
            f"{dispatch_plan.infeasibility_report or 'no details available'}"
        )

    dispatch_by_time: dict[object, float] = {}
    for instruction in dispatch_plan.dispatch_plan:
        dispatch_by_time[instruction.time_step] = (
            dispatch_by_time.get(instruction.time_step, 0.0) + instruction.power_kw
        )
    peak_dispatch_kw = max(dispatch_by_time.values(), default=0.0)
    if peak_dispatch_kw > FEEDER_CAPACITY_KW + 1e-9:
        raise EVModelIntegrationError(
            f"Dispatch peak {peak_dispatch_kw:.3f} kW exceeds the "
            f"{FEEDER_CAPACITY_KW:.3f} kW feeder capacity"
        )

    simulation_input = SimulationInput(
        scenario=scenario,
        initial_resource_states={},
        renewable_demand_forecasts=[],
        dispatch_plan=dispatch_plan,
        system_constraints={"feeder_capacity_kw": FEEDER_CAPACITY_KW},
    )
    simulation_output: SimulationOutput = SimulationAdapter().run_simulation(simulation_input)
    verification = SimulationVerifier().verify(
        simulation_input,
        simulation_output,
        tolerance_kw=0.01,
    )
    if not verification.passed:
        raise EVModelIntegrationError(
            "Integrated simulation failed verification: "
            + "; ".join(verification.violations)
        )
    first_prediction = next(iter(predictions.values()))

    return {
        "demo_mode": True,
        "feeder_capacity_kw": FEEDER_CAPACITY_KW,
        "scenario": scenario.model_dump(mode="json"),
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
        "verification": verification.model_dump(mode="json"),
    }
