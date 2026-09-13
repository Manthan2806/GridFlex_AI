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
from backend.app.schemas.scenarios import Scenario
from backend.app.domain.enums import ResourceType
from backend.app.domain.models import FlexibilityResource
from backend.app.schemas.runs import SimulationInput
from backend.app.services.dispatch_service import MVPOptimizer
from backend.app.services.trust_hydration import build_optimizer_context
from backend.app.integrations.ai_ml_client import ExperimentalEVModelClient
from simulation.adapter import SimulationAdapter

@app.post("/simulate/full")
def simulate_full():
    start = datetime.now(timezone.utc)
    latest_end = start + timedelta(hours=4)
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
