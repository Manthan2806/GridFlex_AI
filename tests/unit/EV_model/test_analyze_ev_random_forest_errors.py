import unittest

from ai_ml.EV_model.analyze_ev_random_forest_errors import analyze_predictions
from ai_ml.EV_model.load_ev_training_data import EVSplit, EVTrainingData


class AnalyzeEVRandomForestErrorsTests(unittest.TestCase):
    def _data(self) -> EVTrainingData:
        feature_names = ("prior_event_count", "signal")
        return EVTrainingData(
            feature_names=feature_names,
            imputation_medians=(1.0, 0.5),
            train=EVSplit(
                resource_ids=("t1", "t2", "t3", "t4", "t5", "t6"),
                features=((0.0, 0.1),) * 6,
                targets=(0.1,) * 6,
                evaluation_dispatched_kw=(1.0, 2.0, 3.0, 4.0, 5.0, 6.0),
            ),
            validation=EVSplit(
                resource_ids=("v1", "v2", "v3", "v4", "v5", "v6"),
                features=(
                    (0.0, 0.1),
                    (0.0, 0.2),
                    (1.0, 0.3),
                    (2.0, 0.4),
                    (3.0, 0.5),
                    (4.0, 0.6),
                ),
                targets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6),
                evaluation_dispatched_kw=(1.0, 2.0, 3.0, 4.0, 5.0, 6.0),
            ),
            test=EVSplit(
                resource_ids=("x1",),
                features=((0.0, 0.0),),
                targets=None,
                evaluation_dispatched_kw=None,
            ),
        )

    def _baseline(self) -> dict:
        metrics = {
            "cold_start": {"mae_ratio": 0.2, "mae_kw": 0.5},
            "with_history": {"mae_ratio": 0.2, "mae_kw": 0.5},
        }
        return {
            "validation_comparison": {"selected_baseline": "rolling_history"},
            "baselines": {
                "rolling_history": {"validation": metrics}
            },
        }

    def test_segments_cover_every_validation_row(self) -> None:
        report = analyze_predictions(
            self._data(), [0.15, 0.25, 0.35, 0.45, 0.55, 0.65], self._baseline()
        )
        history_total = sum(
            group["row_count"] for group in report["history_segments"].values()
        )
        dispatch_total = sum(
            group["row_count"] for group in report["dispatch_segments"].values()
        )
        self.assertEqual(history_total, 6)
        self.assertEqual(dispatch_total, 6)

    def test_dispatch_boundaries_come_from_training_rows(self) -> None:
        report = analyze_predictions(
            self._data(), [0.15, 0.25, 0.35, 0.45, 0.55, 0.65], self._baseline()
        )
        thresholds = report["dispatch_thresholds"]
        self.assertEqual(thresholds["source_split"], "train")
        self.assertAlmostEqual(thresholds["small_max_kw"], 2.666667)
        self.assertAlmostEqual(thresholds["medium_max_kw"], 4.333333)

    def test_test_holdout_remains_sealed(self) -> None:
        report = analyze_predictions(
            self._data(), [0.15, 0.25, 0.35, 0.45, 0.55, 0.65], self._baseline()
        )
        self.assertFalse(report["test_holdout"]["targets_read"])
        self.assertNotIn("test_metrics", report)

    def test_prediction_direction_counts_all_rows(self) -> None:
        report = analyze_predictions(
            self._data(), [0.0, 0.2, 0.4, 0.4, 0.6, 0.5], self._baseline()
        )
        direction = report["prediction_direction"]
        self.assertEqual(sum(direction.values()), 6)
        self.assertEqual(direction["underpredicted_rows"], 2)
        self.assertEqual(direction["overpredicted_rows"], 2)
        self.assertEqual(direction["equal_rows"], 2)

    def test_unsealed_test_outcomes_are_rejected(self) -> None:
        data = self._data()
        unsafe = EVTrainingData(
            feature_names=data.feature_names,
            imputation_medians=data.imputation_medians,
            train=data.train,
            validation=data.validation,
            test=EVSplit(
                resource_ids=("x1",),
                features=((0.0, 0.0),),
                targets=(0.5,),
                evaluation_dispatched_kw=(1.0,),
            ),
        )
        with self.assertRaisesRegex(ValueError, "test outcomes must remain sealed"):
            analyze_predictions(
                unsafe, [0.15, 0.25, 0.35, 0.45, 0.55, 0.65], self._baseline()
            )


if __name__ == "__main__":
    unittest.main()
