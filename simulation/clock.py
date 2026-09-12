from datetime import datetime, timedelta
from typing import List

class SimulationClock:
    """
    Minimal deterministic simulation clock operating at a strictly 15-minute resolution.
    """
    STEP_RESOLUTION = timedelta(minutes=15)

    def __init__(self, start_time: datetime, horizon_steps: int):
        """
        Initialize the simulation clock.
        
        Args:
            start_time: The starting datetime of the simulation.
            horizon_steps: The total number of 15-minute steps to simulate.
        """
        if horizon_steps < 0:
            raise ValueError("Horizon steps cannot be negative.")
        
        self.start_time = start_time
        self.horizon_steps = horizon_steps
        self.current_step_index = 0

    @property
    def current_time(self) -> datetime:
        """Returns the actual datetime of the current simulation step."""
        return self.start_time + (self.current_step_index * self.STEP_RESOLUTION)

    def is_complete(self) -> bool:
        """Returns True if the simulation has reached the end of the horizon."""
        return self.current_step_index >= self.horizon_steps

    def tick(self) -> None:
        """Advances the clock by one 15-minute timestep."""
        if self.is_complete():
            raise RuntimeError("Simulation horizon already completed. Cannot advance clock.")
        self.current_step_index += 1

    def get_full_horizon_times(self) -> List[datetime]:
        """Returns a list of all datetimes in the simulation horizon."""
        return [self.start_time + (i * self.STEP_RESOLUTION) for i in range(self.horizon_steps)]
