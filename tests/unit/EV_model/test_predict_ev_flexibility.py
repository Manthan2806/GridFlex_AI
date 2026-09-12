import unittest

import numpy as np

from ai_ml.EV_model.predict_ev_flexibility import predict_flexibility


class _FixedModel:
    def __init__(self) -> None:
        self.last_matrix = None

    def predict(self, matrix):
        self.last_matrix = matrix
        return np.full(len(matrix), 0.8)


class PredictEVFlexibilityTests(unittest.TestCase):
    def _config(self) -> dict:
        return {
            "feature_contract": {
                "names_in_order": ["rated_power_kw", "prior_delivery_ratio_mean"],
                "imputation_medians": {"rated_power_kw": 7.2, "prior_delivery_ratio_mean": 0.75},
                "features_allowed_to_be_missing": ["prior_delivery_ratio_mean"],
            },
            "safety_policy": {
                "coverage_target": 0.85,
                "dispatch_group_thresholds_kw": {"small_max": 3.0, "medium_max": 6.0},
                "margin_ratio_by_dispatch_group": {"small": 0.1, "medium": 0.2, "large": 0.3},
            },
        }

    def test_returns_expected_and_trusted_power_for_each_group(self) -> None:
        model = _FixedModel()
        rows = [{"rated_power_kw": 7.2, "prior_delivery_ratio_mean": 0.7}] * 3
        results = predict_flexibility(model, self._config(), rows, [2.0, 5.0, 7.0])
        self.assertEqual([row["dispatch_group"] for row in results], ["small", "medium", "large"])
        self.assertEqual([round(row["trusted_ratio"], 2) for row in results], [0.7, 0.6, 0.5])
        self.assertAlmostEqual(results[1]["trusted_kw"], 3.0)

    def test_uses_locked_median_for_missing_history(self) -> None:
        model = _FixedModel()
        predict_flexibility(model, self._config(), [{"rated_power_kw": 7.2}], [2.0])
        self.assertAlmostEqual(float(model.last_matrix[0, 1]), 0.75)

    def test_rejects_missing_required_feature(self) -> None:
        with self.assertRaisesRegex(ValueError, "required feature"):
            predict_flexibility(_FixedModel(), self._config(), [{}], [2.0])

    def test_rejects_negative_dispatch(self) -> None:
        row = {"rated_power_kw": 7.2, "prior_delivery_ratio_mean": 0.7}
        with self.assertRaisesRegex(ValueError, "non-negative"):
            predict_flexibility(_FixedModel(), self._config(), [row], [-1.0])


if __name__ == "__main__":
    unittest.main()
