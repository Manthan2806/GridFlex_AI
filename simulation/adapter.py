from typing import List, Dict, Any
from datetime import datetime

from backend.app.integrations.simulation_client import SimulationClientBoundary
from backend.app.schemas.runs import SimulationInput, SimulationOutput, ActualResponse, ResourceStateEvolution
from backend.app.schemas.dispatch import DispatchInstruction, DispatchPlan
from backend.app.schemas.scenarios import Scenario
from backend.app.domain.enums import ResourceState

from simulation.engine import SimulationEngine
from simulation.interfaces import ProvisionalDispatchInstruction
from simulation.models.generic import EnergyConstrainedResourceModel

class SimulationAdapter(SimulationClientBoundary):
    """
    Translates the canonical Backend SimulationInput schemas into the format
    expected by the internal Phase 1 SimulationEngine, executes the simulation,
    and maps the results back to canonical SimulationOutput schemas.
    """
    
    def run_simulation(self, sim_input: SimulationInput) -> SimulationOutput:
        scenario = sim_input.scenario
        dispatch = sim_input.dispatch_plan
        
        # 1. Derive Horizon and Start Time from the Scenario Configuration
        if not scenario.resources:
            raise ValueError("Scenario must contain at least one resource to derive simulation horizon.")
            
        # The safest temporal bound is defined by the resource availability envelopes
        start_time = min(r.earliest_start for r in scenario.resources)
        latest_end = max(r.latest_end for r in scenario.resources)
        
        total_seconds = (latest_end - start_time).total_seconds()
        horizon_steps = int(total_seconds // 900)
        
        if horizon_steps <= 0:
            raise ValueError("Derived horizon must be at least 1 step based on resource availability windows.")

        # 2. Instantiate Phase 1 SimulationEngine
        engine = SimulationEngine(start_time, horizon_steps)
        
        # 3. Translate Resources (Canonical -> Phase 2A Generic)
        for r in scenario.resources:
            model = EnergyConstrainedResourceModel(
                resource_id=r.id,
                min_power=r.min_power,
                max_power=r.max_power,
                required_kwh=r.required_kwh,
                earliest_start=r.earliest_start,
                latest_end=r.latest_end
            )
            engine.register_resource(model)
            
        # 4. Bucket Dispatch Instructions (Flat -> Timestep Indexed)
        dispatch_buckets: List[List[ProvisionalDispatchInstruction]] = [[] for _ in range(horizon_steps)]
        
        for inst in dispatch.dispatch_plan:
            if isinstance(inst.time_step, datetime):
                delta = inst.time_step - start_time
                idx = int(delta.total_seconds() // 900)
            elif isinstance(inst.time_step, int):
                # PROVISIONAL ADAPTER-LOCAL BEHAVIOR:
                # If the optimizer passes integer timesteps, we assume 0 precisely aligns 
                # with the derived scenario start_time (global earliest resource start).
                idx = inst.time_step
            else:
                raise ValueError("Unsupported TimeStep format in dispatch instruction.")
                
            if 0 <= idx < horizon_steps:
                dispatch_buckets[idx].append(ProvisionalDispatchInstruction(inst.resource_id, inst.power_kw))
                
        # 5. Construct Context - Information Boundary Protection
        # Passes ONLY configuration and forecasts. Actual realizations are NEVER passed in.
        # Seeds are plumbed through for future deterministic consumption.
        # initial_resource_states are preserved in context, though the Phase 2A model currently ignores them.
        context = {
            "renewable_demand_forecasts": sim_input.renewable_demand_forecasts,
            "disruption_specs": scenario.disruption_specs,
            "seeds": scenario.seeds,
            "initial_resource_states": sim_input.initial_resource_states
        }
        
        # 6. Run Engine
        raw_results = engine.run(dispatch_buckets, context)
        
        # 7. Translate Output (Provisional Results -> Canonical SimulationOutput)
        actual_responses = []
        state_evolutions = []
        
        for step_data in raw_results:
            step_time = step_data["time"]
            
            for res_result in step_data["resource_results"]:
                # Preserve actual responses for later verification metrics
                actual_responses.append(ActualResponse(
                    resource_id=res_result.resource_id,
                    time_step=step_time,
                    delivered_kw=res_result.delivered_kw
                ))
                
                # Map provisional string state to domain ResourceState enum
                raw_state = res_result.state_updates.get("lifecycle_state", "available")
                try:
                    enum_state = ResourceState(raw_state)
                except ValueError:
                    # PROVISIONAL DEFENSIVE BEHAVIOR: Default to AVAILABLE if unknown state
                    enum_state = ResourceState.AVAILABLE

                    
                state_evolutions.append(ResourceStateEvolution(
                    resource_id=res_result.resource_id,
                    time_step=step_time,
                    state=enum_state
                ))
                
        return SimulationOutput(
            actual_response=actual_responses,
            resource_state_evolution=state_evolutions,
            renewable_outcomes=[], # To be populated by disruption logic later
            system_outcomes=[],
            event_records={}
        )
