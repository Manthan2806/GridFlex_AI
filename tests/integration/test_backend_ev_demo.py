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
    dispatch_rows = payload["dispatch_plan"]["dispatch_plan"]
    assert len(dispatch_rows) > 3
    assert len({row["time_step"] for row in dispatch_rows}) > 1
    assert payload["dispatch_plan"]["status"] == "FEASIBLE"
    assert payload["verification"]["passed"] is True
    assert payload["verification"]["violations"] == []

    for state in payload["trust_states"]:
        assert state["trusted_kw"] <= state["expected_kw"] <= state["potential_kw"]

    trusted_by_resource = {
        state["resource_id"]: state["trusted_kw"]
        for state in payload["trust_states"]
    }
    dispatched_by_time = {}
    for row in dispatch_rows:
        assert row["power_kw"] <= trusted_by_resource[row["resource_id"]] + 1e-9
        dispatched_by_time[row["time_step"]] = (
            dispatched_by_time.get(row["time_step"], 0.0) + row["power_kw"]
        )

    assert max(dispatched_by_time.values()) <= 15.0 + 1e-9
    for state in payload["trust_states"]:
        assert any(row["resource_id"] == state["resource_id"] for row in dispatch_rows)
