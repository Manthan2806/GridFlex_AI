import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


def test_simulate_endpoint_uses_experimental_ev_model():
    with TestClient(app) as client:
        response = client.post("/simulate/full")

    assert response.status_code == 200
    payload = response.json()
    assert payload["demo_mode"] is True
    assert payload["release_status"] == "accepted_for_offline_demo"
    assert payload["label"] == "offline demo estimate (hybrid/synthetic evidence)"
    assert len(payload["trust_states"]) == 3
    assert len(payload["dispatch_plan"]["dispatch_plan"]) == 3
    assert payload["dispatch_plan"]["status"] == "FEASIBLE"

    for state in payload["trust_states"]:
        assert state["trusted_kw"] <= state["expected_kw"] <= state["potential_kw"]

    dispatched_by_resource = {
        row["resource_id"]: row["power_kw"]
        for row in payload["dispatch_plan"]["dispatch_plan"]
    }
    trusted_total = sum(row["trusted_kw"] for row in payload["trust_states"])
    expected_scale = min(1.0, 15.0 / trusted_total)
    for state in payload["trust_states"]:
        assert dispatched_by_resource[state["resource_id"]] == pytest.approx(
            state["trusted_kw"] * expected_scale
        )
