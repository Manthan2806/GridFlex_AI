from __future__ import annotations

import csv
from pathlib import Path

from ai_ml.water_heater_model.audit_water_heater_data import audit_dataset
from ai_ml.water_heater_model.generate_water_heater_data import Config, generate


def _paths(root: Path) -> tuple[Path, Path, Path]:
    return (
        root / "water_heater_resources.csv",
        root / "behavior" / "water_heater_historical_response.csv",
        root / "water_heater_dataset_metadata.json",
    )


def test_generated_dataset_passes_audit(tmp_path: Path) -> None:
    generate(tmp_path, Config(seed=20, resource_count=20, history_per_resource=4))
    report = audit_dataset(*_paths(tmp_path))
    assert report["status"] == "PASS"
    assert report["failure_count"] == 0
    assert report["source_hashes_verified"] is True


def test_audit_detects_delivered_power_above_potential(tmp_path: Path) -> None:
    generate(tmp_path, Config(seed=21, resource_count=10, history_per_resource=2))
    history_path = _paths(tmp_path)[1]
    with history_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        columns = list(rows[0])
    rows[0]["delivered_kw"] = str(float(rows[0]["potential_kw"]) + 1)
    with history_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    report = audit_dataset(*_paths(tmp_path))
    assert report["status"] == "FAIL"
    assert any("delivered_kw is outside" in item for item in report["failures"])


def test_audit_reports_leakage_boundary(tmp_path: Path) -> None:
    generate(tmp_path, Config(seed=22, resource_count=10, history_per_resource=2))
    report = audit_dataset(*_paths(tmp_path))
    labels = report["label_columns_do_not_use_as_same_event_features"]
    assert "response_ratio" in labels
    assert "has_override" in labels
    assert "outcome" in labels
