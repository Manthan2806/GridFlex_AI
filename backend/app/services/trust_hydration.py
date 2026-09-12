"""Bridge from AI/ML ExperimentalEVModelClient to optimizer context["trust_data"].

This module provides the batch hydration layer that takes a Scenario's resources,
runs the AI/ML inference for each resource via ExperimentalEVModelClient, and
produces the Dict[str, TrustState] mapping that MVPOptimizer expects.

No trust formulas are invented here. All trust calculations are delegated to the
AI/ML team's existing predict_resource() method.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, Sequence

from backend.app.domain.models import FlexibilityResource, TrustState
from backend.app.integrations.ai_ml_client import ExperimentalEVModelClient


def hydrate_trust_context(
    client: ExperimentalEVModelClient,
    resources: Sequence[FlexibilityResource],
    event_time: datetime,
) -> Dict[str, TrustState]:
    """Build context["trust_data"] from live AI/ML inference.

    For each resource, calls client.predict_resource() to obtain the
    ExperimentalEVPrediction containing a TrustState. The result is
    keyed by resource.id for O(1) lookup by the MVPOptimizer.

    Args:
        client: An initialized ExperimentalEVModelClient (demo_mode=True).
        resources: The Scenario.resources list.
        event_time: The scenario start time used for time-of-day features.

    Returns:
        Dict mapping resource_id -> TrustState.

    Raises:
        ValueError: If duplicate resource IDs are found.
    """
    trust_data: Dict[str, TrustState] = {}
    seen_ids: set[str] = set()

    for res in resources:
        if res.id in seen_ids:
            raise ValueError(f"Duplicate resource ID: {res.id}")
        seen_ids.add(res.id)

        # Use the resource's max_power as the requested dispatch for trust estimation,
        # consistent with how the optimizer would plan at full potential.
        prediction = client.predict_resource(
            res, event_time, requested_dispatch_kw=res.max_power
        )
        trust_data[res.id] = prediction.trust_state

    return trust_data


def build_optimizer_context(
    client: ExperimentalEVModelClient,
    resources: Sequence[FlexibilityResource],
    event_time: datetime,
) -> Dict[str, Any]:
    """Build the full optimizer context dict with trust_data populated.

    This is the primary entry point for wiring AI/ML into the experiment runner.
    Returns a dict suitable for passing as `context` to MVPOptimizer.generate_dispatch_plan().
    """
    return {"trust_data": hydrate_trust_context(client, resources, event_time)}
