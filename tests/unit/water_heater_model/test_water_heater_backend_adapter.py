from datetime import datetime, timedelta, timezone

import pytest

from backend.app.domain.enums import ResourceType
from backend.app.domain.models import FlexibilityResource
from backend.app.integrations.water_heater_ml_client import OfflineDemoWaterHeaterModelClient, WaterHeaterModelIntegrationError


def _resource() -> FlexibilityResource:
    now = datetime(2026, 9, 13, 10, 0, tzinfo=timezone.utc)
    return FlexibilityResource(id="wh-demo-1", type=ResourceType.WATER_HEATER, location_id="ahmedabad-demo", rated_power_kw=4.5, earliest_start=now, latest_end=now + timedelta(hours=3), required_kwh=4.0, minimum_kwh=0.0, maximum_kwh=10.0, minimum_duration=15, maximum_duration=180, deadline=now + timedelta(hours=3), min_power=0.0, max_power=4.5, historical_response=[], override_rate=0.0, availability_rate=1.0)


def test_adapter_requires_explicit_demo_mode() -> None:
    with pytest.raises(WaterHeaterModelIntegrationError, match="explicit demo mode"):
        OfflineDemoWaterHeaterModelClient()


def test_adapter_returns_valid_trust_state_and_discloses_fallbacks() -> None:
    resource = _resource()
    result = OfflineDemoWaterHeaterModelClient(demo_mode=True).predict_resource(resource, resource.earliest_start, 3.0)
    assert 0 <= result.trust_state.trusted_kw <= result.trust_state.expected_kw <= result.trust_state.potential_kw <= 3.0
    assert result.release_status == "accepted_for_hackathon_prototype"
    assert "tank_capacity_l" in result.used_demo_fallbacks
