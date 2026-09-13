from backend.app.services.water_heater_simulation import (
    demo_water_heaters,
    run_water_heater_simulation,
)


def test_demo_fleet_matches_household_training_scale() -> None:
    resources = demo_water_heaters()
    assert len(resources) == 5
    assert all(0 < resource.rated_power_kw < 5 for resource in resources)


def test_simulation_respects_small_feeder_capacity() -> None:
    result = run_water_heater_simulation(feeder_capacity_kw=0.05)
    assert result["total_dispatched_kw"] <= 0.05 + 1e-9
    assert result["total_delivered_kw"] <= result["total_dispatched_kw"]
    assert all(
        row["dispatched_kw"] <= row["trusted_kw"] + 1e-9
        for row in result["resources"]
    )
