# Run with:
# pip install fastapi uvicorn sqlalchemy
# uvicorn main:app --reload --port 8000

import json
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, select

try:
    from .db import Base, EVResource, SessionLocal, SimulationRun, engine
except ImportError:  # Supports `uvicorn main:app` from this directory.
    from db import Base, EVResource, SessionLocal, SimulationRun, engine

SEED_EVS = (
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

app = FastAPI(title="GridFlex AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def rounded(value: float) -> float:
    """Return API and persisted numeric values at the requested precision."""
    return round(value, 2)


@app.on_event("startup")
def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        has_resources = session.scalar(select(EVResource.id).limit(1)) is not None
        if not has_resources:
            session.add_all(EVResource(**resource) for resource in SEED_EVS)
            session.commit()


@app.get("/runs")
def list_runs() -> list[dict]:
    with SessionLocal() as session:
        runs = session.scalars(
            select(SimulationRun).order_by(desc(SimulationRun.created_at))
        )
        return [
            {
                "run_id": run.run_id,
                "created_at": run.created_at.isoformat(),
                "total_dispatched_kw": rounded(run.total_dispatched_kw),
                "total_delivered_kw": rounded(run.total_delivered_kw),
            }
            for run in runs
        ]


@app.get("/runs/{run_id}")
def get_run(run_id: str) -> dict:
    with SessionLocal() as session:
        run = session.get(SimulationRun, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Simulation run not found")
        return {
            "run_id": run.run_id,
            "created_at": run.created_at.isoformat(),
            "total_dispatched_kw": rounded(run.total_dispatched_kw),
            "total_delivered_kw": rounded(run.total_delivered_kw),
            "results": json.loads(run.results_json),
        }


from datetime import datetime, timedelta, timezone
from typing import List
from backend.app.schemas.scenarios import Scenario
from backend.app.domain.enums import ResourceType, ResourceState
from backend.app.domain.models import FlexibilityResource
from backend.app.schemas.runs import SimulationInput
from backend.app.services.dispatch_service import MVPOptimizer
from backend.app.services.trust_hydration import build_optimizer_context, hydrate_trust_context

from backend.app.services.verification_service import SimulationVerifier
from experiments.runner import ExperimentRunner, ExperimentComparison

from backend.app.integrations.ai_ml_client import ExperimentalEVModelClient
from simulation.adapter import SimulationAdapter

class ResourceResponse(FlexibilityResource):
    potential_kw: float
    expected_kw: float
    trusted_kw: float
    confidence: float
    state: ResourceState

def _get_canonical_resources(start: datetime, latest_end: datetime) -> List[FlexibilityResource]:
    resources = []
    for ev in SEED_EVS:
        resources.append(
            FlexibilityResource(
                id=ev["id"],
                type=ResourceType.EV,
                location_id="gridflex-feeder",
                rated_power_kw=ev["rated_power_kw"],
                earliest_start=start,
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
        )
    return resources

@app.get("/resources", response_model=List[ResourceResponse])
def get_resources():
    start = datetime.now(timezone.utc)
    latest_end = start + timedelta(hours=4)
    resources = _get_canonical_resources(start, latest_end)
    
    client = ExperimentalEVModelClient(demo_mode=True)
    trust_data = hydrate_trust_context(client, resources, start)
    
    response_list = []
    for res in resources:
        trust = trust_data[res.id]
        res_dict = res.model_dump()
        res_dict.update({
            "potential_kw": rounded(trust.potential_kw),
            "expected_kw": rounded(trust.expected_kw),
            "trusted_kw": rounded(trust.trusted_kw),
            "confidence": rounded(trust.confidence),
            "state": ResourceState.AVAILABLE
        })
        response_list.append(ResourceResponse(**res_dict))
    
    return response_list

from backend.app.domain.enums import OptimizationStatus
from backend.app.schemas.dispatch_api import (
    DispatchResponse,
    DispatchResponseScenario,
    DispatchFlexibilityState,
    RecommendedDispatch,
    DispatchResource,
    ConstraintCheckResult
)

@app.get("/dispatch", response_model=DispatchResponse)
def get_dispatch():
    start = datetime.now(timezone.utc)
    latest_end = start + timedelta(hours=4)
    resources = _get_canonical_resources(start, latest_end)
    
    scenario = Scenario(
        scenario_id="dispatch-scenario-canonical",
        resources=resources,
        disruption_specs={},
        seeds={}
    )
    
    client = ExperimentalEVModelClient(demo_mode=True)
    ctx = build_optimizer_context(client, resources, start)
    
    optimizer = MVPOptimizer()
    plan = optimizer.generate_dispatch_plan(scenario, "trusted_kw", ctx)
    
    # Flexibility summary
    trust_data = ctx.get("trust_data", {})
    total_potential = sum(t.potential_kw for t in trust_data.values())
    total_expected = sum(t.expected_kw for t in trust_data.values())
    total_trusted = sum(t.trusted_kw for t in trust_data.values())
    confidence = (total_trusted / total_expected) if total_expected > 0 else 0.0
    
    flexibility = DispatchFlexibilityState(
        potentialKw=rounded(total_potential),
        expectedKw=rounded(total_expected),
        trustedKw=rounded(total_trusted),
        confidence=rounded(confidence)
    )
    
    # Recommended Dispatch
    # Get max power per resource from instructions
    res_power = {}
    min_time = None
    max_time = None
    for inst in plan.dispatch_plan:
        res_power[inst.resource_id] = max(res_power.get(inst.resource_id, 0.0), inst.power_kw)
        if min_time is None or inst.time_step < min_time:
            min_time = inst.time_step
        if max_time is None or inst.time_step > max_time:
            max_time = inst.time_step
            
    time_window = f"{min_time.isoformat()}/{max_time.isoformat()}" if min_time and max_time else f"{start.isoformat()}/{latest_end.isoformat()}"
    
    dispatch_resources = []
    for r in resources:
        dispatched_kw = res_power.get(r.id, 0.0)
        state = "dispatched" if dispatched_kw > 0.0 else "available"
        dispatch_resources.append(DispatchResource(
            id=r.id,
            name=f"{r.type.value.capitalize()} {r.id}",
            type=r.type.value,
            dispatchedKw=rounded(dispatched_kw),
            state=state
        ))
        
    recommended_dispatch = RecommendedDispatch(
        id=str(uuid4()),
        timeWindow=time_window,
        resources=dispatch_resources,
        totalDispatchedKw=rounded(sum(res_power.values())),
        rationale="Canonical MVP Optimization based on trusted capacity.",
        status="recommendation_ready" if plan.status == OptimizationStatus.FEASIBLE else "infeasible"
    )
    
    # Constraint Check
    passed = (plan.status == OptimizationStatus.FEASIBLE)
    violations = []
    if plan.infeasibility_report:
        violations = [plan.infeasibility_report]
        
    constraint_check = ConstraintCheckResult(
        constraints=["Canonical optimizer constraints"],
        violations=violations,
        deadlineViolations=[],
        passed=passed
    )
    
    return DispatchResponse(
        scenario=DispatchResponseScenario(id=scenario.scenario_id),
        flexibility=flexibility,
        recommendedDispatch=recommended_dispatch,
        constraintCheck=constraint_check
    )

@app.post("/simulate")
@app.post("/simulate/full")
def simulate_full():
    start = datetime.now(timezone.utc)
    latest_end = start + timedelta(hours=4)
    resources = _get_canonical_resources(start, latest_end)
        
    scenario = Scenario(
        scenario_id="simulate-full-canonical",
        resources=resources,
        disruption_specs={},
        seeds={}
    )
    
    client = ExperimentalEVModelClient(demo_mode=True)
    ctx = build_optimizer_context(client, resources, start)
    
    optimizer = MVPOptimizer()
    plan = optimizer.generate_dispatch_plan(scenario, "trusted_kw", ctx)
    
    sim_input = SimulationInput(
        scenario=scenario,
        initial_resource_states={},
        renewable_demand_forecasts=[],
        dispatch_plan=plan,
        system_constraints={},
    )
    
    adapter = SimulationAdapter()
    sim_output = adapter.run_simulation(sim_input)
    
    total_dispatched_kw = sum(instruction.power_kw for instruction in plan.dispatch_plan)
    total_delivered_kw = sum(resp.delivered_kw for resp in sim_output.actual_response)
    
    run_id = str(uuid4())
    results_dict = sim_output.model_dump()
    
    # Exclude non-serializable datetimes or standard Pydantic dumps serialize them?
    # model_dump() returns datetimes which json.dumps can't handle natively unless customized.
    # Instead, we can use sim_output.model_dump_json() to get a valid JSON string directly!
    results_json = sim_output.model_dump_json()
    
    with SessionLocal() as session:
        session.add(
            SimulationRun(
                run_id=run_id,
                total_dispatched_kw=total_dispatched_kw,
                total_delivered_kw=total_delivered_kw,
                results_json=results_json,
            )
        )
        session.commit()
    
    return json.loads(results_json)


@app.post("/experiments/run", response_model=ExperimentComparison)
def run_experiment():
    start = datetime.now(timezone.utc)
    latest_end = start + timedelta(hours=4)
    resources = _get_canonical_resources(start, latest_end)
        
    scenario = Scenario(
        scenario_id="experiment-canonical",
        resources=resources,
        disruption_specs={},
        seeds={}
    )
    
    client = ExperimentalEVModelClient(demo_mode=True)
    ctx = build_optimizer_context(client, resources, start)
    
    optimizer = MVPOptimizer()
    adapter = SimulationAdapter()
    verifier = SimulationVerifier()
    
    runner = ExperimentRunner(strategy=optimizer, verifier=verifier, adapter=adapter)
    
    comparison = runner.run_paired_experiment(
        scenario=scenario,
        renewable_demand_forecasts=[],
        context=ctx
    )
    
    return comparison
