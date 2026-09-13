from __future__ import annotations

import csv
from pathlib import Path

from ai_ml.water_heater_model.evaluate_water_heater_baselines import (
    evaluate_baselines,
)
from ai_ml.water_heater_model.generate_water_heater_data import Config, generate
from ai_ml.water_heater_model.prepare_water_heater_training_data import prepare


def _training_table(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    generate(source, Config(seed=51, resource_count=40, history_per_resource=5))
    output = tmp_path / "processed" / "training.csv"
    prepare(
        source / "water_heater_resources.csv",
        source / "behavior" / "water_heater_historical_response.csv",
        output,
        tmp_path / "processed" / "metadata.json",
    )
    return output


def test_all_declared_baselines_are_evaluated(tmp_path: Path) -> None:
    report = evaluate_baselines(_training_table(tmp_path))
    assert set(report["baselines"]) == {
        "global_train_mean",
        "heater_type_mean",
        "heater_type_direction_mean",
        "prior_resource_mean",
        "prior_resource_ema",
    }
    for result in report["baselines"].values():
        assert result["validation"]["all"]["prediction_bound_violations"] == 0


def test_test_outcomes_are_not_read(tmp_path: Path) -> None:
    path = _training_table(tmp_path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fields = list(rows[0])
    for row in rows:
        if row["dataset_split"] == "test":
            row["target_delivered_kw"] = "SEALED"
            row["target_response_ratio"] = "SEALED"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    report = evaluate_baselines(path)
    assert report["test_holdout"]["target_columns_read"] is False
    assert report["test_holdout"]["status"] == "sealed"


def test_evaluation_is_deterministic(tmp_path: Path) -> None:
    path = _training_table(tmp_path)
    assert evaluate_baselines(path) == evaluate_baselines(path)


def test_validation_groups_are_reported(tmp_path: Path) -> None:
    report = evaluate_baselines(_training_table(tmp_path))
    for baseline in report["baselines"].values():
        groups = baseline["validation"]
        assert {"all", "cold_start", "with_history"}.issubset(groups)
        assert {"heat_pump", "electric_resistance"}.issubset(groups)
        assert {"reduce", "increase"}.issubset(groups)
