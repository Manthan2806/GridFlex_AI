import pytest
from unittest.mock import patch, MagicMock
from backend.app.main import simulate_full
from backend.app.schemas.dispatch import DispatchPlan
from backend.app.domain.enums import OptimizationStatus

@patch("backend.app.main.ExperimentalEVModelClient", create=True)
@patch("backend.app.main.MVPOptimizer", create=True)
@patch("backend.app.main.SimulationAdapter", create=True)
@patch("backend.app.main.build_optimizer_context", create=True)
@patch("backend.app.main.SessionLocal", create=True)
def test_simulate_full_uses_canonical_stack(
    mock_session_local, mock_build_ctx, mock_sim_adapter_cls, mock_optimizer_cls, mock_ev_client_cls
):
    # Setup mocks
    mock_ev_client = MagicMock()
    mock_ev_client_cls.return_value = mock_ev_client
    
    mock_ctx = {"trust_data": {}}
    mock_build_ctx.return_value = mock_ctx
    
    mock_optimizer = MagicMock()
    mock_optimizer_cls.return_value = mock_optimizer
    
    mock_plan = DispatchPlan(dispatch_plan=[], objective_value=0.0, status=OptimizationStatus.FEASIBLE)
    mock_optimizer.generate_dispatch_plan.return_value = mock_plan
    
    mock_sim_adapter = MagicMock()
    mock_sim_adapter_cls.return_value = mock_sim_adapter
    
    # We must return a valid dict simulating a SimulationOutput.model_dump()
    mock_sim_output = MagicMock()
    mock_sim_output.model_dump.return_value = {"actual_response": [], "resource_state_evolution": [], "renewable_outcomes": [], "system_outcomes": [], "event_records": {}}
    mock_sim_output.model_dump_json.return_value = '{"actual_response": [], "resource_state_evolution": [], "renewable_outcomes": [], "system_outcomes": [], "event_records": {}}'
    mock_sim_adapter.run_simulation.return_value = mock_sim_output

    # Mock DB session
    mock_session = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_session

    # Perform request
    response = simulate_full()

    # Assertions
    assert isinstance(response, dict)
    
    # Prove AI/ML trust hydration is reached (client instantiated with demo_mode=True)
    mock_ev_client_cls.assert_called_once_with(demo_mode=True)
    mock_build_ctx.assert_called_once()
    
    # Prove MVPOptimizer is used
    mock_optimizer_cls.assert_called_once()
    mock_optimizer.generate_dispatch_plan.assert_called_once()
    call_args = mock_optimizer.generate_dispatch_plan.call_args[0]
    assert call_args[1] == "trusted_kw"
    assert call_args[2] == mock_ctx
    
    # Prove SimulationAdapter is used
    mock_sim_adapter_cls.assert_called_once()
    mock_sim_adapter.run_simulation.assert_called_once()

    # Prove persistence was invoked
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    added_run = mock_session.add.call_args[0][0]
    assert added_run.total_dispatched_kw == 0.0
    assert added_run.total_delivered_kw == 0.0
    # Ensure feeder_capacity_kw is not present
    assert not hasattr(added_run, "feeder_capacity_kw")

from backend.app.main import get_resources
from backend.app.domain.models import TrustState

@patch("backend.app.main.ExperimentalEVModelClient", create=True)
@patch("backend.app.main.hydrate_trust_context", create=True)
def test_get_resources_canonical(mock_hydrate, mock_ev_client_cls):
    # Mock trust data returned by AI/ML client
    mock_hydrate.return_value = {
        "ev-1": TrustState(potential_kw=7.4, expected_kw=7.4, trusted_kw=7.4, confidence=1.0),
        "ev-2": TrustState(potential_kw=11.0, expected_kw=11.0, trusted_kw=11.0, confidence=1.0),
        "ev-3": TrustState(potential_kw=3.7, expected_kw=3.7, trusted_kw=3.7, confidence=1.0),
    }

    response = get_resources()

    assert isinstance(response, list)
    assert len(response) == 3

    # Verify canonical models mapped cleanly without feeder_capacity_kw
    for res in response:
        assert not hasattr(res, "feeder_capacity_kw")
        assert res.state == "available"
        assert res.type == "ev"
        assert res.potential_kw is not None
        assert res.expected_kw is not None
        assert res.trusted_kw is not None
        assert res.confidence == 1.0
        assert hasattr(res, "historical_response")
        assert isinstance(res.historical_response, list)
        assert len(res.historical_response) == 0

    mock_ev_client_cls.assert_called_once_with(demo_mode=True)
    mock_hydrate.assert_called_once()

