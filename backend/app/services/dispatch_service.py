from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from backend.app.schemas.scenarios import Scenario
from backend.app.schemas.dispatch import DispatchPlan, DispatchInstruction
from backend.app.domain.enums import OptimizationStatus

logger = logging.getLogger(__name__)

class MVPOptimizer:
    """
    MVP deterministic matching/dispatch strategy.
    Implements a greedy planner respecting canonical resource limits and time windows.
    Compliant with the StrategyBoundary expected by Team 4's ExperimentRunner.
    """
    
    def generate_dispatch_plan(self, scenario: Scenario, strategy_basis: str, context: Dict[str, Any]) -> DispatchPlan:
        instructions: List[DispatchInstruction] = []
        
        # Sort resources deterministically by ID to ensure reproducible ordering
        sorted_resources = sorted(scenario.resources, key=lambda r: r.id)
        
        for res in sorted_resources:
            # 1. Determine usable planning power based on strategy_basis
            if strategy_basis == "trusted_kw":
                trust_data = context.get("trust_data", {})
                res_trust = trust_data.get(res.id)
                if not res_trust:
                    raise ValueError(f"Trusted data unavailable for resource {res.id}")
                planning_power_kw = res_trust.trusted_kw
            elif strategy_basis == "potential_kw":
                trust_data = context.get("trust_data", {})
                res_trust = trust_data.get(res.id)
                if res_trust:
                    planning_power_kw = res_trust.potential_kw
                else:
                    # Fallback to hardware maximum if no ML mapping provided for baseline
                    planning_power_kw = res.max_power 
            else:
                raise ValueError(f"Unknown strategy basis: {strategy_basis}")
                
            # 2. Clamp to existing physical bounds (hardware constraint)
            usable_kw = max(res.min_power, min(res.max_power, planning_power_kw))
            
            # 3. Simple Greedy Allocation
            # We fulfill the required_kwh sequentially from earliest_start to latest_end.
            remaining_kwh = res.required_kwh
            current_time = res.earliest_start
            
            while remaining_kwh > 0.0001 and current_time < res.latest_end:
                # 15-minute timestep resolution (0.25 hours)
                step_kwh = usable_kw * 0.25
                dispatch_kw = usable_kw
                
                # If we only need a fraction of the block to finish the requirement
                if step_kwh > remaining_kwh:
                    dispatch_kw = remaining_kwh / 0.25
                    step_kwh = remaining_kwh
                    
                instructions.append(DispatchInstruction(
                    resource_id=res.id,
                    time_step=current_time,
                    power_kw=dispatch_kw
                ))
                
                remaining_kwh -= step_kwh
                current_time += timedelta(minutes=15)
                
        return DispatchPlan(
            dispatch_plan=instructions,
            objective_value=0.0, # Placeholder for MVP
            status=OptimizationStatus.OPTIMAL
        )
