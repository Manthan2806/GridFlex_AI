from pydantic import BaseModel
from typing import List, Dict, Any
from .core import TimeStep
from .scenarios import Scenario
from .dispatch import DispatchPlan
from ..domain.enums import ResourceState

class SimulationInput(BaseModel):
    """
    CONTRACT: Backend -> Simulation (CONTRACTS.md 8.4)
    Team 4: Use this schema as the exact input to your Simulation Engine.
    """
    scenario: Scenario
    initial_resource_states: Dict[str, ResourceState]
    # Forecasts only! Simulation must NOT receive actual future outcomes.
    renewable_demand_forecasts: List[Dict[str, Any]]
    dispatch_plan: DispatchPlan
    system_constraints: Dict[str, Any]

class ActualResponse(BaseModel):
    resource_id: str
    time_step: TimeStep
    delivered_kw: float

class ResourceStateEvolution(BaseModel):
    resource_id: str
    time_step: TimeStep
    state: ResourceState

class SimulationOutput(BaseModel):
    """
    CONTRACT: Simulation -> Backend (CONTRACTS.md 8.4)
    Team 4: Your Simulation Engine must return data matching this schema.
    """
    actual_response: List[ActualResponse]
    resource_state_evolution: List[ResourceStateEvolution]
    renewable_outcomes: List[Dict[str, Any]]
    system_outcomes: List[Dict[str, Any]]
    event_records: Dict[str, List[Any]]