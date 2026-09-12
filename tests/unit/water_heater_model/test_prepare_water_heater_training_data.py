from __future__ import annotations

import csv
from pathlib import Path

from ai_ml.water_heater_model.generate_water_heater_data import Config, generate
from ai_ml.water_heater_model.prepare_water_heater_training_data import (
    MODEL_FEATURE_COLUMNS,
    TARGET_COLUMNS,
    TrainingDataError,
    build_training_rows,
    prepare,
)


def _source_paths(root: Path) -> tuple[Path, Path]:
    return (
        root / "water_heater_resources.csv",
        root / "behavior" / "water_heater_historical_response.csv",
    )


def test_preparation_preserves_counts_and_resource_splits(tmp_path: Path) -> None:
    source = tmp_path / "source"
    generate(source, Config(seed=31, resource_count=20, history_per_resource=4))
    output = tmp_path / "processed" / "training.csv"
    metadata = tmp_path / "processed" / "metadata.json"
    result = prepare(*_source_paths(source), output, metadata)
    with output.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 80
    assert result["row_count"] == 80
    splits_by_resource: dict[str, set[str]] = {}
    for row in rows:
        splits_by_resource.setdefault(row["resource_id"], set()).add(row["dataset_split"])
    assert all(len(splits) == 1 for splits in splits_by_resource.values())


def test_prior_features_use_only_earlier_events(tmp_path: Path) -> None:
    source = tmp_path / "source"
    generate(source, Config(seed=32, resource_count=4, history_per_resource=4))
    rows = build_training_rows(*_source_paths(source))
    first_resource = [row for row in rows if row["resource_id"] == "wh-0001"]
    assert first_resource[0]["prior_event_count"] == 0
    assert first_resource[0]["prior_response_ratio_mean"] == ""
    assert first_resource[1]["prior_event_count"] == 1
    assert first_resource[1]["prior_response_ratio_mean"] == first_resource[0][
        "target_response_ratio"
    ]


def test_current_outcomes_are_not_model_features() -> None:
    forbidden = {
        "target_delivered_kw",
        "target_response_ratio",
        "target_is_available",
        "target_has_override",
        "target_outcome",
        "target_hot_water_draw_l",
        "hot_water_draw_l",
    }
    assert forbidden.isdisjoint(MODEL_FEATURE_COLUMNS)
    assert forbidden - {"hot_water_draw_l"} == set(TARGET_COLUMNS)


def test_preparation_is_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "source"
    generate(source, Config(seed=33, resource_count=8, history_per_resource=3))
    first = build_training_rows(*_source_paths(source))
    second = build_training_rows(*_source_paths(source))
    assert first == second


def test_split_mismatch_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source"
    generate(source, Config(seed=34, resource_count=8, history_per_resource=2))
    history_path = _source_paths(source)[1]
    with history_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        columns = list(rows[0])
    rows[0]["dataset_split"] = "test" if rows[0]["dataset_split"] != "test" else "train"
    with history_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    try:
        build_training_rows(*_source_paths(source))
    except TrainingDataError as error:
        assert "split does not match" in str(error)
    else:
        raise AssertionError("split mismatch should fail")
