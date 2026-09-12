from typing import Dict, List, Any
from datetime import datetime
from simulation.clock import SimulationClock
from simulation.interfaces import ResourceBehaviorModel, ProvisionalDispatchInstruction, ProvisionalStepResult

class SimulationEngine:
    """
    Minimal deterministic simulation engine for executing a 15-minute timestep loop.
    """
    
    def __init__(self, start_time: datetime, horizon_steps: int):
        self.clock = SimulationClock(start_time, horizon_steps)
        self.resources: Dict[str, ResourceBehaviorModel] = {}
        # Simple storage for results: list of dicts mapped by time step index
        self.results: List[Dict[str, Any]] = []
        
    def register_resource(self, resource: ResourceBehaviorModel) -> None:
        """Registers a resource model with the simulation engine."""
        self.resources[resource.resource_id] = resource
        
    def run(self, dispatch_plans: List[List[ProvisionalDispatchInstruction]], scenario_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Executes the simulation loop over the entire horizon.
        
        Args:
            dispatch_plans: A list (length == horizon_steps) of lists containing 
                            ProvisionalDispatchInstructions for each resource at that step.
            scenario_context: Static or dynamic scenario context (e.g. weather) - simplified for Phase 1.
            
        Returns:
            A list of step results, one dictionary per step index.
        """
        if len(dispatch_plans) != self.clock.horizon_steps:
            raise ValueError(f"Expected {self.clock.horizon_steps} dispatch plans, got {len(dispatch_plans)}")

        self.results = []
        
        while not self.clock.is_complete():
            current_time = self.clock.current_time
            step_idx = self.clock.current_step_index
            
            # 1. Get the dispatch instructions for the current timestep
            current_instructions = dispatch_plans[step_idx]
            instruction_map = {inst.resource_id: inst for inst in current_instructions}
            
            # 2. Invoke registered resources
            step_results = []
            for resource_id, resource in self.resources.items():
                # Default instruction is 0 kW if none provided
                instruction = instruction_map.get(
                    resource_id, 
                    ProvisionalDispatchInstruction(resource_id=resource_id, power_kw=0.0)
                )
                result = resource.step(current_time, instruction, scenario_context)
                step_results.append(result)
            
            # 3. Collect minimal per-step simulation state/results
            self.results.append({
                "step_index": step_idx,
                "time": current_time,
                "resource_results": step_results
            })
            
            # 4. Advance clock
            self.clock.tick()
            
        return self.results
