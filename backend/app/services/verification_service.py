from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel

from backend.app.schemas.runs import SimulationInput, SimulationOutput
from backend.app.schemas.core import TimeStep
from experiments.metrics import (
    calculate_renewable_absorption,
    calculate_delivered_flexibility_error,
    calculate_overcommitment,
    calculate_reliability,
    calculate_rebound
)

class VerificationResult(BaseModel):
    passed: bool
    delivered_flexibility_error: float
    overcommitment: float
    constraint_violation_count: int
    deadline_violation_count: int
    reliability: float
    renewable_absorption: Optional[float]
    rebound: Optional[float]
    violations: List[str]

class SimulationVerifier:
    """
    Pure analysis verification component. Validates planned dispatch against 
    actual simulated outcomes and domain constraints.
    """
    def verify(
        self, 
        sim_input: SimulationInput, 
        sim_output: SimulationOutput, 
        tolerance_kw: float, 
        renewable_excess_series: Optional[Dict[TimeStep, float]] = None
    ) -> VerificationResult:
        
        # 1. Pre-process disjoint datasets for O(1) alignment
        dispatched: Dict[str, Dict[TimeStep, float]] = {}
        
        violations = []
        constraint_violations = 0
        deadline_violations = 0
        
        # Build resource map for quick lookup
        resource_map = {r.id: r for r in sim_input.scenario.resources}
        
        for inst in sim_input.dispatch_plan.dispatch_plan:
            res = resource_map.get(inst.resource_id)
            if not res:
                constraint_violations += 1
                violations.append(f"Unknown resource {inst.resource_id} in dispatch plan")
                continue
                
            if inst.power_kw < 0:
                constraint_violations += 1
                violations.append(f"Negative power {inst.power_kw} for {inst.resource_id}")
                
            if isinstance(inst.time_step, datetime):
                if inst.time_step.minute % 15 != 0 or inst.time_step.second != 0 or inst.time_step.microsecond != 0:
                    constraint_violations += 1
                    violations.append(f"Non-15-minute timestamp {inst.time_step} for {inst.resource_id}")
                
                if isinstance(res.earliest_start, datetime) and isinstance(res.latest_end, datetime):
                    if inst.time_step < res.earliest_start or inst.time_step >= res.latest_end:
                        constraint_violations += 1
                        violations.append(f"Instruction for {inst.resource_id} outside time window: {inst.time_step}")
                
            if inst.resource_id not in dispatched:
                dispatched[inst.resource_id] = {}
                
            if inst.time_step in dispatched[inst.resource_id]:
                constraint_violations += 1
                violations.append(f"Duplicate instruction for {inst.resource_id} at {inst.time_step}")
                
            dispatched[inst.resource_id][inst.time_step] = inst.power_kw
            
        actuals: Dict[str, Dict[TimeStep, float]] = {}
        for resp in sim_output.actual_response:
            if resp.resource_id not in actuals:
                actuals[resp.resource_id] = {}
            actuals[resp.resource_id][resp.time_step] = resp.delivered_kw
            
        # 2. Compute explicit formulas
        error = calculate_delivered_flexibility_error(dispatched, actuals)
        overcommit = calculate_overcommitment(dispatched, actuals, tolerance_kw)
        reliability = calculate_reliability(dispatched, actuals)
        rebound = calculate_rebound()
        
        absorption = None
        if renewable_excess_series is not None:
            absorption = calculate_renewable_absorption(sim_output.actual_response, renewable_excess_series)
            
        # 3. Analyze constraints and deadlines per resource
        
        for res in sim_input.scenario.resources:
            res_actuals = actuals.get(res.id, {})
            total_kwh = 0.0
            
            for t, a_kw in res_actuals.items():
                if a_kw > res.max_power:
                    constraint_violations += 1
                    violations.append(f"Resource {res.id} exceeded max power {res.max_power} at {t} with {a_kw}kW")
                
                if 0 < a_kw < res.min_power:
                    constraint_violations += 1
                    violations.append(f"Resource {res.id} below min power {res.min_power} at {t} with {a_kw}kW")
                
                total_kwh += a_kw * 0.25
                
            if total_kwh < res.required_kwh - 0.0001:
                deadline_violations += 1
                violations.append(f"Resource {res.id} missed required {res.required_kwh} kWh (delivered {total_kwh} kWh)")
                
        passed = (constraint_violations == 0 and deadline_violations == 0 and overcommit == 0)
        
        return VerificationResult(
            passed=passed,
            delivered_flexibility_error=error,
            overcommitment=overcommit,
            constraint_violation_count=constraint_violations,
            deadline_violation_count=deadline_violations,
            reliability=reliability,
            renewable_absorption=absorption,
            rebound=rebound,
            violations=violations
        )
