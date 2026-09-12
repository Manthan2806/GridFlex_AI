import unittest

from ai_ml.EV_model.load_ev_training_data import EVSplit, EVTrainingData
from ai_ml.EV_model.train_ev_random_forest import (
    MODEL_PARAMETERS,
    _calculate_metrics,
    build_model,
    train_and_evaluate,
)


class TrainEVRandomForestTests(unittest.TestCase):
    def _data(self) -> EVTrainingData:
        feature_names = ("prior_event_count", "prior_delivery_ratio_mean")
        train_features = tuple(
            (float(index % 5), float(index % 10) / 10.0) for index in range(40)
        )
        train_targets = tuple(row[1] for row in train_features)
        validation_features = ((1.0, 0.2), (2.0, 0.7), (3.0, 0.5))
        return EVTrainingData(
            feature_names=feature_names,
            imputation_medians=(2.0, 0.45),
            train=EVSplit(
                resource_ids=tuple(f"train_{index}" for index in range(40)),
                features=train_features,
                targets=train_targets,
                evaluation_dispatched_kw=tuple(4.0 for _ in range(40)),
            ),
            validation=EVSplit(
                resource_ids=("val_1", "val_2", "val_3"),
                features=validation_features,
                targets=(0.2, 0.7, 0.5),
                evaluation_dispatched_kw=(4.0, 4.0, 4.0),
            ),
            test=EVSplit(
                resource_ids=("test_1",),
                features=((0.0, 0.0),),
                targets=None,
                evaluation_dispatched_kw=None,
            ),
        )

    def test_model_has_fixed_reproducible_parameters(self) -> None:
        model = build_model()
        for name, value in MODEL_PARAMETERS.items():
            self.assertEqual(model.get_params()[name], value)

    def test_metrics_include_ratio_and_kw_errors(self) -> None:
        metrics = _calculate_metrics([0.5, 1.0], [0.25, 0.75], [4.0, 8.0])
        self.assertEqual(metrics["mae_ratio"], 0.25)
        self.assertEqual(metrics["mae_kw"], 1.5)
        self.assertEqual(metrics["prediction_bound_violations"], 0)

    def test_training_report_keeps_test_sealed(self) -> None:
        _, report = train_and_evaluate(
            self._data(),
            baseline_name="rolling_history",
            baseline_metrics={"mae_ratio": 0.2, "mae_kw": 0.8},
        )
        self.assertEqual(report["split_usage"]["test"]["status"], "sealed")
        self.assertFalse(report["split_usage"]["test"]["targets_read"])
        self.assertNotIn("test_metrics", report)

    def test_training_is_deterministic(self) -> None:
        _, first = train_and_evaluate(
            self._data(),
            baseline_name="rolling_history",
            baseline_metrics={"mae_ratio": 0.2, "mae_kw": 0.8},
        )
        _, second = train_and_evaluate(
            self._data(),
            baseline_name="rolling_history",
            baseline_metrics={"mae_ratio": 0.2, "mae_kw": 0.8},
        )
        self.assertEqual(first, second)

    def test_unsealed_test_data_is_rejected(self) -> None:
        data = self._data()
        unsafe = EVTrainingData(
            feature_names=data.feature_names,
            imputation_medians=data.imputation_medians,
            train=data.train,
            validation=data.validation,
            test=EVSplit(
                resource_ids=data.test.resource_ids,
                features=data.test.features,
                targets=(0.5,),
                evaluation_dispatched_kw=(4.0,),
            ),
        )
        with self.assertRaisesRegex(ValueError, "test outcomes must remain sealed"):
            train_and_evaluate(
                unsafe,
                baseline_name="rolling_history",
                baseline_metrics={"mae_ratio": 0.2, "mae_kw": 0.8},
            )


if __name__ == "__main__":
    unittest.main()
