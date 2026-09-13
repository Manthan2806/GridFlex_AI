import pytest
from backend.app.integrations.simulation_client import SimulationClientBoundary
from backend.app.schemas.runs import SimulationInput, SimulationOutput

class MockTeam4Simulation(SimulationClientBoundary):
    """Mock implementation to verify the contract interface works as expected."""
    def run_simulation(self, sim_input: SimulationInput) -> SimulationOutput:
        # Mocking a trivial response that satisfies the schema
        return SimulationOutput(
            actual_response=[],
            resource_state_evolution=[],
            renewable_outcomes=[],
            system_outcomes=[],
            event_records={"override_events": [], "failure_events": []}
        )

def test_simulation_boundary_instantiation():
    """Ensure the boundary forces the correct implementation signature."""
    client = MockTeam4Simulation()
    assert isinstance(client, SimulationClientBoundary)
    
    # Verify that a class failing to implement run_simulation raises TypeError
    with pytest.raises(TypeError):
        class BadSim(SimulationClientBoundary):
            pass
        BadSim()