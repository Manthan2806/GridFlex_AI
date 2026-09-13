from pydantic import BaseModel
from typing import List

class DispatchResponseScenario(BaseModel):
    id: str

class DispatchFlexibilityState(BaseModel):
    potentialKw: float
    expectedKw: float
    trustedKw: float
    confidence: float

class DispatchResource(BaseModel):
    id: str
    name: str
    type: str
    dispatchedKw: float
    state: str

class RecommendedDispatch(BaseModel):
    id: str
    timeWindow: str
    resources: List[DispatchResource]
    totalDispatchedKw: float
    rationale: str
    status: str

class ConstraintCheckResult(BaseModel):
    constraints: List[str]
    violations: List[str]
    deadlineViolations: List[str]
    passed: bool

class DispatchResponse(BaseModel):
    scenario: DispatchResponseScenario
    flexibility: DispatchFlexibilityState
    recommendedDispatch: RecommendedDispatch
    constraintCheck: ConstraintCheckResult
