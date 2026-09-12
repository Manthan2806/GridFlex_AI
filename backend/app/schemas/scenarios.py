from pydantic import BaseModel
from typing import List, Dict, Any
from ..domain.models import FlexibilityResource

class Scenario(BaseModel):
    """Defines simulation conditions"""
    scenario_id: str
    resources: List[FlexibilityResource]
    disruption_specs: Dict[str, Any]
    seeds: Dict[str, int]