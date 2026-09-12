from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from ai_ml.water_heater_model.evaluate_water_heater_baselines import (
    evaluate_baselines,
    write_report as write_baseline_report,
)
from ai_ml.water_heater_model.generate_water_heater_data import Config, generate
from ai_ml.water_heater_model.prepare_water_heater_training_data import (
    MODEL_FEATURE_COLUMNS,
    prepare,
)
from ai_ml.water_heater_model.train_water_heater_candidate import train_candidate


def _inputs(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    generate(source, Config(seed=61, resource_count=80, history_per_resource=6))
    training = tmp_path / "processed" / "training.csv"
    prepare(
        source / "water_heater_resources.csv",
        source / "behavior" / "water_heater_historical_response.csv",
        training,
        tmp_path / "processed" / "training_metadata.json",
    )
    baseline_path = tmp_path / "processed" / "baseline.json"
    write_baseline_report(evaluate_baselines(training), baseline_path)
    return training, baseline_path


def test_candidate_uses_declared_features_and_reports_validation(tmp_path: Path) -> None:
    model, report = train_candidate(*_inputs(tmp_path))
    assert model is not None
    assert report["model"]["feature_names_in_order"] == list(MODEL_FEATURE_COLUMNS)
    assert report["candidate_validation"]["all"]["row_count"] > 0
    assert report["candidate_validation"]["all"]["prediction_bound_violations"] == 0
    assert report["model_artifact_saved"] is False


def test_candidate_does_not_read_test_outcomes(tmp_path: Path) -> None:
    training, baseline = _inputs(tmp_path)
    with training.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fields = list(rows[0])
    for row in rows:
        if row["dataset_split"] == "test":
            row["target_response_ratio"] = "SEALED"
            row["target_delivered_kw"] = "SEALED"
    with training.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    # Regenerate only the baseline report's input hash; its evaluation also
    # proves that sealed test strings are not parsed.
    write_baseline_report(evaluate_baselines(training), baseline)
    _, report = train_candidate(training, baseline)
    assert report["test_holdout"]["target_columns_read"] is False
    assert report["data_boundary"]["sealed_test_rows"] > 0


def test_candidate_training_is_deterministic(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    first_model, first = train_candidate(*inputs)
    second_model, second = train_candidate(*inputs)
    assert first == second
    sample = np.asarray([[value for value in first["model"]["training_only_imputation_medians"].values()]])
    assert np.allclose(first_model.predict(sample), second_model.predict(sample))
