from datetime import datetime, timedelta, timezone

import pytest

from ai_ml.EV_model.load_ev_training_data import load_ev_training_data
from backend.app.domain.enums import ResourceType
from backend.app.domain.models import FlexibilityResource
from backend.app.integrations.ai_ml_client import (
    DEMO_LABEL,
    EVModelIntegrationError,
    ExperimentalEVModelClient,
    _require_demo_permission,
    _trust_state_from_output,
)


def test_rejected_model_requires_explicit_demo_mode():
    status = {"deployment_allowed": False, "demo_allowed": True}
    with pytest.raises(EVModelIntegrationError, match="demo mode"):
        _require_demo_permission(status, demo_mode=False)
    _require_demo_permission(status, demo_mode=True)


def test_prediction_maps_to_backend_trust_contract():
    # Normal case
    trust = _trust_state_from_output(
        {
            "requested_dispatch_kw": 4.0,
            "expected_kw": 2.0,
            "trusted_kw": 1.4,
            "safety_coverage": 0.85, # Metadata, unused for confidence now
        }
    )
    assert trust.potential_kw == 4.0
    assert trust.expected_kw == 2.0
    assert trust.trusted_kw == 1.4
    assert trust.confidence == 0.7  # 1.4 / 2.0

    # Zero expected case
    trust_zero = _trust_state_from_output(
        {
            "requested_dispatch_kw": 4.0,
            "expected_kw": 0.0,
            "trusted_kw": 0.0,
        }
    )
    assert trust_zero.confidence == 0.0

def test_evidence_hashing_cross_platform(tmp_path):
    from backend.app.integrations.ai_ml_client import _sha256

    file_lf = tmp_path / "test_lf.csv"
    file_lf.write_bytes(b"a,b,c\n1,2,3\n")

    file_crlf = tmp_path / "test_crlf.csv"
    file_crlf.write_bytes(b"a,b,c\r\n1,2,3\r\n")

    assert _sha256(file_lf) == _sha256(file_crlf)


def test_demo_client_predicts_from_locked_features():
    client = ExperimentalEVModelClient(demo_mode=True)
    data = load_ev_training_data()
    feature_row = dict(zip(data.feature_names, data.validation.features[0]))
    result = client.predict_from_features(feature_row, 4.0)
    assert result.label == DEMO_LABEL
    assert result.release_status == "experimental_not_deployable"
    assert result.trust_state.trusted_kw <= result.trust_state.expected_kw
    assert result.trust_state.expected_kw <= result.trust_state.potential_kw


def test_demo_client_adapts_existing_backend_ev_resource():
    start = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
    resource = FlexibilityResource(
        id="demo-ev-1",
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
    result = ExperimentalEVModelClient(demo_mode=True).predict_resource(
        resource, start, requested_dispatch_kw=4.0
    )
    assert result.label == DEMO_LABEL
    assert result.used_demo_fallbacks
    assert result.trust_state.potential_kw == 4.0
    assert result.trust_state.trusted_kw <= result.trust_state.expected_kw <= 4.0
