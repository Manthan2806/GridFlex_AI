import sys
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path so we can run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.domain.enums import ResourceType
from backend.app.domain.models import FlexibilityResource
from backend.app.schemas.scenarios import Scenario
from backend.app.integrations.ai_ml_client import OfflineDemoEVModelClientV2
from backend.app.services.trust_hydration import build_optimizer_context
from backend.app.services.dispatch_service import MVPOptimizer
from experiments.disruption_adapter import SeededEVDisruptionAdapter
from simulation.adapter import SimulationAdapter
from backend.app.services.verification_service import SimulationVerifier
from experiments.runner import ExperimentRunner

def _make_resource(
    res_id: str,
    max_power: float = 7.2,
    required_kwh: float = 4.0,
    connection_hours: float = 8.0,
    availability_rate: float = 0.9,
    override_rate: float = 0.05,
) -> FlexibilityResource:
    start = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
    return FlexibilityResource(
        id=res_id,
        type=ResourceType.EV,
        location_id="test-loc",
        rated_power_kw=max_power,
        earliest_start=start,
        latest_end=start + timedelta(hours=connection_hours),
        required_kwh=required_kwh,
        minimum_kwh=0.0,
        maximum_kwh=20.0,
        minimum_duration=15,
        maximum_duration=int(connection_hours * 60),
        deadline=start + timedelta(hours=connection_hours),
        min_power=0.0,
        max_power=max_power,
        historical_response=[],
        override_rate=override_rate,
        availability_rate=availability_rate,
    )

