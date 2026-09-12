import pytest
from datetime import datetime, timedelta, timezone

from backend.app.domain.enums import OptimizationStatus, ResourceType
from backend.app.domain.models import FlexibilityResource
from backend.app.schemas.scenarios import Scenario
from backend.app.integrations.ai_ml_client import OfflineDemoEVModelClientV2
from backend.app.services.trust_hydration import build_optimizer_context
from backend.app.services.dispatch_service import MVPOptimizer
from simulation.adapter import SimulationAdapter
from backend.app.services.verification_service import SimulationVerifier
from experiments.runner import ExperimentRunner

def _make_resource(res_id: str, max_power: float = 7.2, required_kwh: float = 4.0) -> FlexibilityResource:
    start = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
    return FlexibilityResource(
        id=res_id,
        type=ResourceType.EV,
        location_id="test-loc",
        rated_power_kw=max_power,
        earliest_start=start,
        latest_end=start + timedelta(hours=8),
        required_kwh=required_kwh,
        minimum_kwh=0.0,
        maximum_kwh=20.0,
        minimum_duration=15,
        maximum_duration=480,
        deadline=start + timedelta(hours=8),
        min_power=0.0,
        max_power=max_power,
        historical_response=[],
        override_rate=0.0,
        availability_rate=1.0,
    )

def test_mvp_e2e_experiment_runner():
    """
    Proves the full MVP pipeline:
    Scenario -> AI/ML -> TrustState -> Baseline + Trust-aware optimizer
    -> DispatchPlans -> SimulationAdapter -> Verification -> Comparison
    """
    resources = [
        _make_resource("ev-e2e-001"),
        _make_resource("ev-e2e-002")
    ]
    scenario = Scenario(
        scenario_id="scen-e2e-test",
        resources=resources,
        disruption_specs={},
        seeds={"master": 99}
    )
    event_time = resources[0].earliest_start

    # 1. AI/ML Inference
    client = OfflineDemoEVModelClientV2(demo_mode=True)
    ctx = build_optimizer_context(client, resources, event_time)

    assert len(ctx["trust_data"]) == 2
    assert client.report["decision"] == "accepted_for_offline_demo"
    assert client.report["deployment_allowed"] is False

    # 2. Setup ExperimentRunner
    optimizer = MVPOptimizer()
    adapter = SimulationAdapter()
    verifier = SimulationVerifier()
    runner = ExperimentRunner(strategy=optimizer, verifier=verifier, adapter=adapter)

    # 3. Run Paired Experiment
    comparison = runner.run_paired_experiment(
        scenario=scenario,
        renewable_demand_forecasts=[],
        context=ctx
    )

    # 4. Verify output Comparison
    assert comparison.scenario_id == "scen-e2e-test"
    assert comparison.experiment_seed == 99

    base_res = comparison.baseline_result
    trust_res = comparison.trust_aware_result

    assert base_res is not None
    assert trust_res is not None

    # A final MVP result must do more than execute: both plans must be feasible
    # and both simulated outcomes must pass verification.
    assert comparison.baseline_plan_status == OptimizationStatus.FEASIBLE
    assert comparison.trust_aware_plan_status == OptimizationStatus.FEASIBLE
    assert base_res.passed
    assert trust_res.passed

    # Trust-aware should generally have <= overcommitment than baseline in uncertain scenarios
    assert trust_res.overcommitment <= base_res.overcommitment
