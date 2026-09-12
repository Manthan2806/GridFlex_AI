import unittest

from ai_ml.EV_model.compare_ev_safety_levels import select_safety_level


class CompareEVSafetyLevelsTests(unittest.TestCase):
    def test_selects_safest_eligible_level(self) -> None:
        results = [
            {"coverage_target": 0.80, "risk_rule_passed": True, "trusted_kw_retained_percent_of_expected": 70.0},
            {"coverage_target": 0.85, "risk_rule_passed": True, "trusted_kw_retained_percent_of_expected": 55.0},
            {"coverage_target": 0.90, "risk_rule_passed": True, "trusted_kw_retained_percent_of_expected": 40.0},
        ]
        selected = select_safety_level(results, minimum_retention_percent=50.0)
        self.assertIsNotNone(selected)
        self.assertEqual(selected["coverage_target"], 0.85)

    def test_returns_none_when_no_level_is_useful_enough(self) -> None:
        results = [{"coverage_target": 0.80, "risk_rule_passed": True, "trusted_kw_retained_percent_of_expected": 49.9}]
        self.assertIsNone(select_safety_level(results, minimum_retention_percent=50.0))

    def test_rejects_level_that_fails_risk_rule(self) -> None:
        results = [
            {"coverage_target": 0.90, "risk_rule_passed": False, "trusted_kw_retained_percent_of_expected": 90.0},
            {"coverage_target": 0.80, "risk_rule_passed": True, "trusted_kw_retained_percent_of_expected": 60.0},
        ]
        self.assertEqual(select_safety_level(results)["coverage_target"], 0.80)


if __name__ == "__main__":
    unittest.main()
