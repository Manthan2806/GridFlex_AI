from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pytest

from ai_ml.water_heater_model.evaluate_water_heater_final import run_final_evaluation
from ai_ml.water_heater_model.predict_water_heater_flexibility import predict_flexibility


ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "data/processed/water_heater_training/water_heater_candidate_v1_config.json"
REPORT = ROOT / "data/processed/water_heater_training/water_heater_candidate_v1_final_evaluation.json"
ARTIFACT = ROOT / "ai_ml/water_heater_model/artifacts/water_heater_candidate_v1_demo_bundle.joblib"
TRAINING = ROOT / "data/processed/water_heater_training/water_heater_training_examples.csv"


def test_release_evidence_and_artifact_are_consistent() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert config["status"] == "locked_for_final_holdout"
    assert report["decision"] == "accepted_for_hackathon_prototype"
    assert report["deployment_allowed"] is False
    assert report["holdout"]["training_resource_overlap"] == 0
    assert all(report["acceptance_checks"].values())
    assert hashlib.sha256(ARTIFACT.read_bytes()).hexdigest() == report["model_artifact"]["sha256"]


def test_release_safety_groups_pass_predeclared_limit() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert set(report["safety"]["groups"]) == {
        "all", "heat_pump", "electric_resistance", "reduce", "increase", "small", "medium", "large"
    }
    assert all(group["passes"] for group in report["safety"]["groups"].values())
    assert report["safety"]["trusted_kw_retained_percent"] > 0


def test_saved_bundle_produces_bounded_backend_values() -> None:
    bundle = joblib.load(ARTIFACT)
    names = bundle["config"]["feature_contract"]["names_in_order"]
    with TRAINING.open(newline="", encoding="utf-8") as handle:
        source = next(csv.DictReader(handle))
    row = {name: source[name] for name in names}
    result = predict_flexibility(bundle, [row])[0]
    assert set(result) == {"potential_kw", "expected_ratio", "trusted_ratio", "expected_kw", "trusted_kw", "confidence"}
    assert 0 <= result["trusted_kw"] <= result["expected_kw"] <= result["potential_kw"]
    assert 0 <= result["confidence"] <= 1


def test_final_evaluation_refuses_to_reuse_existing_holdout() -> None:
    with pytest.raises(FileExistsError, match="refusing to consume"):
        run_final_evaluation(TRAINING, CONFIG, REPORT, ARTIFACT)


def test_prediction_rejects_missing_required_feature() -> None:
    bundle = joblib.load(ARTIFACT)
    with pytest.raises(ValueError, match="required feature"):
        predict_flexibility(bundle, [{"potential_kw": 1.0}])
