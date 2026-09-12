import csv
import tempfile
import unittest
from pathlib import Path

from ai_ml.EV_model.prepare_ev_training_data import (
    MODEL_FEATURE_COLUMNS,
    TARGET_COLUMNS,
    TrainingDataError,
    build_training_rows,
    prepare_ev_training_data,
)


RESOURCE_COLUMNS = (
    "id",
    "rated_power_kw",
    "earliest_start",
    "latest_end",
    "required_kwh",
    "maximum_kwh",
    "max_power",
    "battery_capacity_kwh",
    "arrival_soc_pct",
    "target_soc_pct",
    "dataset_split",
)

HISTORY_COLUMNS = (
    "resource_id",
    "timestamp",
    "dispatched_kw",
    "delivered_kw",
    "is_available",
    "has_override",
    "dataset_split",
)


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _resource(resource_id: str = "ev_test", split: str = "train") -> dict[str, object]:
    return {
        "id": resource_id,
        "rated_power_kw": 7.2,
        "earliest_start": "2026-01-15T08:00:00+05:30",
        "latest_end": "2026-01-15T10:00:00+05:30",
        "required_kwh": 7.2,
        "maximum_kwh": 14.4,
        "max_power": 7.2,
        "battery_capacity_kwh": 60.0,
        "arrival_soc_pct": 30.0,
        "target_soc_pct": 42.0,
        "dataset_split": split,
    }


def _event(
    timestamp: str,
    delivered_kw: float,
    *,
    resource_id: str = "ev_test",
    split: str = "train",
    is_available: bool = True,
    has_override: bool = False,
    dispatched_kw: float = 4.0,
) -> dict[str, object]:
    return {
        "resource_id": resource_id,
        "timestamp": timestamp,
        "dispatched_kw": dispatched_kw,
        "delivered_kw": delivered_kw,
        "is_available": str(is_available).lower(),
        "has_override": str(has_override).lower(),
        "dataset_split": split,
    }


class PrepareEvTrainingDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary_directory.name)

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def test_prior_features_use_only_earlier_events(self) -> None:
        resources = self.root / "resources.csv"
        history = self.root / "history.csv"
        _write_csv(resources, RESOURCE_COLUMNS, [_resource()])
        _write_csv(
            history,
            HISTORY_COLUMNS,
            [
                _event("2026-01-03T08:00:00+05:30", 0.0, is_available=False),
                _event("2026-01-01T08:00:00+05:30", 2.0),
                _event("2026-01-02T08:00:00+05:30", 4.0),
            ],
        )

        rows = build_training_rows(resources, history)

        self.assertEqual([row["prior_event_count"] for row in rows], [0, 1, 2])
        self.assertEqual(rows[0]["prior_delivery_ratio_mean"], "")
        self.assertEqual(rows[1]["prior_delivery_ratio_mean"], 0.5)
        self.assertEqual(rows[2]["prior_delivery_ratio_mean"], 0.75)
        self.assertEqual(rows[2]["prior_availability_rate"], 1.0)
        self.assertEqual(rows[2]["target_delivery_ratio"], 0.0)

    def test_adding_future_outcome_does_not_change_earlier_features(self) -> None:
        resources = self.root / "resources.csv"
        history = self.root / "history.csv"
        _write_csv(resources, RESOURCE_COLUMNS, [_resource()])
        first_two = [
            _event("2026-01-01T08:00:00+05:30", 2.0),
            _event("2026-01-02T08:00:00+05:30", 3.0),
        ]
        _write_csv(history, HISTORY_COLUMNS, first_two)
        before = build_training_rows(resources, history)

        _write_csv(
            history,
            HISTORY_COLUMNS,
            [*first_two, _event("2026-01-03T08:00:00+05:30", 0.0, has_override=True)],
        )
        after = build_training_rows(resources, history)

        self.assertEqual(after[:2], before)

    def test_model_feature_allow_list_excludes_current_outcomes(self) -> None:
        forbidden = {
            "resource_id",
            "dataset_split",
            "target_dispatched_kw",
            "target_delivered_kw",
            "target_delivery_ratio",
            "target_is_available",
            "target_has_override",
            "override_rate",
            "availability_rate",
        }
        self.assertTrue(forbidden.isdisjoint(MODEL_FEATURE_COLUMNS))
        self.assertTrue(set(TARGET_COLUMNS).issubset(forbidden))

    def test_split_mismatch_is_rejected(self) -> None:
        resources = self.root / "resources.csv"
        history = self.root / "history.csv"
        _write_csv(resources, RESOURCE_COLUMNS, [_resource(split="test")])
        _write_csv(
            history,
            HISTORY_COLUMNS,
            [_event("2026-01-01T08:00:00+05:30", 2.0, split="train")],
        )

        with self.assertRaisesRegex(TrainingDataError, "does not match resource split"):
            build_training_rows(resources, history)

    def test_writer_is_deterministic_and_keeps_all_rows(self) -> None:
        resources = self.root / "resources.csv"
        history = self.root / "history.csv"
        first_output = self.root / "first.csv"
        second_output = self.root / "second.csv"
        _write_csv(resources, RESOURCE_COLUMNS, [_resource()])
        _write_csv(
            history,
            HISTORY_COLUMNS,
            [
                _event("2026-01-02T08:00:00+05:30", 3.0),
                _event("2026-01-01T08:00:00+05:30", 2.0),
            ],
        )

        self.assertEqual(prepare_ev_training_data(resources, history, first_output), 2)
        self.assertEqual(prepare_ev_training_data(resources, history, second_output), 2)
        self.assertEqual(first_output.read_bytes(), second_output.read_bytes())


if __name__ == "__main__":
    unittest.main()
