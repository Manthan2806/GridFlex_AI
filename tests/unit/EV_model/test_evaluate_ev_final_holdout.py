import unittest

import numpy as np

from ai_ml.EV_model.evaluate_ev_final_holdout import evaluate_predictions


class EvaluateEVFinalHoldoutTests(unittest.TestCase):
    def _config(self) -> dict:
        return {
            "safety_policy": {
                "coverage_target": 0.85,
                "maximum_allowed_overprediction_rate_percent": 15.0,
                "minimum_required_retention_percent": 50.0,
                "dispatch_group_thresholds_kw": {"small_max": 3.0, "medium_max": 6.0},
            }
        }

    def test_accepts_candidate_that_passes_every_locked_rule(self) -> None:
        actual = np.array([0.7] * 21)
        dispatch = np.array([2.0] * 7 + [5.0] * 7 + [8.0] * 7)
        expected = np.array([0.72] * 21)
        trusted = np.array([0.65] * 21)
        baseline = np.array([0.8] * 21)
        result = evaluate_predictions(actual, dispatch, expected, trusted, baseline, self._config())
        self.assertTrue(result["accepted"])
        self.assertTrue(all(result["acceptance_checks"].values()))

    def test_rejects_candidate_that_keeps_too_little_power(self) -> None:
        actual = np.array([0.7] * 21)
        dispatch = np.array([2.0] * 7 + [5.0] * 7 + [8.0] * 7)
        result = evaluate_predictions(
            actual,
            dispatch,
            np.array([0.72] * 21),
            np.array([0.20] * 21),
            np.array([0.8] * 21),
            self._config(),
        )
        self.assertFalse(result["accepted"])
        self.assertFalse(result["acceptance_checks"]["trusted_kw_retention_passes_floor"])

    def test_rejects_misaligned_arrays(self) -> None:
        with self.assertRaisesRegex(ValueError, "aligned"):
            evaluate_predictions(
                np.array([0.5]), np.array([2.0]), np.array([0.5]), np.array([]), np.array([0.5]), self._config()
            )


if __name__ == "__main__":
    unittest.main()
