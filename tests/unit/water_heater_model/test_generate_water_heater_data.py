from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from ai_ml.water_heater_model.generate_water_heater_data import Config, generate


def _read(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_generate_counts_and_classification(tmp_path: Path) -> None:
    metadata = generate(tmp_path, Config(seed=9, resource_count=20, history_per_resource=4))
    resources = _read(tmp_path / "water_heater_resources.csv")
    history = _read(tmp_path / "behavior" / "water_heater_historical_response.csv")
    assert len(resources) == 20
    assert len(history) == 80
    assert metadata["classification"] == "SYNTHETIC"
    assert {row["data_classification"] for row in resources} == {"SYNTHETIC"}
    assert {row["data_classification"] for row in history} == {"SYNTHETIC"}


def test_history_is_physical_and_resource_split_is_leakage_safe(tmp_path: Path) -> None:
    generate(tmp_path, Config(seed=12, resource_count=30, history_per_resource=5))
    resources = _read(tmp_path / "water_heater_resources.csv")
    history = _read(tmp_path / "behavior" / "water_heater_historical_response.csv")
    split_by_resource = {row["id"]: row["dataset_split"] for row in resources}
    for row in history:
        assert row["dataset_split"] == split_by_resource[row["resource_id"]]
        assert 0 <= float(row["delivered_kw"]) <= float(row["potential_kw"])
        assert 0 <= float(row["response_ratio"]) <= 1
        timestamp = datetime.fromisoformat(row["timestamp"])
        assert timestamp.tzinfo is not None
        assert timestamp.minute in {0, 15, 30, 45}
        assert timestamp.second == 0


def test_generation_is_reproducible(tmp_path: Path) -> None:
    first = generate(tmp_path / "first", Config(seed=33, resource_count=12, history_per_resource=3))
    second = generate(tmp_path / "second", Config(seed=33, resource_count=12, history_per_resource=3))
    for name in ("water_heater_resources.csv", "behavior/water_heater_historical_response.csv"):
        assert first["files"][name]["sha256"] == second["files"][name]["sha256"]


def test_both_flex_directions_and_heater_types_exist(tmp_path: Path) -> None:
    generate(tmp_path, Config(seed=2806, resource_count=100, history_per_resource=10))
    resources = _read(tmp_path / "water_heater_resources.csv")
    history = _read(tmp_path / "behavior" / "water_heater_historical_response.csv")
    assert {row["heater_type"] for row in resources} == {"heat_pump", "electric_resistance"}
    assert {row["flex_direction"] for row in history} == {"reduce", "increase"}


def test_metadata_file_matches_returned_metadata(tmp_path: Path) -> None:
    metadata = generate(tmp_path, Config(seed=7, resource_count=10, history_per_resource=2))
    stored = json.loads((tmp_path / "water_heater_dataset_metadata.json").read_text())
    assert stored == metadata
