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


def simulate_full():
    import os, sys
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from backend.app.services.integrated_simulation import run_integrated_simulation
    result = run_integrated_simulation()
    return result

@app.post("/simulate")
def simulate() -> dict:


    with SessionLocal() as session:
        ev_resources = list(session.scalars(select(EVResource).order_by(EVResource.id)))

        trust_states = []
        for ev in ev_resources:
            potential_kw = ev.rated_power_kw
            confidence = 1 - ev.override_rate
            expected_kw = ev.rated_power_kw * ev.availability_rate
            trusted_kw = expected_kw * confidence
            trust_states.append(
                {
                    "id": ev.id,
                    "potential_kw": potential_kw,
                    "expected_kw": expected_kw,
                    "trusted_kw": trusted_kw,
                    "confidence": confidence,
                    "availability_rate": ev.availability_rate,
                }
            )

        total_trusted_kw = sum(state["trusted_kw"] for state in trust_states)
        dispatch_scale = (
            1.0
            if total_trusted_kw <= FEEDER_CAPACITY_KW
            else FEEDER_CAPACITY_KW / total_trusted_kw
        )

        results = []
        total_dispatched_kw = 0.0
        total_delivered_kw = 0.0
        for state in trust_states:
            dispatched_kw = state["trusted_kw"] * dispatch_scale
            delivered_kw = dispatched_kw * state["availability_rate"]
            total_dispatched_kw += dispatched_kw
            total_delivered_kw += delivered_kw
            results.append(
                {
                    "id": state["id"],
                    "potential_kw": rounded(state["potential_kw"]),
                    "expected_kw": rounded(state["expected_kw"]),
                    "trusted_kw": rounded(state["trusted_kw"]),
                    "confidence": rounded(state["confidence"]),
                    "dispatched_kw": rounded(dispatched_kw),
                    "delivered_kw": rounded(delivered_kw),
                    "error_kw": rounded(dispatched_kw - delivered_kw),
                }
            )

        response = {
            "run_id": str(uuid4()),
            "feeder_capacity_kw": rounded(FEEDER_CAPACITY_KW),
            "total_trusted_kw": rounded(total_trusted_kw),
            "total_dispatched_kw": rounded(total_dispatched_kw),
            "total_delivered_kw": rounded(total_delivered_kw),
            "results": results,
        }
        try:
            from datetime import datetime
            from backend.app.services.peak_alignment import compute_peak_alignment_score
            response["peak_alignment_score"] = compute_peak_alignment_score(datetime.utcnow())
        except Exception:
            response["peak_alignment_score"] = None
        session.add(
            SimulationRun(
                run_id=response["run_id"],
                feeder_capacity_kw=response["feeder_capacity_kw"],
                total_dispatched_kw=response["total_dispatched_kw"],
                total_delivered_kw=response["total_delivered_kw"],
                results_json=json.dumps(results),
            )
        )
        session.commit()
        return response


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
            "feeder_capacity_kw": rounded(run.feeder_capacity_kw),
            "total_dispatched_kw": rounded(run.total_dispatched_kw),
            "total_delivered_kw": rounded(run.total_delivered_kw),
            "results": json.loads(run.results_json),
        }


@app.post("/simulate/full")
def simulate_full():
    import os, sys
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from backend.app.services.integrated_simulation import run_integrated_simulation
    result = run_integrated_simulation()
    return result
