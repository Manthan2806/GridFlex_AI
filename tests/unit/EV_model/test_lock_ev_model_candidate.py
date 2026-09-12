import unittest

from ai_ml.EV_model.load_ev_training_data import EVSplit, EVTrainingData
from ai_ml.EV_model.lock_ev_model_candidate import build_candidate_config


class LockEVModelCandidateTests(unittest.TestCase):
    def _data(self, sealed: bool = True) -> EVTrainingData:
        return EVTrainingData(
            feature_names=("rated_power_kw", "prior_delivery_ratio_mean"),
            imputation_medians=(7.2, 0.75),
            train=EVSplit(
                resource_ids=("t1", "t2", "t3"),
                features=((1.0, 0.5),) * 3,
                targets=(0.5, 0.5, 0.5),
                evaluation_dispatched_kw=(2.0, 5.0, 8.0),
            ),
            validation=EVSplit(
                resource_ids=("v1",), features=((1.0, 0.5),), targets=(0.5,), evaluation_dispatched_kw=(4.0,)
            ),
            test=EVSplit(
                resource_ids=("x1",),
                features=((1.0, 0.5),),
                targets=None if sealed else (0.5,),
                evaluation_dispatched_kw=None if sealed else (4.0,),
            ),
        )

    def _tuning(self) -> dict:
        return {"selected": {"name": "shallower", "parameters": {"max_depth": 8, "random_state": 2806}}}

    def _tradeoff(self) -> dict:
        groups = {name: {"safety_margin_ratio": margin} for name, margin in (("small", 0.1), ("medium", 0.2), ("large", 0.3))}
        return {
            "selection_rule": {"minimum_trusted_kw_retention_percent": 50.0},
            "selected_model": self._tuning()["selected"],
            "selected": {
                "coverage_target": 0.85,
                "maximum_allowed_overprediction_rate_percent": 15.0,
                "trusted_kw_retained_percent_of_expected": 60.0,
                "dispatch_group_safety": groups,
                "risk_rule_passed": True,
            },
        }

    def test_locks_model_features_safety_and_sealed_test(self) -> None:
        config = build_candidate_config(self._data(), self._tuning(), self._tradeoff())
        self.assertEqual(config["status"], "locked_before_final_holdout_evaluation")
        self.assertEqual(config["model"]["selected_name"], "shallower")
        self.assertEqual(config["safety_policy"]["coverage_target"], 0.85)
        self.assertEqual(config["feature_contract"]["names_in_order"][0], "rated_power_kw")
        self.assertFalse(config["test_holdout"]["targets_read"])
        self.assertFalse(config["model_artifact_saved"])

    def test_rejects_unsealed_test_outcomes(self) -> None:
        with self.assertRaisesRegex(ValueError, "test outcomes must remain sealed"):
            build_candidate_config(self._data(sealed=False), self._tuning(), self._tradeoff())


if __name__ == "__main__":
    unittest.main()
