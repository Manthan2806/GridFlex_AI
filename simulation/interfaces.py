from abc import ABC, abstractmethod
from typing import Any, Dict
from datetime import datetime

class ProvisionalDispatchInstruction:
    """
    Provisional internal structure representing a dispatch instruction for Phase 1.
    This is NOT the final Backend/Optimization cross-team JSON contract.
    """
    def __init__(self, resource_id: str, power_kw: float):
        self.resource_id = resource_id
        self.power_kw = power_kw

class ProvisionalStepResult:
    """
    Provisional internal structure representing a resource's response to a dispatch.
    """
    def __init__(self, resource_id: str, delivered_kw: float, state_updates: Dict[str, Any] = None):
        self.resource_id = resource_id
        self.delivered_kw = delivered_kw
        self.state_updates = state_updates or {}

class ResourceBehaviorModel(ABC):
    """
    Minimal abstract interface for a resource behavior model.
    Future resource models (EV, Water Heater, Industrial) will implement this.
    """
    
    @property
    @abstractmethod
    def resource_id(self) -> str:
        """Returns the unique identifier of this resource."""
        pass

    @abstractmethod
    def step(self, current_time: datetime, instruction: ProvisionalDispatchInstruction, context: Dict[str, Any]) -> ProvisionalStepResult:
        """
        Executes a single 15-minute timestep for the resource.
        
        Args:
            current_time: The current simulation time.
            instruction: The dispatch instruction for this timestep.
            context: Additional simulation context (e.g., weather, system conditions).
            
        Returns:
            ProvisionalStepResult containing the actual response and any state changes.
        """
        pass
