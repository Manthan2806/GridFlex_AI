"""GridFlex AI hackathon API.

Run from the repository root with:
    uvicorn backend.app.main:app --reload --port 8000
"""

from __future__ import annotations

import json
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, select

from backend.app.db import (
    Base,
    EVResource,
    SessionLocal,
    SimulationRun,
    WaterHeaterSimulationRun,
    engine,
)
from backend.app.integrations.ai_ml_client import EVModelIntegrationError
from backend.app.integrations.water_heater_ml_client import (
    WaterHeaterModelIntegrationError,
)
from backend.app.services.integrated_simulation import run_integrated_simulation
from backend.app.services.water_heater_simulation import run_water_heater_simulation


FEEDER_CAPACITY_KW = 15.0
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

app = FastAPI(title="GridFlex AI", version="0.1.0-demo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        has_resources = session.scalar(select(EVResource.id).limit(1)) is not None
        if not has_resources:
            session.add_all(EVResource(**resource) for resource in SEED_EVS)
            session.commit()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "mode": "experimental_demo",
        "model_deployment_allowed": False,
    }


def _save_run(result: dict) -> dict:
    run_id = str(uuid4())
    dispatch_rows = result["dispatch_plan"]["dispatch_plan"]
    response_rows = result["simulation"]["actual_response"]

    def peak_power(rows: list[dict], value_key: str) -> float:
        totals_by_time: dict[str, float] = {}
        for row in rows:
            time_key = str(row["time_step"])
            totals_by_time[time_key] = (
                totals_by_time.get(time_key, 0.0) + float(row[value_key])
            )
        return max(totals_by_time.values(), default=0.0)

    total_dispatched_kw = peak_power(dispatch_rows, "power_kw")
    total_delivered_kw = peak_power(response_rows, "delivered_kw")
    result = {"run_id": run_id, **result}

    with SessionLocal() as session:
        session.add(
            SimulationRun(
                run_id=run_id,
                feeder_capacity_kw=FEEDER_CAPACITY_KW,
                total_dispatched_kw=total_dispatched_kw,
                total_delivered_kw=total_delivered_kw,
                results_json=json.dumps(result),
            )
        )
        session.commit()
    return result


@app.post("/simulate")
@app.post("/simulate/full")
def simulate_full() -> dict:
    """Use experimental ML trust estimates, then dispatch and simulate the EVs."""
    try:
        return _save_run(run_integrated_simulation())
    except EVModelIntegrationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


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
                "total_dispatched_kw": round(run.total_dispatched_kw, 2),
                "total_delivered_kw": round(run.total_delivered_kw, 2),
            }
            for run in runs
        ]


@app.post("/simulate/water-heater")
def simulate_water_heater() -> dict:
    """Run the saved water-heater model in explicit offline prototype mode."""
    try:
        result = run_water_heater_simulation()
    except WaterHeaterModelIntegrationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    run_id = str(uuid4())
    result = {"run_id": run_id, **result}
    with SessionLocal() as session:
        session.add(
            WaterHeaterSimulationRun(
                run_id=run_id,
                feeder_capacity_kw=float(result["feeder_capacity_kw"]),
                total_dispatched_kw=float(result["total_dispatched_kw"]),
                total_delivered_kw=float(result["total_delivered_kw"]),
                results_json=json.dumps(result),
            )
        )
        session.commit()
    return result


@app.get("/runs/water-heater")
def list_water_heater_runs() -> list[dict]:
    with SessionLocal() as session:
        runs = session.scalars(
            select(WaterHeaterSimulationRun).order_by(
                desc(WaterHeaterSimulationRun.created_at)
            )
        )
        return [
            {
                "run_id": run.run_id,
                "created_at": run.created_at.isoformat(),
                "total_dispatched_kw": round(run.total_dispatched_kw, 6),
                "total_delivered_kw": round(run.total_delivered_kw, 6),
            }
            for run in runs
        ]


@app.get("/runs/water-heater/{run_id}")
def get_water_heater_run(run_id: str) -> dict:
    with SessionLocal() as session:
        run = session.get(WaterHeaterSimulationRun, run_id)
        if run is None:
            raise HTTPException(
                status_code=404, detail="Water-heater simulation run not found"
            )
        return json.loads(run.results_json)


@app.get("/runs/{run_id}")
def get_run(run_id: str) -> dict:
    with SessionLocal() as session:
        run = session.get(SimulationRun, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Simulation run not found")
        return json.loads(run.results_json)
