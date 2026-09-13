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
