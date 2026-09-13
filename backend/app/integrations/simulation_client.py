from abc import ABC, abstractmethod
from ..schemas.runs import SimulationInput, SimulationOutput

class SimulationClientBoundary(ABC):
    """
    INTERFACE DEFINITION: Backend <-> Simulation Boundary
    
    Team 4: 
    1. Implement this abstract base class in the `simulation/` module.
    2. The backend orchestrator will instantiate/inject your concrete class.
    3. Do NOT modify this file. It represents the frozen contract boundary.
    
    Architectural Rule (ARCHITECTURE.md):
    - Dispatch precedes Simulate.
    - The simulation engine tests the dispatch plan; it does not invent it.
    """

    @abstractmethod
    def run_simulation(self, sim_input: SimulationInput) -> SimulationOutput:
        """
        Executes a time-stepped simulation for the given scenario and dispatch plan.
        
        Args:
            sim_input (SimulationInput): Includes the scenario, initial states,
                                         forecasts, and the x[i,t] dispatch plan.
                                         
        Returns:
            SimulationOutput: Contains the actual delivered responses, state 
                              evolution, and event records (overrides/failures).
        """
        pass