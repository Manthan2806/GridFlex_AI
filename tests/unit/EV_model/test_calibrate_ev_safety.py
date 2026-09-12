import unittest

import numpy as np

from ai_ml.EV_model.calibrate_ev_safety import (
    _dispatch_groups,
    _safety_margin,
    calibrate_predictions,
)
from ai_ml.EV_model.load_ev_training_data import EVSplit, EVTrainingData


class CalibrateEVSafetyTests(unittest.TestCase):
    def _data(self) -> EVTrainingData:
        return EVTrainingData(
            feature_names=("signal",),
            imputation_medians=(0.5,),
            train=EVSplit(
                resource_ids=tuple(f"t{i}" for i in range(9)),
                features=tuple((float(i),) for i in range(9)),
                targets=tuple(0.5 for _ in range(9)),
                evaluation_dispatched_kw=(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0),
            ),
            validation=EVSplit(
                resource_ids=tuple(f"v{i}" for i in range(9)),
                features=tuple((float(i),) for i in range(9)),
                targets=(0.2, 0.4, 0.6, 0.3, 0.5, 0.7, 0.2, 0.5, 0.8),
                evaluation_dispatched_kw=(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0),
            ),
            test=EVSplit(
                resource_ids=("x1",),
                features=((0.0,),),
                targets=None,
                evaluation_dispatched_kw=None,
            ),
        )

    def test_safety_margin_is_never_negative(self) -> None:
        margin = _safety_margin(np.array([0.8, 0.9]), np.array([0.2, 0.3]))
        self.assertEqual(margin, 0.0)

    def test_custom_coverage_changes_margin(self) -> None:
        actual = np.array([0.2, 0.4, 0.6, 0.8])
        predicted = np.array([0.5, 0.5, 0.5, 0.5])
        self.assertLessEqual(
            _safety_margin(actual, predicted, 0.5),
            _safety_margin(actual, predicted, 0.9),
        )

    def test_invalid_coverage_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "between zero and one"):
            _safety_margin(np.array([0.5]), np.array([0.5]), 1.0)

    def test_dispatch_groups_are_complete_and_disjoint(self) -> None:
        values = np.array([1.0, 3.0, 5.0, 7.0])
        groups = _dispatch_groups(values, 3.0, 5.0)
        membership = sum(mask.astype(int) for mask in groups.values())
        self.assertTrue(np.all(membership == 1))

    def test_calibration_passes_risk_limit_and_seals_test(self) -> None:
        report = calibrate_predictions(
            self._data(),
            [0.3, 0.5, 0.7, 0.4, 0.6, 0.8, 0.3, 0.6, 0.9],
            baseline_metrics={"mae_ratio": 0.2, "mae_kw": 1.5},
        )
        self.assertTrue(
            report["acceptance_checks"]["all_dispatch_groups_pass_risk_limit"]
        )
        self.assertTrue(
            report["acceptance_checks"]["trusted_predictions_never_exceed_expected"]
        )
        self.assertFalse(report["test_holdout"]["targets_read"])
        self.assertNotIn("test_metrics", report)
        self.assertTrue(report["risk_rule_passed"])
        self.assertFalse(report["provisional_acceptance"])

    def test_unsealed_test_data_is_rejected(self) -> None:
        data = self._data()
        unsafe = EVTrainingData(
            feature_names=data.feature_names,
            imputation_medians=data.imputation_medians,
            train=data.train,
            validation=data.validation,
            test=EVSplit(
                resource_ids=("x1",),
                features=((0.0,),),
                targets=(0.5,),
                evaluation_dispatched_kw=(1.0,),
            ),
        )
        with self.assertRaisesRegex(ValueError, "test outcomes must remain sealed"):
            calibrate_predictions(
                unsafe,
                [0.3, 0.5, 0.7, 0.4, 0.6, 0.8, 0.3, 0.6, 0.9],
                baseline_metrics={"mae_ratio": 0.2, "mae_kw": 1.5},
            )


if __name__ == "__main__":
    unittest.main()