@patch("backend.app.main.ExperimentalEVModelClient", create=True)
@patch("backend.app.main.MVPOptimizer", create=True)
@patch("backend.app.main.build_optimizer_context", create=True)
def test_get_dispatch_canonical(mock_build_ctx, mock_optimizer_cls, mock_ev_client_cls):
    # Mock trust data
    mock_ctx = {
        "trust_data": {
            "ev-1": TrustState(potential_kw=7.4, expected_kw=7.4, trusted_kw=7.4, confidence=1.0),
            "ev-2": TrustState(potential_kw=11.0, expected_kw=11.0, trusted_kw=11.0, confidence=1.0),
            "ev-3": TrustState(potential_kw=3.7, expected_kw=3.7, trusted_kw=3.7, confidence=1.0),
        }
    }
    mock_build_ctx.return_value = mock_ctx
    
    mock_optimizer = MagicMock()
    mock_optimizer_cls.return_value = mock_optimizer
    
    from backend.app.schemas.dispatch import DispatchInstruction, DispatchPlan
    from backend.app.schemas.core import TimeStep
    from datetime import datetime, timezone
    
    now = datetime.now(timezone.utc)
    mock_plan = DispatchPlan(
        dispatch_plan=[
            DispatchInstruction(resource_id="ev-1", time_step=now, power_kw=7.4),
            DispatchInstruction(resource_id="ev-2", time_step=now, power_kw=11.0)
        ],
        objective_value=0.0,
        status=OptimizationStatus.FEASIBLE
    )
    mock_optimizer.generate_dispatch_plan.return_value = mock_plan
    
    from backend.app.main import get_dispatch
    
    response = get_dispatch()
    
    # Assertions
    assert response.scenario.id == "dispatch-scenario-canonical"
    assert not hasattr(response, "renewableOpportunity")
    
    assert response.flexibility.trustedKw == 22.1
    
    assert response.recommendedDispatch.status == "recommendation_ready"
    assert response.recommendedDispatch.totalDispatchedKw == 18.4
    
    assert response.constraintCheck.passed is True
    
    mock_ev_client_cls.assert_called_once_with(demo_mode=True)
    mock_build_ctx.assert_called_once()
    mock_optimizer.generate_dispatch_plan.assert_called_once()
    call_args = mock_optimizer.generate_dispatch_plan.call_args[0]
    assert call_args[1] == "trusted_kw"

@patch("backend.app.main.ExperimentalEVModelClient", create=True)
@patch("backend.app.main.MVPOptimizer", create=True)
@patch("backend.app.main.build_optimizer_context", create=True)
def test_get_dispatch_infeasible(mock_build_ctx, mock_optimizer_cls, mock_ev_client_cls):
    mock_ctx = {"trust_data": {}}
    mock_build_ctx.return_value = mock_ctx
    
    mock_optimizer = MagicMock()
    mock_optimizer_cls.return_value = mock_optimizer
    
    from backend.app.schemas.dispatch import DispatchPlan
    from backend.app.domain.enums import OptimizationStatus
    
    mock_plan = DispatchPlan(
        dispatch_plan=[],
        objective_value=0.0,
        status=OptimizationStatus.INFEASIBLE,
        infeasibility_report="Resource ev-1 missed required energy by 10.0 kWh before deadline"
    )
    mock_optimizer.generate_dispatch_plan.return_value = mock_plan
    
    from backend.app.main import get_dispatch
    response = get_dispatch()
    
    assert response.recommendedDispatch.status == "infeasible"
    assert response.constraintCheck.passed is False
    assert len(response.constraintCheck.violations) == 1
    assert response.constraintCheck.violations[0] == "Resource ev-1 missed required energy by 10.0 kWh before deadline"
