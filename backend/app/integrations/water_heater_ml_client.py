"""Demo-only bridge from backend resources to the water-heater model bundle."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import fmean, pstdev
from typing import Mapping

from ai_ml.water_heater_model.predict_water_heater_flexibility import load_bundle, predict_flexibility
from backend.app.domain.enums import ResourceType
from backend.app.domain.models import FlexibilityResource, TrustState


class WaterHeaterModelIntegrationError(RuntimeError):
    """Raised when the prototype model cannot be used safely."""


@dataclass(frozen=True)
class WaterHeaterPrediction:
    trust_state: TrustState
    label: str
    release_status: str
    used_demo_fallbacks: tuple[str, ...]


def _history(resource: FlexibilityResource) -> dict[str, float | None]:
    ratios, delivered, available, override = [], [], [], []
    for event in resource.historical_response:
        dispatched = float(event.get("dispatched_kw", event.get("potential_kw", 0.0)))
        delivered_kw = float(event.get("delivered_kw", 0.0))
        if dispatched > 0:
            ratios.append(min(1.0, max(0.0, delivered_kw / dispatched)))
            delivered.append(max(0.0, delivered_kw))
            available.append(float(bool(event.get("is_available", True))))
            override.append(float(bool(event.get("has_override", False))))
    if not ratios:
        return {"prior_event_count": 0.0, "prior_response_ratio_mean": None, "prior_response_ratio_ema": None, "prior_response_ratio_std": None, "prior_delivered_kw_mean": None, "prior_availability_rate": None, "prior_override_rate": None}
    ema = ratios[0]
    for ratio in ratios[1:]:
        ema = 0.35 * ratio + 0.65 * ema
    return {"prior_event_count": float(len(ratios)), "prior_response_ratio_mean": fmean(ratios), "prior_response_ratio_ema": ema, "prior_response_ratio_std": pstdev(ratios) if len(ratios) > 1 else 0.0, "prior_delivered_kw_mean": fmean(delivered), "prior_availability_rate": fmean(available), "prior_override_rate": fmean(override)}


class OfflineDemoWaterHeaterModelClient:
    """Load the accepted bundle and return the canonical TrustState contract."""

    def __init__(self, *, demo_mode: bool = False, repository_root: Path | None = None) -> None:
        if not demo_mode:
            raise WaterHeaterModelIntegrationError("water-heater candidate requires explicit demo mode")
        self.repository_root = repository_root or Path(__file__).resolve().parents[3]
        report_path = self.repository_root / "data/processed/water_heater_training/water_heater_candidate_v1_final_evaluation.json"
        self.report = json.loads(report_path.read_text(encoding="utf-8"))
        if self.report.get("decision") != "accepted_for_hackathon_prototype" or self.report.get("deployment_allowed") is not False:
            raise WaterHeaterModelIntegrationError("water-heater candidate did not pass its prototype gate")
        artifact = self.report["model_artifact"]
        artifact_path = self.repository_root / artifact["path"]
        if hashlib.sha256(artifact_path.read_bytes()).hexdigest() != artifact["sha256"]:
            raise WaterHeaterModelIntegrationError("water-heater artifact hash does not match")
        self.bundle = load_bundle(artifact_path)

    def predict_from_features(self, feature_row: Mapping[str, object]) -> WaterHeaterPrediction:
        output = predict_flexibility(self.bundle, [feature_row])[0]
        return WaterHeaterPrediction(
            trust_state=TrustState(potential_kw=output["potential_kw"], expected_kw=output["expected_kw"], trusted_kw=output["trusted_kw"], confidence=output["confidence"]),
            label="offline prototype estimate (fully synthetic evidence)",
            release_status=self.report["decision"],
            used_demo_fallbacks=(),
        )

    def predict_resource(self, resource: FlexibilityResource, event_time: datetime, requested_dispatch_kw: float, *, flex_direction: str = "reduce") -> WaterHeaterPrediction:
        if resource.type != ResourceType.WATER_HEATER:
            raise ValueError("water-heater client requires a water_heater resource")
        if flex_direction not in {"reduce", "increase"}:
            raise ValueError("flex_direction must be 'reduce' or 'increase'")
        potential = max(0.0, min(float(requested_dispatch_kw), resource.rated_power_kw, resource.max_power))
        medians = self.bundle["config"]["feature_contract"]["imputation_medians"]
        fallback_names = ("heater_type_heat_pump", "tank_capacity_l", "minimum_comfort_temp_c", "maximum_temp_c", "temperature_band_c", "recovery_rate_c_per_hour", "baseline_duty_cycle", "pre_dispatch_temp_c", "pre_dispatch_power_kw", "directional_temperature_margin_c", "directional_temperature_margin_fraction")
        row = {name: medians[name] for name in fallback_names}
        row.update({"rated_power_kw": resource.rated_power_kw, "event_hour": event_time.hour + event_time.minute / 60.0, "event_weekday": float(event_time.weekday()), "flex_direction_reduce": float(flex_direction == "reduce"), "potential_kw": potential, **_history(resource)})
        prediction = self.predict_from_features(row)
        return WaterHeaterPrediction(prediction.trust_state, prediction.label, prediction.release_status, fallback_names)
