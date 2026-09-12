import unittest

from ai_ml.EV_model.load_ev_training_data import EVSplit, EVTrainingData
from ai_ml.EV_model.tune_ev_random_forest import (
    CANDIDATES,
    select_candidate,
    tune_models,
)


class TuneEVRandomForestTests(unittest.TestCase):
    def _data(self) -> EVTrainingData:
        train_features = tuple(
            (float(index % 7), float(index % 11) / 10.0) for index in range(70)
        )
        train_targets = tuple(
            min(1.0, 0.08 * row[0] + 0.45 * row[1]) for row in train_features
        )
        validation_features = (
            (0.0, 0.1),
            (1.0, 0.3),
            (2.0, 0.5),
            (3.0, 0.7),
        )
        validation_targets = tuple(
            min(1.0, 0.08 * row[0] + 0.45 * row[1])
            for row in validation_features
        )
        return EVTrainingData(
            feature_names=("prior_event_count", "signal"),
            imputation_medians=(3.0, 0.5),
            train=EVSplit(
                resource_ids=tuple(f"t{index}" for index in range(70)),
                features=train_features,
                targets=train_targets,
                evaluation_dispatched_kw=tuple(4.0 for _ in range(70)),
            ),
            validation=EVSplit(
                resource_ids=("v1", "v2", "v3", "v4"),
                features=validation_features,
                targets=validation_targets,
                evaluation_dispatched_kw=(2.0, 3.0, 4.0, 5.0),
            ),
            test=EVSplit(
                resource_ids=("x1",),
                features=((0.0, 0.0),),
                targets=None,
                evaluation_dispatched_kw=None,
            ),
        )

    def test_search_is_small_and_contains_control(self) -> None:
        names = [candidate["name"] for candidate in CANDIDATES]
        self.assertEqual(len(CANDIDATES), 8)
        self.assertEqual(len(set(names)), 8)
        self.assertIn("control", names)

    def test_selection_uses_ratio_then_kw_then_name(self) -> None:
        results = [
            {"name": "b", "validation_metrics": {"mae_ratio": 0.2, "mae_kw": 0.5}},
            {"name": "a", "validation_metrics": {"mae_ratio": 0.2, "mae_kw": 0.5}},
            {"name": "c", "validation_metrics": {"mae_ratio": 0.2, "mae_kw": 0.4}},
            {"name": "d", "validation_metrics": {"mae_ratio": 0.1, "mae_kw": 0.9}},
        ]
        self.assertEqual(select_candidate(results)["name"], "d")
        self.assertEqual(select_candidate(results[:3])["name"], "c")
        self.assertEqual(select_candidate(results[:2])["name"], "a")

    def test_small_tuning_run_keeps_test_sealed(self) -> None:
        candidates = (
            {
                "name": "control",
                "n_estimators": 5,
                "max_depth": 3,
                "min_samples_leaf": 1,
                "max_features": "sqrt",
                "random_state": 2806,
                "n_jobs": 1,
            },
            {
                "name": "alternative",
                "n_estimators": 5,
                "max_depth": 2,
                "min_samples_leaf": 2,
                "max_features": 1.0,
                "random_state": 2806,
                "n_jobs": 1,
            },
        )
        _, report = tune_models(
            self._data(),
            baseline_name="rolling_history",
            baseline_metrics={"mae_ratio": 0.2, "mae_kw": 0.8},
            candidates=candidates,
        )
        self.assertEqual(report["candidate_count"], 2)
        self.assertFalse(report["split_usage"]["test"]["targets_read"])
        self.assertNotIn("test_metrics", report)

    def test_unsealed_test_data_is_rejected(self) -> None:
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
                evaluation_dispatched_kw=(4.0,),
            ),
        )
        with self.assertRaisesRegex(ValueError, "test outcomes must remain sealed"):
            tune_models(
                unsafe,
                baseline_name="rolling_history",
                baseline_metrics={"mae_ratio": 0.2, "mae_kw": 0.8},
                candidates=(CANDIDATES[0],),
            )


if __name__ == "__main__":
    unittest.main()
