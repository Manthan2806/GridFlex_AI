"""Run one end-to-end EV model to backend TrustState demonstration."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from backend.app.domain.enums import ResourceType
from backend.app.domain.models import FlexibilityResource
from backend.app.integrations.ai_ml_client import ExperimentalEVModelClient


def run_demo() -> dict:
    start = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
    resource = FlexibilityResource(
        id="demo-ev-001",
        type=ResourceType.EV,
        location_id="ahmedabad-demo",
        rated_power_kw=7.2,
        earliest_start=start,
        latest_end=start + timedelta(hours=4),
        required_kwh=8.0,
        minimum_kwh=0.0,
        maximum_kwh=20.0,
        minimum_duration=15,
        maximum_duration=240,
        deadline=start + timedelta(hours=4),
        min_power=0.0,
        max_power=7.2,
        historical_response=[],
        override_rate=0.0,
        availability_rate=1.0,
    )
    prediction = ExperimentalEVModelClient(demo_mode=True).predict_resource(
        resource, start, requested_dispatch_kw=4.0
    )
    return {
        "resource_id": resource.id,
        "label": prediction.label,
        "release_status": prediction.release_status,
        "dispatch_group": prediction.dispatch_group,
        "used_demo_fallbacks": list(prediction.used_demo_fallbacks),
        "trust_state": prediction.trust_state.model_dump(),
    }


def main() -> None:
    print(json.dumps(run_demo(), indent=2))


if __name__ == "__main__":
    main()
