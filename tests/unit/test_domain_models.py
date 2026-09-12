import pytest
from pydantic import ValidationError
from backend.app.domain.models import TrustState

def test_trust_ordering_invariant():
    """Validates DOMAIN_MODEL.md invariant: trusted_kw <= expected_kw <= potential_kw"""
    
    # Valid ordering
    trust = TrustState(
        potential_kw=10.0,
        expected_kw=8.0,
        trusted_kw=5.0,
        confidence=0.9
    )
    assert trust.trusted_kw == 5.0
    
    # Invalid ordering: expected > potential
    with pytest.raises(ValidationError):
        TrustState(
            potential_kw=10.0,
            expected_kw=12.0,
            trusted_kw=5.0,
            confidence=0.9
        )
        
    # Invalid ordering: trusted > expected
    with pytest.raises(ValidationError):
        TrustState(
            potential_kw=10.0,
            expected_kw=8.0,
            trusted_kw=9.0,
            confidence=0.9
        )