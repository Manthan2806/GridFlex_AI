from typing import List, Dict, Any, Optional
from backend.app.schemas.core import TimeStep

def calculate_renewable_absorption(actual_responses: List[Any], renewable_excess_series: Dict[TimeStep, float]) -> float:
    """
    Measures the integral of actual response concurrent with renewable excess.
    sum(actual_response_kw * 0.25) over timesteps where renewable excess > 0.
    """
    total_absorption_kwh = 0.0
    for resp in actual_responses:
        excess = renewable_excess_series.get(resp.time_step, 0.0)
        if excess > 0:
            total_absorption_kwh += resp.delivered_kw * 0.25
    return total_absorption_kwh

def calculate_delivered_flexibility_error(dispatched: Dict[str, Dict[TimeStep, float]], actuals: Dict[str, Dict[TimeStep, float]]) -> float:
    """
    sum(abs(dispatched_kw - actual_response_kw))
    """
    error = 0.0
    all_resources = set(dispatched.keys()).union(set(actuals.keys()))
    for res_id in all_resources:
        d_times = dispatched.get(res_id, {})
        a_times = actuals.get(res_id, {})
        all_times = set(d_times.keys()).union(set(a_times.keys()))
        for t in all_times:
            d_kw = d_times.get(t, 0.0)
            a_kw = a_times.get(t, 0.0)
            error += abs(d_kw - a_kw)
    return error

def calculate_overcommitment(dispatched: Dict[str, Dict[TimeStep, float]], actuals: Dict[str, Dict[TimeStep, float]], tolerance_kw: float) -> float:
    """
    sum(max(0, dispatched_kw - (actual_response_kw + tolerance)))
    """
    overcommitment = 0.0
    for res_id, d_times in dispatched.items():
        for t, d_kw in d_times.items():
            a_kw = actuals.get(res_id, {}).get(t, 0.0)
            overcommitment += max(0.0, d_kw - (a_kw + tolerance_kw))
    return overcommitment

def calculate_reliability(dispatched: Dict[str, Dict[TimeStep, float]], actuals: Dict[str, Dict[TimeStep, float]]) -> float:
    """
    sum(actual_response_kw) / sum(dispatched_kw)
    Handles zero committed dispatch safely.
    """
    total_d = sum(sum(d_times.values()) for d_times in dispatched.values())
    total_a = sum(sum(a_times.values()) for a_times in actuals.values())
    
    if total_d == 0:
        return 1.0 if total_a == 0 else 0.0
    return total_a / total_d

def calculate_rebound() -> Optional[float]:
    """
    Rebound model is undefined in Phase 4. Returns explicit uncomputable state.
    """
    return None
