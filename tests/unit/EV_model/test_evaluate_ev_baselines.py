import csv
import tempfile
import unittest
from pathlib import Path

from ai_ml.EV_model.evaluate_ev_baselines import (
    BaselineEvaluationError,
    EvaluationRow,
    calculate_metrics,
    evaluate_baselines,
    write_evaluation_report,
)


COLUMNS = (
    "resource_id",
    "dataset_split",
    "prior_event_count",
    "prior_delivery_ratio_mean",
    "target_dispatched_kw",
    "target_delivered_kw",
    "target_delivery_ratio",
)


def _row(
    resource_id: str,
    split: str,
    ratio: float,
    *,
    prior_count: int = 0,
    prior_mean: float | str = "",
    dispatched_kw: float = 10.0,
) -> dict[str, object]:
    return {
        "resource_id": resource_id,
        "dataset_split": split,
        "prior_event_count": prior_count,
        "prior_delivery_ratio_mean": prior_mean,
        "target_dispatched_kw": dispatched_kw,
        "target_delivered_kw": dispatched_kw * ratio,
        "target_delivery_ratio": ratio,
    }


class EvaluateEvBaselinesTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary_directory.name)

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def _write_rows(self, rows: list[dict[str, object]]) -> Path:
        path = self.root / "training.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_global_average_uses_training_rows_only(self) -> None:
        path = self._write_rows(
            [
                _row("train_1", "train", 0.2),
                _row("train_2", "train", 0.8),
                _row("validation_1", "validation", 1.0),
                _row("test_1", "test", 0.0),
            ]
        )

        report = evaluate_baselines(path)

        self.assertEqual(report["global_train_mean_ratio"], 0.5)

    def test_rolling_history_uses_global_mean_only_for_cold_start(self) -> None:
        path = self._write_rows(
            [
                _row("train_1", "train", 0.4),
                _row("validation_1", "validation", 0.4),
                _row(
                    "validation_1",
                    "validation",
                    0.8,
                    prior_count=1,
                    prior_mean=0.4,
                ),
                _row("test_1", "test", 0.3),
            ]
        )

        report = evaluate_baselines(path)
        rolling = report["baselines"]["rolling_history"]["validation"]

        self.assertEqual(rolling["cold_start"]["mae_ratio"], 0.0)
        self.assertEqual(rolling["with_history"]["mae_ratio"], 0.4)

    def test_metrics_report_ratio_and_kw_error(self) -> None:
        rows = [
            EvaluationRow("ev_1", "validation", 0, None, 10.0, 5.0, 0.5),
            EvaluationRow("ev_2", "validation", 0, None, 4.0, 4.0, 1.0),
        ]

        metrics = calculate_metrics(rows, [0.5, 0.5])

        self.assertEqual(metrics["mae_ratio"], 0.25)
        self.assertEqual(metrics["mae_kw"], 1.0)
        self.assertEqual(metrics["bias_kw"], -1.0)
        self.assertEqual(metrics["prediction_bound_violations"], 0)

    def test_test_holdout_has_no_metrics(self) -> None:
        path = self._write_rows(
            [
                _row("train_1", "train", 0.5),
                _row("validation_1", "validation", 0.5),
                _row("test_1", "test", 1.0),
            ]
        )

        report = evaluate_baselines(path)

        self.assertEqual(report["test_holdout"]["status"], "sealed")
        self.assertFalse(report["test_holdout"]["target_columns_read"])
        self.assertNotIn("metrics", report["test_holdout"])
        self.assertNotIn("test", report["baselines"]["global_train_mean"])
        self.assertNotIn("test", report["baselines"]["rolling_history"])

    def test_test_target_values_are_not_parsed(self) -> None:
        rows = [
            _row("train_1", "train", 0.5),
            _row("validation_1", "validation", 0.5),
            _row("test_1", "test", 0.5),
        ]
        rows[-1]["target_dispatched_kw"] = "sealed"
        rows[-1]["target_delivered_kw"] = "sealed"
        rows[-1]["target_delivery_ratio"] = "sealed"
        path = self._write_rows(rows)

        report = evaluate_baselines(path)

        self.assertEqual(report["test_holdout"]["status"], "sealed")

    def test_out_of_bounds_target_is_rejected(self) -> None:
        path = self._write_rows(
            [
                _row("train_1", "train", 0.5),
                _row("validation_1", "validation", 1.2),
                _row("test_1", "test", 0.5),
            ]
        )

        with self.assertRaisesRegex(BaselineEvaluationError, "between 0 and 1"):
            evaluate_baselines(path)

    def test_written_report_is_deterministic(self) -> None:
        path = self._write_rows(
            [
                _row("train_1", "train", 0.5),
                _row("validation_1", "validation", 0.7),
                _row("test_1", "test", 0.2),
            ]
        )
        report = evaluate_baselines(path)
        first = self.root / "first.json"
        second = self.root / "second.json"

        write_evaluation_report(report, first)
        write_evaluation_report(report, second)

        self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
