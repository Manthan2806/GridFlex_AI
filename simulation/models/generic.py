from datetime import datetime
from typing import Dict, Any

from simulation.interfaces import ResourceBehaviorModel, ProvisionalDispatchInstruction, ProvisionalStepResult

class EnergyConstrainedResourceModel(ResourceBehaviorModel):
    """
    An idealized deterministic energy-constrained resource behavior model.
    Tracks remaining required energy and strictly obeys power bounds and availability windows.
    Does NOT model stochastic behavior, thermal dynamics, or specific industrial logic.
    """
    def __init__(
        self,
        resource_id: str,
        min_power: float,
        max_power: float,
        required_kwh: float,
        earliest_start: datetime,
        latest_end: datetime,
    ):
        self._resource_id = resource_id
        self.min_power = min_power
        self.max_power = max_power
        self.required_kwh = required_kwh
        self.remaining_kwh = required_kwh
        self.earliest_start = earliest_start
        self.latest_end = latest_end
        
        self.lifecycle_state = "available"

    @property
    def resource_id(self) -> str:
        return self._resource_id

    def step(self, current_time: datetime, instruction: ProvisionalDispatchInstruction, context: Dict[str, Any]) -> ProvisionalStepResult:
        """
        Executes a deterministic 15-minute timestep.
        """
        # If already completed, no more energy delivery
        if self.remaining_kwh <= 0.0:
            self.lifecycle_state = "completed"
            return ProvisionalStepResult(
                self.resource_id, 
                0.0, 
                {"lifecycle_state": self.lifecycle_state, "remaining_kwh": self.remaining_kwh}
            )

        # Availability window check
        if current_time < self.earliest_start or current_time >= self.latest_end:
            # Not in availability window. Deliver 0.
            # Provisional defensive choice: if outside window, we consider it unavailable.
            self.lifecycle_state = "unavailable"
            return ProvisionalStepResult(
                self.resource_id, 
                0.0, 
                {"lifecycle_state": self.lifecycle_state, "remaining_kwh": self.remaining_kwh}
            )

        # Default state if within window and not completed
        self.lifecycle_state = "available"
        requested_kw = instruction.power_kw
        delivered_kw = 0.0

        if requested_kw > 0.0:
            self.lifecycle_state = "dispatched"
            
            # Provisional defensive behavior: clip requested_kw to min/max power bounds.
            delivered_kw = max(self.min_power, min(self.max_power, requested_kw))
            
            # Energy calculation (15 min = 0.25h)
            delivered_kwh = delivered_kw * 0.25
            
            # Provisional defensive behavior: if delivered_kwh exceeds remaining_kwh, clip the delivery.
            if delivered_kwh > self.remaining_kwh:
                delivered_kwh = self.remaining_kwh
                delivered_kw = delivered_kwh / 0.25
                
            self.remaining_kwh -= delivered_kwh
            
            if self.remaining_kwh <= 0.0:
                self.remaining_kwh = 0.0
                self.lifecycle_state = "completed"

        return ProvisionalStepResult(
            self.resource_id, 
            delivered_kw, 
            {"lifecycle_state": self.lifecycle_state, "remaining_kwh": self.remaining_kwh}
        )
