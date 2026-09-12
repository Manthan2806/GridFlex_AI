"""Evaluate the locked water-heater candidate once and save its demo bundle."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

from ai_ml.water_heater_model.calibrate_water_heater_safety import _groups
from ai_ml.water_heater_model.prepare_water_heater_training_data import MODEL_FEATURE_COLUMNS
from ai_ml.water_heater_model.train_water_heater_candidate import _canonical_sha256


DEFAULT_INPUT = Path("data/processed/water_heater_training/water_heater_training_examples.csv")
DEFAULT_CONFIG = Path("data/processed/water_heater_training/water_heater_candidate_v1_config.json")
DEFAULT_REPORT = Path("data/processed/water_heater_training/water_heater_candidate_v1_final_evaluation.json")
DEFAULT_ARTIFACT = Path("ai_ml/water_heater_model/artifacts/water_heater_candidate_v1_demo_bundle.joblib")


def _load_rows(path: Path, config: dict) -> dict:
    names = tuple(config["feature_contract"]["names_in_order"])
    if names != MODEL_FEATURE_COLUMNS:
        raise ValueError("locked feature contract differs from the current contract")
    medians = config["feature_contract"]["imputation_medians"]
    result = {split: {"x": [], "y": [], "potential": [], "groups": [], "ids": []} for split in ("train", "test")}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"resource_id", "dataset_split", "target_response_ratio", "potential_kw", "prior_event_count", "heater_type_heat_pump", "flex_direction_reduce", *names}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"training table is missing columns: {sorted(missing)}")
        for number, row in enumerate(reader, start=2):
            split = row["dataset_split"]
            if split not in result:
                continue
            vector = []
            for name in names:
                raw = row[name].strip()
                vector.append(float(medians[name]) if raw == "" else float(raw))
            target = float(row["target_response_ratio"])
            potential = float(row["potential_kw"])
            if not 0 <= target <= 1 or potential <= 0:
                raise ValueError(f"row {number} violates target or power bounds")
            result[split]["x"].append(vector)
            result[split]["y"].append(target)
            result[split]["potential"].append(potential)
            result[split]["groups"].append((int(row["prior_event_count"]), int(row["heater_type_heat_pump"]), int(row["flex_direction_reduce"])))
            result[split]["ids"].append(row["resource_id"])
    if not result["train"]["x"] or not result["test"]["x"]:
        raise ValueError("non-empty train and test splits are required")
    return result


def _metrics(actual: np.ndarray, predicted: np.ndarray, potential: np.ndarray) -> dict:
    error = predicted - actual
    power_error = error * potential
    return {
        "row_count": int(len(actual)),
        "mae_ratio": round(float(np.mean(np.abs(error))), 6),
        "rmse_ratio": round(float(np.sqrt(np.mean(error ** 2))), 6),
        "bias_ratio": round(float(np.mean(error)), 6),
        "mae_kw": round(float(np.mean(np.abs(power_error))), 6),
        "rmse_kw": round(float(np.sqrt(np.mean(power_error ** 2))), 6),
        "bias_kw": round(float(np.mean(power_error)), 6),
        "overprediction_rate_percent": round(100 * float(np.mean(predicted > actual + 1e-12)), 6),
    }


def run_final_evaluation(
    input_path: Path = DEFAULT_INPUT,
    config_path: Path = DEFAULT_CONFIG,
    report_path: Path = DEFAULT_REPORT,
    artifact_path: Path = DEFAULT_ARTIFACT,
    *,
    refuse_repeat: bool = True,
) -> dict:
    if refuse_repeat and report_path.exists():
        raise FileExistsError("final evaluation already exists; refusing to consume the holdout twice")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("status") != "locked_for_final_holdout":
        raise ValueError("candidate is not locked for final evaluation")
    if config["evidence"]["training_table_canonical_sha256"] != _canonical_sha256(input_path):
        raise ValueError("training table changed after locking")
    data = _load_rows(input_path, config)
    train = data["train"]
    test = data["test"]
    train_x, train_y = np.asarray(train["x"]), np.asarray(train["y"])
    test_x = np.asarray(test["x"])
    actual, potential = np.asarray(test["y"]), np.asarray(test["potential"])

    expected_model = HistGradientBoostingRegressor(**config["expected_model"]["parameters"]).fit(train_x, train_y)
    lower_model = HistGradientBoostingRegressor(**config["safety_policy"]["lower_model_parameters"]).fit(train_x, train_y)
    expected = np.clip(expected_model.predict(test_x), 0.0, 1.0)
    trusted = np.minimum(expected, np.clip(lower_model.predict(test_x), 0.0, 1.0))

    # Rebuild the selected heater-type/direction baseline using training only.
    baseline_values: dict[tuple[int, int], list[float]] = defaultdict(list)
    for target, group in zip(train_y, train["groups"]):
        baseline_values[(group[1], group[2])].append(float(target))
    baseline_means = {key: float(np.mean(values)) for key, values in baseline_values.items()}
    baseline = np.asarray([baseline_means[(group[1], group[2])] for group in test["groups"]])

    maximum = float(config["safety_policy"]["maximum_allowed_overprediction_rate_percent"])
    thresholds = config["safety_policy"]["potential_group_thresholds_kw"]
    group_results = {}
    for name, mask in _groups(potential, test["groups"], thresholds).items():
        if not np.any(mask):
            raise ValueError(f"final test group {name} is empty")
        rate = 100 * float(np.mean(trusted[mask] > actual[mask] + 1e-12))
        group_results[name] = {"row_count": int(np.sum(mask)), "overprediction_rate_percent": round(rate, 6), "maximum_allowed_percent": maximum, "passes": rate <= maximum}

    baseline_metrics = _metrics(actual, baseline, potential)
    expected_metrics = _metrics(actual, expected, potential)
    trusted_metrics = _metrics(actual, trusted, potential)
    retention = 100 * float(np.sum(trusted * potential) / np.sum(expected * potential))
    checks = {
        "expected_mae_ratio_beats_baseline": expected_metrics["mae_ratio"] < baseline_metrics["mae_ratio"],
        "expected_mae_kw_beats_baseline": expected_metrics["mae_kw"] < baseline_metrics["mae_kw"],
        "all_predeclared_safety_groups_pass": all(item["passes"] for item in group_results.values()),
        "trusted_never_exceeds_expected": bool(np.all(trusted <= expected + 1e-12)),
        "predictions_are_bounded": bool(np.all((expected >= 0) & (expected <= 1)) and np.all((trusted >= 0) & (trusted <= 1))),
        "trusted_power_is_nonzero": bool(np.sum(trusted * potential) > 0),
    }
    accepted = all(checks.values())
    report = {
        "candidate_version": config["candidate_version"],
        "evaluation_status": "final_resource_disjoint_test_evaluated_once",
        "decision": "accepted_for_hackathon_prototype" if accepted else "rejected",
        "deployment_allowed": False,
        "prototype_allowed": accepted,
        "holdout": {"rows": len(actual), "resources": len(set(test["ids"])), "training_resource_overlap": len(set(train["ids"]) & set(test["ids"])), "training_table_canonical_sha256": _canonical_sha256(input_path)},
        "baseline_metrics": baseline_metrics,
        "expected_metrics": expected_metrics,
        "trusted_metrics": trusted_metrics,
        "safety": {"groups": group_results, "trusted_kw_retained_percent": round(retention, 6), "retention_is_acceptance_gate": False},
        "acceptance_checks": checks,
        "limitations": [
            "Every response outcome is synthetic; these metrics are not field evidence.",
            "The split is resource-disjoint but produced by the same synthetic generator.",
            "The trusted estimate is intentionally very conservative.",
            "Acceptance permits a hackathon/MVP prototype only, not real autonomous dispatch.",
        ],
    }
    if accepted:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"candidate_version": config["candidate_version"], "expected_model": expected_model, "lower_bound_model": lower_model, "config": config}, artifact_path)
        report["model_artifact"] = {"saved": True, "path": artifact_path.as_posix(), "sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest()}
    else:
        report["model_artifact"] = {"saved": False}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    args = parser.parse_args()
    report = run_final_evaluation(args.input, args.config, args.report, args.artifact)
    print(f"Water-heater final decision: {report['decision']}")
    print(f"Final test rows: {report['holdout']['rows']}")
    print(f"Expected ratio MAE: {report['expected_metrics']['mae_ratio']:.6f}")
    print(f"Expected power MAE: {report['expected_metrics']['mae_kw']:.6f} kW")
    print(f"Trusted overprediction: {report['trusted_metrics']['overprediction_rate_percent']:.2f}%")
    print(f"Trusted kW retained: {report['safety']['trusted_kw_retained_percent']:.2f}%")


if __name__ == "__main__":
    main()
