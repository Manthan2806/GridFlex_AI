"""Experimental EV model adapter for the backend demo.

The final EV candidate did not pass its deployment gate. This adapter therefore
requires explicit demo mode and labels every result as an offline experiment.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import fmean, pstdev
from typing import Mapping

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor

from ai_ml.EV_model.load_ev_training_data import load_ev_training_data
from ai_ml.EV_model.predict_ev_flexibility import predict_flexibility
from backend.app.domain.models import FlexibilityResource, TrustState


DEMO_LABEL = "experimental offline estimate"
V2_DEMO_LABEL = "offline demo estimate (hybrid/synthetic evidence)"


class EVModelIntegrationError(RuntimeError):
    """Raised when the EV experiment cannot be used safely by the backend."""


@dataclass(frozen=True)
class ExperimentalEVPrediction:
    trust_state: TrustState
    label: str
    release_status: str
    dispatch_group: str
    used_demo_fallbacks: tuple[str, ...] = ()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    if path.suffix in (".csv", ".json"):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                digest.update(line.replace("\r\n", "\n").encode("utf-8"))
    else:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def _require_demo_permission(release_status: dict, demo_mode: bool) -> None:
    if release_status.get("deployment_allowed"):
        return
    if not demo_mode or not release_status.get("demo_allowed"):
        raise EVModelIntegrationError(
            "EV model is not deployment-approved; enable explicit demo mode"
        )


def _trust_state_from_output(output: Mapping[str, float]) -> TrustState:
    expected_kw = float(output["expected_kw"])
    trusted_kw = float(output["trusted_kw"])
    potential_kw = float(output["requested_dispatch_kw"])

    if expected_kw == 0.0:
        confidence = 0.0
    else:
        confidence = trusted_kw / expected_kw

    return TrustState(
        potential_kw=potential_kw,
        expected_kw=expected_kw,
        trusted_kw=trusted_kw,
        confidence=max(0.0, min(1.0, confidence)),
    )


def _history_features(resource: FlexibilityResource) -> dict[str, float | None]:
    records = resource.historical_response
    ratios = [
        min(1.0, max(0.0, float(row.get("delivered_kw", 0.0)) / float(row["dispatched_kw"])))
        for row in records
        if float(row.get("dispatched_kw", 0.0)) > 0.0
    ]
    if not records or not ratios:
        return {
            "prior_event_count": 0.0,
            "prior_delivery_ratio_mean": None,
            "prior_delivery_ratio_ema": None,
            "prior_delivery_ratio_std": None,
            "prior_availability_rate": None,
            "prior_override_rate": None,
        }
    ema = ratios[0]
    for ratio in ratios[1:]:
        ema = 0.35 * ratio + 0.65 * ema
    return {
        "prior_event_count": float(len(records)),
        "prior_delivery_ratio_mean": fmean(ratios),
        "prior_delivery_ratio_ema": ema,
        "prior_delivery_ratio_std": pstdev(ratios) if len(ratios) > 1 else 0.0,
        "prior_availability_rate": fmean(bool(row.get("is_available", True)) for row in records),
        "prior_override_rate": fmean(bool(row.get("has_override", False)) for row in records),
    }


class ExperimentalEVModelClient:
    """Lazy-loading adapter from EV inputs to the backend TrustState contract."""

    def __init__(self, *, demo_mode: bool = False, repository_root: Path | None = None) -> None:
        self.repository_root = repository_root or Path(__file__).resolve().parents[3]
        self.config_path = self.repository_root / "data/processed/ev_training/ev_model_candidate_config.json"
        self.status_path = self.repository_root / "data/processed/ev_training/ev_release_status.json"
        self.training_path = self.repository_root / "data/processed/ev_training/ev_training_examples.csv"
        with self.config_path.open(encoding="utf-8") as handle:
            self.config = json.load(handle)
        with self.status_path.open(encoding="utf-8") as handle:
            self.release_status = json.load(handle)
        _require_demo_permission(self.release_status, demo_mode)
        if self.release_status["evidence"]["locked_config"]["sha256"] != _sha256(self.config_path):
            raise EVModelIntegrationError("EV configuration does not match release evidence")
        if self.config["inputs"]["training_table"]["sha256"] != _sha256(self.training_path):
            raise EVModelIntegrationError("EV training data changed after model locking")
        self._model: RandomForestRegressor | None = None

    def _get_model(self) -> RandomForestRegressor:
        if self._model is None:
            data = load_ev_training_data(self.training_path)
            self._model = RandomForestRegressor(**self.config["model"]["parameters"])
            self._model.fit(data.train.features, data.train.targets)
        return self._model

    def predict_from_features(
        self, feature_row: Mapping[str, object], requested_dispatch_kw: float
    ) -> ExperimentalEVPrediction:
        output = predict_flexibility(
            self._get_model(), self.config, [feature_row], [requested_dispatch_kw]
        )[0]
        return ExperimentalEVPrediction(
            trust_state=_trust_state_from_output(output),
            label=DEMO_LABEL,
            release_status=str(self.release_status["release_status"]),
            dispatch_group=str(output["dispatch_group"]),
        )

    def predict_resource(
        self,
        resource: FlexibilityResource,
        event_time: datetime,
        requested_dispatch_kw: float,
    ) -> ExperimentalEVPrediction:
        """Adapt the current backend EV resource using explicit demo fallbacks."""
        potential_kw = max(
            0.0,
            min(float(requested_dispatch_kw), resource.max_power, resource.rated_power_kw),
        )
        medians = self.config["feature_contract"]["imputation_medians"]
        connection_hours = max(
            0.25, (resource.latest_end - resource.earliest_start).total_seconds() / 3600.0
        )
        battery_capacity = float(medians["battery_capacity_kwh"])
        feature_row: dict[str, object] = {
            "rated_power_kw": resource.rated_power_kw,
            "max_power_kw": resource.max_power,
            "required_kwh": resource.required_kwh,
            "battery_capacity_kwh": battery_capacity,
            "arrival_soc_pct": medians["arrival_soc_pct"],
            "target_soc_pct": medians["target_soc_pct"],
            "soc_gap_pct": medians["soc_gap_pct"],
            "connection_window_hours": connection_hours,
            "required_energy_share": resource.required_kwh / battery_capacity,
            "average_required_power_kw": resource.required_kwh / connection_hours,
            "event_hour": event_time.hour + event_time.minute / 60.0,
            "event_weekday": float(event_time.weekday()),
            **_history_features(resource),
        }
        result = self.predict_from_features(feature_row, potential_kw)
        return ExperimentalEVPrediction(
            trust_state=result.trust_state,
            label=result.label,
            release_status=result.release_status,
            dispatch_group=result.dispatch_group,
            used_demo_fallbacks=(
                "battery_capacity_kwh",
                "arrival_soc_pct",
                "target_soc_pct",
                "soc_gap_pct",
            ),
        )


class OfflineDemoEVModelClientV2:
    """Load the accepted offline-demo v2 bundle without request-time retraining."""

    def __init__(
        self, *, demo_mode: bool = False, repository_root: Path | None = None
    ) -> None:
        self.repository_root = repository_root or Path(__file__).resolve().parents[3]
        self.config_path = (
            self.repository_root
            / "data/processed/ev_training/v2/ev_candidate_v2_config.json"
        )
        self.report_path = (
            self.repository_root
            / "data/processed/ev_training/v2/ev_candidate_v2_final_evaluation.json"
        )
        with self.config_path.open(encoding="utf-8") as handle:
            self.config = json.load(handle)
        with self.report_path.open(encoding="utf-8") as handle:
            self.report = json.load(handle)
        if not demo_mode:
            raise EVModelIntegrationError("EV candidate v2 requires explicit demo mode")
        if self.report.get("decision") != "accepted_for_offline_demo":
            raise EVModelIntegrationError("EV candidate v2 did not pass its offline demo gate")
        if self.report.get("deployment_allowed") is not False:
            raise EVModelIntegrationError("EV candidate v2 has an invalid deployment status")
        if not self.report.get("demo_allowed"):
            raise EVModelIntegrationError("EV candidate v2 is not allowed for demo use")
        artifact = self.report.get("model_artifact", {})
        artifact_path = str(artifact.get("path", "")).replace("\\", "/")
        self.model_path = self.repository_root / Path(artifact_path)
        if not artifact.get("saved") or not self.model_path.is_file():
            raise EVModelIntegrationError("EV candidate v2 demo artifact is unavailable")
        if artifact.get("sha256") != _sha256(self.model_path):
            raise EVModelIntegrationError("EV candidate v2 artifact hash does not match")
        bundle = joblib.load(self.model_path)
        if bundle.get("candidate_version") != self.config.get("candidate_version"):
            raise EVModelIntegrationError("EV candidate v2 bundle and config do not match")
        self.expected_model = bundle["expected_model"]
        self.lower_bound_model = bundle["lower_bound_model"]

    def _predict_feature_row(
        self, feature_row: Mapping[str, object], requested_dispatch_kw: float
    ) -> ExperimentalEVPrediction:
        if requested_dispatch_kw < 0.0:
            raise ValueError("requested dispatch must be non-negative")
        contract = self.config["feature_contract"]
        values = []
        for name in contract["names_in_order"]:
            raw = feature_row.get(name)
            if raw is None or raw == "":
                raw = contract["imputation_medians"][name]
            value = float(raw)
            if not np.isfinite(value):
                raise ValueError(f"feature {name!r} must be finite")
            values.append(value)
        matrix = np.asarray([values], dtype=float)
        expected_ratio = float(
            np.clip(self.expected_model.predict(matrix)[0], 0.0, 1.0)
        )
        lower_ratio = min(
            expected_ratio,
            float(np.clip(self.lower_bound_model.predict(matrix)[0], 0.0, 1.0)),
        )
        thresholds = self.config["safety_policy"]["dispatch_group_thresholds_kw"]
        if requested_dispatch_kw <= float(thresholds["small_max"]):
            dispatch_group = "small"
        elif requested_dispatch_kw <= float(thresholds["medium_max"]):
            dispatch_group = "medium"
        else:
            dispatch_group = "large"
        adjustments = self.config["safety_policy"][
            "conformal_adjustment_ratio_by_dispatch_group"
        ]
        trusted_ratio = max(0.0, lower_ratio - float(adjustments[dispatch_group]))
        expected_kw = requested_dispatch_kw * expected_ratio
        trusted_kw = requested_dispatch_kw * trusted_ratio
        return ExperimentalEVPrediction(
            trust_state=TrustState(
                potential_kw=requested_dispatch_kw,
                expected_kw=expected_kw,
                trusted_kw=trusted_kw,
                confidence=trusted_kw / expected_kw if expected_kw > 0.0 else 0.0,
            ),
            label=V2_DEMO_LABEL,
            release_status="accepted_for_offline_demo",
            dispatch_group=dispatch_group,
        )

    def predict_resource(
        self,
        resource: FlexibilityResource,
        event_time: datetime,
        requested_dispatch_kw: float,
    ) -> ExperimentalEVPrediction:
        potential_kw = max(
            0.0,
            min(float(requested_dispatch_kw), resource.max_power, resource.rated_power_kw),
        )
        medians = self.config["feature_contract"]["imputation_medians"]
        connection_hours = max(
            0.25,
            (resource.latest_end - resource.earliest_start).total_seconds() / 3600.0,
        )
        battery_capacity = float(medians["battery_capacity_kwh"])
        feature_row: dict[str, object] = {
            "rated_power_kw": resource.rated_power_kw,
            "max_power_kw": resource.max_power,
            "required_kwh": resource.required_kwh,
            "battery_capacity_kwh": battery_capacity,
            "arrival_soc_pct": medians["arrival_soc_pct"],
            "target_soc_pct": medians["target_soc_pct"],
            "soc_gap_pct": medians["soc_gap_pct"],
            "connection_window_hours": connection_hours,
            "required_energy_share": resource.required_kwh / battery_capacity,
            "average_required_power_kw": resource.required_kwh / connection_hours,
            "event_hour": event_time.hour + event_time.minute / 60.0,
            "event_weekday": float(event_time.weekday()),
            **_history_features(resource),
        }
        result = self._predict_feature_row(feature_row, potential_kw)
        return ExperimentalEVPrediction(
            trust_state=result.trust_state,
            label=result.label,
            release_status=result.release_status,
            dispatch_group=result.dispatch_group,
            used_demo_fallbacks=(
                "battery_capacity_kwh",
                "arrival_soc_pct",
                "target_soc_pct",
                "soc_gap_pct",
            ),
        )
