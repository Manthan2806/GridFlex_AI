import unittest

from ai_ml.EV_model.finalize_ev_experiment import (
    assert_deployment_allowed,
    build_model_card,
    build_release_status,
)


class FinalizeEVExperimentTests(unittest.TestCase):
    def _report(self) -> dict:
        metrics = {"mae_ratio": 0.15, "mae_kw": 0.73}
        groups = {
            "small": {"overprediction_rate_percent": 15.8, "maximum_allowed_percent": 15.0, "passes": False},
            "medium": {"overprediction_rate_percent": 16.0, "maximum_allowed_percent": 15.0, "passes": False},
            "large": {"overprediction_rate_percent": 12.0, "maximum_allowed_percent": 15.0, "passes": True},
        }
        return {
            "status": "final_holdout_evaluated_once",
            "decision": "rejected",
            "holdout": {
                "row_count": 3150,
                "baseline_metrics": metrics,
                "expected_metrics": metrics,
                "trusted_metrics": metrics,
                "safety": {
                    "coverage_target": 0.85,
                    "trusted_kw_retained_percent_of_expected": 58.4,
                    "overall_overprediction_rate_percent": 14.4,
                    "maximum_allowed_overprediction_rate_percent": 15.0,
                    "dispatch_groups": groups,
                },
                "acceptance_checks": {
                    "expected_mae_ratio_beats_baseline": True,
                    "all_dispatch_groups_pass_overprediction_limit": False,
                },
                "accepted": False,
            },
            "model_artifact": {"saved": False},
        }

    def _config(self) -> dict:
        return {
            "model": {"family": "RandomForestRegressor", "selected_name": "shallower"},
            "feature_contract": {"names_in_order": ["a", "b"]},
        }

    def test_rejected_result_blocks_deployment_and_holdout_reuse(self) -> None:
        status = build_release_status(self._report())
        self.assertEqual(status["release_status"], "experimental_not_deployable")
        self.assertFalse(status["deployment_allowed"])
        self.assertFalse(status["holdout"]["reuse_for_tuning_allowed"])
        self.assertIn("all_dispatch_groups_pass_overprediction_limit", status["acceptance"]["failed_checks"])

    def test_deployment_guard_raises_for_rejected_model(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "not approved"):
            assert_deployment_allowed(build_release_status(self._report()))

    def test_model_card_uses_explicit_non_deployment_language(self) -> None:
        status = build_release_status(self._report())
        card = build_model_card(self._config(), self._report(), status)
        self.assertIn("Experimental — not approved for deployment", card)
        self.assertIn("Do not reuse the consumed holdout", card)
        self.assertNotIn("production-ready", card.split("## Not allowed")[0])

    def test_inconsistent_rejection_with_saved_artifact_is_rejected(self) -> None:
        report = self._report()
        report["model_artifact"]["saved"] = True
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            build_release_status(report)


if __name__ == "__main__":
    unittest.main()
