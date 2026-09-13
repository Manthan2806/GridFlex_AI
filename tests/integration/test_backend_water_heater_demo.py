from fastapi.testclient import TestClient

from backend.app.main import app


def test_water_heater_endpoint_uses_locked_model_and_persists_run() -> None:
    with TestClient(app) as client:
        response = client.post("/simulate/water-heater")
        assert response.status_code == 200
        payload = response.json()

        assert payload["demo_mode"] is True
        assert payload["deployment_allowed"] is False
        assert payload["release_status"] == "accepted_for_hackathon_prototype"
        assert payload["label"] == "offline prototype estimate (fully synthetic evidence)"
        assert payload["simulation_mode"] == "deterministic_demo_not_field_measurement"
        assert len(payload["resources"]) == 5
        assert payload["total_dispatched_kw"] <= payload["feeder_capacity_kw"]

        for row in payload["resources"]:
            assert 0 <= row["trusted_kw"] <= row["expected_kw"] <= row["potential_kw"]
            assert row["dispatched_kw"] <= row["trusted_kw"] + 1e-9
            assert 0 <= row["confidence"] <= 1
            assert "tank_capacity_l" in row["used_demo_fallbacks"]

        run_id = payload["run_id"]
        listing = client.get("/runs/water-heater")
        assert listing.status_code == 200
        assert any(row["run_id"] == run_id for row in listing.json())

        detail = client.get(f"/runs/water-heater/{run_id}")
        assert detail.status_code == 200
        assert detail.json() == payload


def test_unknown_water_heater_run_returns_404() -> None:
    with TestClient(app) as client:
        response = client.get("/runs/water-heater/not-a-real-run")
    assert response.status_code == 404
    assert response.json()["detail"] == "Water-heater simulation run not found"