def main():
    print("==================================================")
    print("FINAL MVP END-TO-END EXPERIMENT")
    print("==================================================\n")

    # 1. Setup deterministic scenario
    master_seed = 42
    resources = [
        _make_resource("ev-001", max_power=7.2, required_kwh=4.0, availability_rate=0.92, override_rate=0.04),
        _make_resource("ev-002", max_power=7.2, required_kwh=6.0, availability_rate=0.82, override_rate=0.12),
        _make_resource("ev-003", max_power=11.0, required_kwh=8.0, availability_rate=0.75, override_rate=0.18),
        _make_resource("ev-004", max_power=3.6, required_kwh=2.0, availability_rate=0.96, override_rate=0.02),
        _make_resource("ev-005", max_power=22.0, required_kwh=10.0, availability_rate=0.78, override_rate=0.16),
    ]
    scenario = Scenario(
        scenario_id="mvp-demo-scen-001",
        resources=resources,
        disruption_specs={},
        seeds={"master": master_seed}
    )
    event_time = resources[0].earliest_start

    # 2. Run AI/ML Inference
    print("Initializing offline-only EV Model Client...")
    try:
        client = OfflineDemoEVModelClientV2(demo_mode=True)
        ctx = build_optimizer_context(client, resources, event_time)
        print("✅ AI/ML inference executed successfully.")
        print(f"✅ Generated TrustState for {len(ctx['trust_data'])} resources.")
    except Exception as e:
        print(f"❌ ERROR: AI/ML runtime failed: {e}")
        raise SystemExit(1) from e

    # 3. Setup Experiment Components
    optimizer = MVPOptimizer()
    adapter = SimulationAdapter()
    verifier = SimulationVerifier()
    runner = ExperimentRunner(strategy=optimizer, verifier=verifier, adapter=adapter)

    # 4. Run Paired Experiment
    print("\nRunning Baseline (potential_kw) and Trust-Aware (trusted_kw) Pipelines...")
    # Empty renewable series for this MVP demo (we focus on flexibility error/overcommitment)
    renewable_forecasts = []

    comparison = runner.run_paired_experiment(
        scenario=scenario,
        renewable_demand_forecasts=renewable_forecasts,
        context=ctx
    )

    disruption_runner = ExperimentRunner(
        strategy=optimizer,
        verifier=verifier,
        adapter=SeededEVDisruptionAdapter(seed=master_seed),
    )
    disruption_comparison = disruption_runner.run_paired_experiment(
        scenario=scenario,
        renewable_demand_forecasts=renewable_forecasts,
        context=ctx,
    )

    base_res = comparison.baseline_result
    trust_res = comparison.trust_aware_result

    # 5. Output Human-Readable Report
    print("\n==================================================")
    print("EXPERIMENT REPORT")
    print("==================================================")

    print("\n--- 1. SCENARIO SUMMARY ---")
    print(f"Scenario ID: {scenario.scenario_id}")
    print(f"Seed (Provenance): master={master_seed}")
    print(f"Total Resources: {len(resources)}")
    print(f"Total Required Energy: {sum(r.required_kwh for r in resources):.1f} kWh")
    print("Connection Window: 8 hours (workplace charging scenario)")

    trust_states = list(ctx["trust_data"].values())
    total_potential_kw = sum(state.potential_kw for state in trust_states)
    total_expected_kw = sum(state.expected_kw for state in trust_states)
    total_trusted_kw = sum(state.trusted_kw for state in trust_states)
    trusted_retention_percent = (
        100.0 * total_trusted_kw / total_expected_kw if total_expected_kw else 0.0
    )
    print(f"Total Potential Power: {total_potential_kw:.2f} kW")
    print(f"Total Expected Power: {total_expected_kw:.2f} kW")
    print(f"Total Trusted Power: {total_trusted_kw:.2f} kW")
    print(f"Trusted/Expected Retention: {trusted_retention_percent:.2f}%")

    print("\n--- 2. BASELINE DISPATCH SUMMARY ---")
    print(f"Strategy Basis: potential_kw")
    print(f"Optimizer Status: {comparison.baseline_plan_status.name if comparison.baseline_plan_status else 'UNKNOWN'}")
    print(f"Passed Verification: {base_res.passed}")
    print(f"Violations: {len(base_res.violations)}")

    print("\n--- 3. TRUST-AWARE DISPATCH SUMMARY ---")
    print(f"Strategy Basis: trusted_kw")
    print(f"Optimizer Status: {comparison.trust_aware_plan_status.name if comparison.trust_aware_plan_status else 'UNKNOWN'}")
    print(f"Passed Verification: {trust_res.passed}")
    print(f"Violations: {len(trust_res.violations)}")

    print("\n--- 4. METRICS COMPARISON ---")
    print(f"{'Metric':<30} | {'Baseline':<15} | {'Trust-Aware':<15}")
    print("-" * 65)
    print(f"{'Delivered Flex Error (kW)':<30} | {base_res.delivered_flexibility_error:<15.2f} | {trust_res.delivered_flexibility_error:<15.2f}")
    print(f"{'Overcommitment (kW)':<30} | {base_res.overcommitment:<15.2f} | {trust_res.overcommitment:<15.2f}")
    print(f"{'Reliability (Actual/Commit)':<30} | {base_res.reliability:<15.2f} | {trust_res.reliability:<15.2f}")
    print(f"{'Constraint Violations':<30} | {base_res.constraint_violation_count:<15} | {trust_res.constraint_violation_count:<15}")
    print(f"{'Deadline Violations':<30} | {base_res.deadline_violation_count:<15} | {trust_res.deadline_violation_count:<15}")

    disruption_base = disruption_comparison.baseline_result
    disruption_trust = disruption_comparison.trust_aware_result
    disruption_reduction = (
        disruption_base.overcommitment - disruption_trust.overcommitment
    )
    baseline_overcommitment_kwh = disruption_base.overcommitment * 0.25
    trust_overcommitment_kwh = disruption_trust.overcommitment * 0.25
    disruption_reduction_kwh = disruption_reduction * 0.25
    disruption_reduction_percent = (
        100.0 * disruption_reduction / disruption_base.overcommitment
        if disruption_base.overcommitment
        else 0.0
    )
    reliability_improvement_points = 100.0 * (
        disruption_trust.reliability - disruption_base.reliability
    )
    print("\n--- 5. SEEDED EV DISRUPTION COMPARISON ---")
    print(f"Shared disruption seed: {master_seed}")
    print(f"Baseline overcommitment energy: {baseline_overcommitment_kwh:.2f} kWh")
    print(f"Trust-aware overcommitment energy: {trust_overcommitment_kwh:.2f} kWh")
    print(
        f"Overcommitment reduction: {disruption_reduction_kwh:.2f} kWh "
        f"({disruption_reduction_percent:.2f}%)"
    )
    print(f"Baseline reliability: {disruption_base.reliability:.3f}")
    print(f"Trust-aware reliability: {disruption_trust.reliability:.3f}")
    print(f"Reliability improvement: {reliability_improvement_points:.2f} percentage points")
    print(f"Baseline deadline violations: {disruption_base.deadline_violation_count}")
    print(f"Trust-aware deadline violations: {disruption_trust.deadline_violation_count}")

    print("\n==================================================")
    print("RESULT INTERPRETATION")
    print("Trust-aware dispatch uses more conservative trusted flexibility estimates.")
    print("In the deterministic control run, both strategies satisfy every deadline.")
    print("This script compares response reliability, not feeder-level safety.")
    print("\nThe primary pipeline remains deterministic and checks integration correctness.")
    print("The separate seeded comparison applies synthetic availability and user-override")
    print("events. Both strategies receive the same resource/timestamp outcomes.")
    print("This illustrates behavior under controlled disruptions; it is not field evidence.")
    all_strategies_passed = bool(base_res.passed and trust_res.passed)
    if all_strategies_passed:
        print("\nBoth strategies satisfy the resource constraints in the deterministic control.")
    else:
        print("\nThis run is not a successful end-to-end result because at least one")
        print("strategy failed verification. Review the reported violations before")
        print("using the generated JSON as demo evidence.")
    if disruption_base.passed and disruption_trust.passed:
        print("Both strategies also pass the seeded disruption stress test.")
    else:
        print(
            "In the seeded stress test, neither strategy satisfies every deadline; "
            "dynamic replanning is not implemented."
        )
        print(
            f"Trust-aware dispatch reduces overcommitment energy by "
            f"{disruption_reduction_percent:.2f}% and improves reliability by "
            f"{reliability_improvement_points:.2f} percentage points in this seed."
        )
    print("==================================================")

    # Write JSON output
    out_dir = Path("experiments/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "mvp_experiment.json"

    out_data = {
        "scenario_id": comparison.scenario_id,
        "seed": comparison.experiment_seed,
        "baseline_plan_status": comparison.baseline_plan_status.value,
        "trust_aware_plan_status": comparison.trust_aware_plan_status.value,
        "all_strategies_passed": all_strategies_passed,
        "trust_state_summary": {
            "total_potential_kw": total_potential_kw,
            "total_expected_kw": total_expected_kw,
            "total_trusted_kw": total_trusted_kw,
            "trusted_expected_retention_percent": trusted_retention_percent,
        },
        "baseline_metrics": base_res.model_dump(),
        "trust_aware_metrics": trust_res.model_dump(),
        "seeded_disruption_experiment": {
            "evidence_type": "synthetic seeded experiment; not real-world validation",
            "shared_seed": master_seed,
            "same_outcome_rule_for_both_strategies": True,
            "baseline_metrics": disruption_base.model_dump(),
            "trust_aware_metrics": disruption_trust.model_dump(),
            "baseline_overcommitment_kwh": baseline_overcommitment_kwh,
            "trust_aware_overcommitment_kwh": trust_overcommitment_kwh,
            "overcommitment_reduction_kwh": disruption_reduction_kwh,
            "overcommitment_reduction_percent": disruption_reduction_percent,
            "reliability_improvement_percentage_points": reliability_improvement_points,
        },
    }
    with out_file.open("w") as f:
        json.dump(out_data, f, indent=2)
        f.write("\n")
    print(f"\nSaved structured results to: {out_file}")

    if not all_strategies_passed:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
