from enum import Enum

class ResourceType(str, Enum):
    """Canonical resource types per DOMAIN_MODEL.md"""
    EV = "ev"
    WATER_HEATER = "water_heater"
    INDUSTRIAL_BATCH = "industrial_batch"

class ResourceState(str, Enum):
    """Canonical resource states per DOMAIN_MODEL.md"""
    AVAILABLE = "available"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    UNAVAILABLE = "unavailable"

class OptimizationStatus(str, Enum):
    """Canonical optimization statuses per CONTRACTS.md"""
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    TIMEOUT = "TIMEOUT"