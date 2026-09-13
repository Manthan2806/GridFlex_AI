"""Small, explicit water-heater inference and simulation service for the MVP."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from backend.app.domain.enums import ResourceType
from backend.app.domain.models import FlexibilityResource
from backend.app.integrations.water_heater_ml_client import OfflineDemoWaterHeaterModelClient


DEFAULT_FEEDER_CAPACITY_KW = 15.0


def _resource(
    resource_id: str,
    rated_power_kw: float,
    required_kwh: float,
    availability_rate: float,
    override_rate: float,
    start: datetime,
) -> FlexibilityResource:
    return FlexibilityResource(
        id=resource_id,
        type=ResourceType.WATER_HEATER,
        location_id="ahmedabad-demo",
        rated_power_kw=rated_power_kw,
        earliest_start=start,
        latest_end=start + timedelta(hours=4),
        required_kwh=required_kwh,
        minimum_kwh=0.0,
        maximum_kwh=required_kwh * 2.0,
        minimum_duration=15,
        maximum_duration=240,
        deadline=start + timedelta(hours=4),
        min_power=0.0,
        max_power=rated_power_kw,
        historical_response=[],
        override_rate=override_rate,
        availability_rate=availability_rate,
    )


def demo_water_heaters(event_time: datetime | None = None) -> tuple[FlexibilityResource, ...]:
    """Return household-scale prototype resources within the training range."""
    start = event_time or datetime(2026, 9, 13, 18, 0, tzinfo=timezone.utc)
    return (
        _resource("wh-demo-001", 3.85, 4.0, 0.88, 0.08, start),
        _resource("wh-demo-002", 4.40, 5.0, 0.82, 0.12, start),
        _resource("wh-demo-003", 3.95, 4.5, 0.91, 0.06, start),
        _resource("wh-demo-004", 4.20, 5.5, 0.79, 0.15, start),
        _resource("wh-demo-005", 3.70, 3.5, 0.94, 0.04, start),
    )


def run_water_heater_simulation(
    *,
    event_time: datetime | None = None,
    feeder_capacity_kw: float = DEFAULT_FEEDER_CAPACITY_KW,
) -> dict:
    if feeder_capacity_kw <= 0:
        raise ValueError("feeder capacity must be positive")
    timestamp = event_time or datetime(2026, 9, 13, 18, 0, tzinfo=timezone.utc)
    resources = demo_water_heaters(timestamp)
    client = OfflineDemoWaterHeaterModelClient(demo_mode=True)
    predictions = [
        client.predict_resource(
            resource,
            timestamp,
            requested_dispatch_kw=resource.rated_power_kw,
            flex_direction="reduce",
        )
        for resource in resources
    ]
    total_trusted = sum(item.trust_state.trusted_kw for item in predictions)
    scale = min(1.0, feeder_capacity_kw / total_trusted) if total_trusted else 0.0

    rows = []
    total_dispatched = 0.0
    total_delivered = 0.0
    for resource, prediction in zip(resources, predictions):
        state = prediction.trust_state
        dispatched = state.trusted_kw * scale
        # Deterministic demo response; this is not field measurement.
        delivered = dispatched * resource.availability_rate
        total_dispatched += dispatched
        total_delivered += delivered
        rows.append(
            {
                "resource_id": resource.id,
                "type": resource.type.value,
                "location_id": resource.location_id,
                "rated_power_kw": resource.rated_power_kw,
                "earliest_start": resource.earliest_start.isoformat(),
                "latest_end": resource.latest_end.isoformat(),
                "required_kwh": resource.required_kwh,
                "minimum_kwh": resource.minimum_kwh,
                "maximum_kwh": resource.maximum_kwh,
                "minimum_duration": resource.minimum_duration,
                "maximum_duration": resource.maximum_duration,
                "deadline": resource.deadline.isoformat(),
                "min_power": resource.min_power,
                "max_power": resource.max_power,
                "availability_rate": resource.availability_rate,
                "override_rate": resource.override_rate,
                "potential_kw": round(state.potential_kw, 6),
                "expected_kw": round(state.expected_kw, 6),
                "trusted_kw": round(state.trusted_kw, 6),
                "confidence": round(state.confidence, 6),
                "dispatched_kw": round(dispatched, 6),
                "delivered_kw": round(delivered, 6),
                "overcommitment_kw": round(max(0.0, dispatched - delivered), 6),
                "used_demo_fallbacks": list(prediction.used_demo_fallbacks),
            }
        )
    return {
        "demo_mode": True,
        "label": "offline prototype estimate (fully synthetic evidence)",
        "release_status": "accepted_for_hackathon_prototype",
        "deployment_allowed": False,
        "event_time": timestamp.isoformat(),
        "simulation_mode": "deterministic_demo_not_field_measurement",
        "feeder_capacity_kw": feeder_capacity_kw,
        "total_potential_kw": round(sum(row["potential_kw"] for row in rows), 6),
        "total_expected_kw": round(sum(row["expected_kw"] for row in rows), 6),
        "total_trusted_kw": round(total_trusted, 6),
        "total_dispatched_kw": round(total_dispatched, 6),
        "total_delivered_kw": round(total_delivered, 6),
        "resources": rows,
        "limitations": [
            "Water-heater response evidence is fully synthetic.",
            "Missing physical state uses disclosed training-median fallbacks.",
            "This endpoint supports a hackathon prototype, not real dispatch.",
        ],
    }
