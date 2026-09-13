from typing import List, Dict, Any, Optional, Protocol
from pydantic import BaseModel
from datetime import datetime, timedelta

from backend.app.schemas.runs import SimulationInput
from backend.app.schemas.scenarios import Scenario
from backend.app.schemas.dispatch import DispatchPlan
from backend.app.schemas.core import TimeStep

from backend.app.services.verification_service import SimulationVerifier, VerificationResult
from simulation.adapter import SimulationAdapter

class StrategyBoundary(Protocol):
    """
    Injectable boundary representing the Optimizer / Dispatch generator.
    Must generate a DispatchPlan from a Scenario and a specified strategy_basis.
    """
    def generate_dispatch_plan(self, scenario: Scenario, strategy_basis: str, context: Dict[str, Any]) -> DispatchPlan:
        ...

from backend.app.domain.enums import OptimizationStatus

class ExperimentComparison(BaseModel):
    """
    Result of a paired Baseline vs Trust-Aware experiment execution.
    Raw results are exposed directly for comparison.
    """
    baseline_result: Optional[VerificationResult] = None
    baseline_plan_status: Optional[OptimizationStatus] = None
    trust_aware_result: Optional[VerificationResult] = None
    trust_aware_plan_status: Optional[OptimizationStatus] = None
    horizon_validated: bool
    experiment_seed: int
    scenario_id: str

class ExperimentRunner:
    """
    Orchestration layer coordinating Scenario -> Strategy -> Simulation -> Verification -> Comparison.
    """
    def __init__(self, strategy: StrategyBoundary, verifier: SimulationVerifier, adapter: SimulationAdapter):
        self.strategy = strategy
        self.verifier = verifier
        self.adapter = adapter
        
    def _validate_horizon(self, scenario: Scenario) -> bool:
        """
        Validates that the scenario's temporal bounds are well-formed so the SimulationAdapter
        and Verifier will fully encompass all resource deadlines.
        """
        if not scenario.resources:
            return False
            
        try:
            start_time = min(r.earliest_start for r in scenario.resources)
            latest_end = max(r.latest_end for r in scenario.resources)
            total_seconds = (latest_end - start_time).total_seconds()
            return total_seconds >= 900 # At least one 15-minute step
        except Exception:
            return False

    def run_paired_experiment(
        self, 
        scenario: Scenario, 
        renewable_demand_forecasts: List[Dict[str, Any]], 
        renewable_excess_series: Optional[Dict[TimeStep, float]] = None,
        tolerance_kw: float = 0.0,
        context: Optional[Dict[str, Any]] = None
    ) -> ExperimentComparison:
        """
        Executes a paired baseline vs trust-aware experiment on an identical scenario.
        """
        ctx = context or {}
        master_seed = scenario.seeds.get("master", 0)
        
        horizon_valid = self._validate_horizon(scenario)
        if not horizon_valid:
            raise ValueError("Scenario temporal bounds are invalid or insufficient to cover resource deadlines.")
            
        # --- 1. Baseline Run (potential_kw) ---
        baseline_plan = self.strategy.generate_dispatch_plan(scenario, "potential_kw", ctx)
        baseline_sim_input = SimulationInput(
            scenario=scenario, # Strict identical scenario preservation
            initial_resource_states={},
            renewable_demand_forecasts=renewable_demand_forecasts,
            dispatch_plan=baseline_plan,
            system_constraints={}
        )
        baseline_sim_output = self.adapter.run_simulation(baseline_sim_input)
        baseline_verification = self.verifier.verify(
            sim_input=baseline_sim_input,
            sim_output=baseline_sim_output,
            tolerance_kw=tolerance_kw,
            renewable_excess_series=renewable_excess_series
        )
        
        # --- 2. Trust-Aware Run (trusted_kw) ---
        try:
            trust_plan = self.strategy.generate_dispatch_plan(scenario, "trusted_kw", ctx)
            trust_sim_input = SimulationInput(
                scenario=scenario, # Strict identical scenario preservation
                initial_resource_states={},
                renewable_demand_forecasts=renewable_demand_forecasts,
                dispatch_plan=trust_plan,
                system_constraints={}
            )
            trust_sim_output = self.adapter.run_simulation(trust_sim_input)
            trust_verification = self.verifier.verify(
                sim_input=trust_sim_input,
                sim_output=trust_sim_output,
                tolerance_kw=tolerance_kw,
                renewable_excess_series=renewable_excess_series
            )
        except Exception as e:
            raise RuntimeError(f"Trust-aware experiment failed: {e}") from e

        return ExperimentComparison(
            baseline_result=baseline_verification,
            baseline_plan_status=baseline_plan.status,
            trust_aware_result=trust_verification,
            trust_aware_plan_status=trust_plan.status,
            horizon_validated=True,
            experiment_seed=master_seed,
            scenario_id=scenario.scenario_id
        )
