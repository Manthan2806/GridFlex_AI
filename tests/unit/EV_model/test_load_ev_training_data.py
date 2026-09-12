import csv
import tempfile
import unittest
from pathlib import Path

from ai_ml.EV_model.load_ev_training_data import (
    EVALUATION_DISPATCH_COLUMN,
    EVDataLoadingError,
    IMPUTABLE_FEATURE_COLUMNS,
    TARGET_COLUMN,
    load_ev_training_data,
)
from ai_ml.EV_model.prepare_ev_training_data import MODEL_FEATURE_COLUMNS


class LoadEVTrainingDataTests(unittest.TestCase):
    def _row(self, split: str, value: str, *, target: str = "0.5") -> dict[str, str]:
        row = {column: value for column in MODEL_FEATURE_COLUMNS}
        row.update(
            {
                "resource_id": f"{split}_ev",
                "dataset_split": split,
                TARGET_COLUMN: target,
                EVALUATION_DISPATCH_COLUMN: "4.0",
            }
        )
        return row

    def _write(self, rows: list[dict[str, str]]) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "training.csv"
        columns = [
            "resource_id",
            "dataset_split",
            *MODEL_FEATURE_COLUMNS,
            EVALUATION_DISPATCH_COLUMN,
            TARGET_COLUMN,
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_loads_expected_splits_and_feature_allow_list(self) -> None:
        path = self._write(
            [self._row("train", "1"), self._row("validation", "2"), self._row("test", "3", target="sealed")]
        )
        data = load_ev_training_data(path)

        self.assertEqual(data.feature_names, tuple(MODEL_FEATURE_COLUMNS))
        self.assertEqual((data.train.row_count, data.validation.row_count, data.test.row_count), (1, 1, 1))
        self.assertNotIn(TARGET_COLUMN, data.feature_names)
        self.assertNotIn(EVALUATION_DISPATCH_COLUMN, data.feature_names)

    def test_test_answers_are_not_parsed_or_exposed(self) -> None:
        test_row = self._row("test", "3", target="sealed")
        test_row[EVALUATION_DISPATCH_COLUMN] = "sealed"
        path = self._write(
            [self._row("train", "1"), self._row("validation", "2"), test_row]
        )

        data = load_ev_training_data(path)

        self.assertIsNone(data.test.targets)
        self.assertIsNone(data.test.evaluation_dispatched_kw)

    def test_missing_values_use_training_median_only(self) -> None:
        low = self._row("train", "1")
        high = self._row("train", "5")
        validation = self._row("validation", "99")
        test = self._row("test", "99", target="sealed")
        for column in IMPUTABLE_FEATURE_COLUMNS:
            validation[column] = ""
            test[column] = ""
        path = self._write([low, high, validation, test])

        data = load_ev_training_data(path)

        self.assertTrue(all(value == 3.0 for value in data.imputation_medians))
        for index, column in enumerate(MODEL_FEATURE_COLUMNS):
            expected = 3.0 if column in IMPUTABLE_FEATURE_COLUMNS else 99.0
            self.assertEqual(data.validation.features[0][index], expected)
            self.assertEqual(data.test.features[0][index], expected)

    def test_rejects_missing_required_non_history_feature(self) -> None:
        bad = self._row("train", "1")
        bad["rated_power_kw"] = ""
        path = self._write(
            [bad, self._row("validation", "2"), self._row("test", "3", target="sealed")]
        )

        with self.assertRaisesRegex(EVDataLoadingError, "required feature"):
            load_ev_training_data(path)

    def test_rejects_invalid_training_target(self) -> None:
        path = self._write(
            [self._row("train", "1", target="1.2"), self._row("validation", "2"), self._row("test", "3", target="sealed")]
        )

        with self.assertRaisesRegex(EVDataLoadingError, "between 0 and 1"):
            load_ev_training_data(path)

    def test_rejects_non_numeric_feature(self) -> None:
        bad = self._row("train", "1")
        bad[MODEL_FEATURE_COLUMNS[0]] = "not-a-number"
        path = self._write(
            [bad, self._row("validation", "2"), self._row("test", "3", target="sealed")]
        )

        with self.assertRaisesRegex(EVDataLoadingError, "must be numeric"):
            load_ev_training_data(path)


if __name__ == "__main__":
    unittest.main()
