"""Experiment-only EV availability and user-override disruptions."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from backend.app.schemas.runs import ActualResponse, SimulationInput, SimulationOutput
from simulation.adapter import SimulationAdapter


@dataclass(frozen=True)
class EVDisruptionOutcome:
    available: bool
    overridden: bool

    @property
    def interrupted(self) -> bool:
        return not self.available or self.overridden


class SeededEVDisruptionAdapter:
    """Apply reproducible EV interruptions after the deterministic simulation.

    The outcome for a resource and timestamp depends only on the seed, resource
    ID and timestamp. Consequently, baseline and trust-aware runs see the same
    underlying conditions regardless of call order or dispatch-plan length.

    This is synthetic experiment evidence. It is deliberately separate from the
    production/demo SimulationAdapter and must not be described as real-world
    validation.
    """

    def __init__(
        self,
        *,
        seed: int,
        base_adapter: SimulationAdapter | None = None,
    ) -> None:
        self.seed = int(seed)
        self.base_adapter = base_adapter or SimulationAdapter()

    def _uniform(self, resource_id: str, time_step: object, stream: str) -> float:
        payload = f"{self.seed}|{resource_id}|{time_step}|{stream}".encode("utf-8")
        value = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
        return value / float(2**64)

    def outcome(
        self,
        *,
        resource_id: str,
        time_step: object,
        availability_rate: float,
        override_rate: float,
    ) -> EVDisruptionOutcome:
        available = self._uniform(resource_id, time_step, "availability") < max(
            0.0, min(1.0, float(availability_rate))
        )
        overridden = self._uniform(resource_id, time_step, "override") < max(
            0.0, min(1.0, float(override_rate))
        )
        return EVDisruptionOutcome(available=available, overridden=overridden)

    def run_simulation(self, sim_input: SimulationInput) -> SimulationOutput:
        ideal_output = self.base_adapter.run_simulation(sim_input)
        resources = {resource.id: resource for resource in sim_input.scenario.resources}
        actual_response: list[ActualResponse] = []
        events = []

        for response in ideal_output.actual_response:
            resource = resources[response.resource_id]
            outcome = self.outcome(
                resource_id=response.resource_id,
                time_step=response.time_step,
                availability_rate=resource.availability_rate,
                override_rate=resource.override_rate,
            )
            delivered_kw = response.delivered_kw
            if delivered_kw > 0.0 and outcome.interrupted:
                delivered_kw = 0.0
                events.append(
                    {
                        "resource_id": response.resource_id,
                        "time_step": response.time_step.isoformat()
                        if hasattr(response.time_step, "isoformat")
                        else response.time_step,
                        "reason": "unavailable"
                        if not outcome.available
                        else "user_override",
                    }
                )
            actual_response.append(
                ActualResponse(
                    resource_id=response.resource_id,
                    time_step=response.time_step,
                    delivered_kw=delivered_kw,
                )
            )

        event_records = dict(ideal_output.event_records)
        event_records["ev_disruptions"] = events
        return ideal_output.model_copy(
            update={
                "actual_response": actual_response,
                "event_records": event_records,
            }
        )
