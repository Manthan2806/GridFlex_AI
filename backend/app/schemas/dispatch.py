from pydantic import BaseModel
from typing import List, Union
from .core import TimeStep
from ..domain.enums import OptimizationStatus

class DispatchInstruction(BaseModel):
    """Represents x[i,t] from the optimizer"""
    resource_id: str
    time_step: TimeStep
    power_kw: float

class DispatchPlan(BaseModel):
    """Output from the Optimization subsystem"""
    dispatch_plan: List[DispatchInstruction]
    objective_value: float
    status: OptimizationStatus
    infeasibility_report: Union[str, None] = None