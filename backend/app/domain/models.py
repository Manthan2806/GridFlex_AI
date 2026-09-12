from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Any
from datetime import datetime
from .enums import ResourceType

class TrustState(BaseModel):
    """Time-dependent trust computed state per DOMAIN_MODEL.md"""
    potential_kw: float
    expected_kw: float
    trusted_kw: float
    confidence: float = Field(..., ge=0.0, le=1.0)

    @model_validator(mode='after')
    def check_trust_ordering(self) -> 'TrustState':
        """Invariant: trusted_kw <= expected_kw <= potential_kw"""
        if not (self.trusted_kw <= self.expected_kw <= self.potential_kw):
            raise ValueError("Trust ordering invariant violated: trusted_kw <= expected_kw <= potential_kw")
        return self

class FlexibilityResource(BaseModel):
    """
    Central domain entity representing a flexible load.
    Note: ID format (UUID/ULID) and Timezone handling are PENDING DECISIONS.
    """
    id: str
    type: ResourceType
    location_id: str
    rated_power_kw: float
    
    # Availability
    earliest_start: datetime
    latest_end: datetime
    
    # Energy
    required_kwh: float
    minimum_kwh: float
    maximum_kwh: float
    
    # Duration (minutes)
    minimum_duration: int
    maximum_duration: int
    
    # Constraints
    deadline: datetime
    min_power: float
    max_power: float
    
    # Behavior
    historical_response: List[Dict[str, Any]]
    override_rate: float = Field(..., ge=0.0, le=1.0)
    availability_rate: float = Field(..., ge=0.0, le=1.0)