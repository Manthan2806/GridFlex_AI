from pydantic import BaseModel
from typing import List, Dict, Any
from .core import TimeStep

class VerificationMetric(BaseModel):
    resource_id: str
    time_step: TimeStep
    delivered_kw: float
    dispatched_kw: float
    error_kw: float

class VerificationResult(BaseModel):
    """CONTRACT: Simulation/Backend -> Verification -> Learning"""
    metrics: List[VerificationMetric]
    overcommitment_kw: float
    constraint_adherence: List[Dict[str, Any]]
    deadline_violations: List[str] 
    rebound_events: List[Dict[str, Any]]
    actual_committed_reliability: float
    override_events: List[Dict[str, Any]]
    failure_events: List[Dict[str, Any]]