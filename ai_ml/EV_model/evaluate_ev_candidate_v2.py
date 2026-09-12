"""Evaluate locked EV candidate v2 once on its source-disjoint holdout."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import joblib
import numpy as np

from ai_ml.EV_model.develop_ev_candidate_v2 import build_model
from ai_ml.EV_model.evidence import canonical_sha256, file_sha256
from ai_ml.EV_model.load_ev_training_data import DEFAULT_INPUT_PATH, load_ev_training_data
from ai_ml.EV_model.prepare_ev_training_data import MODEL_FEATURE_COLUMNS
from ai_ml.EV_model.train_ev_random_forest import _calculate_metrics


V2_DIR = Path("data/processed/ev_training/v2")
DEFAULT_CONFIG_PATH = V2_DIR / "ev_candidate_v2_config.json"
DEFAULT_DEVELOPMENT_REPORT_PATH = V2_DIR / "ev_candidate_v2_development.json"
DEFAULT_HOLDOUT_PATH = V2_DIR / "ev_candidate_v2_holdout_examples.csv"
DEFAULT_REPORT_PATH = V2_DIR / "ev_candidate_v2_final_evaluation.json"
DEFAULT_MODEL_PATH = Path("ai_ml/EV_model/artifacts/ev_candidate_v2_demo_bundle.joblib")
DEFAULT_ORIGINAL_SOURCES = Path("data/synthetic/source_samples/acn_session_summaries.csv")
DEFAULT_HOLDOUT_SOURCES = Path(
    "data/synthetic/ev_v2_holdout/source_samples/acn_session_summaries.csv"
)


def _source_paths(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if "source_session_path" not in (reader.fieldnames or ()):
            raise ValueError(f"{path} is missing source_session_path")
        values = {
            row["source_session_path"].strip()
            for row in reader
            if row.get("source_session_path", "").strip()
        }
    if not values:
        raise ValueError(f"{path} contains no source sessions")
    return values


def _load_holdout(path: Path, config: dict) -> dict[str, object]:
    feature_names = tuple(config["feature_contract"]["names_in_order"])
    if feature_names != MODEL_FEATURE_COLUMNS:
        raise ValueError("locked v2 feature order does not match the current feature contract")
    medians = config["feature_contract"]["imputation_medians"]
    resource_ids: list[str] = []
    features: list[list[float]] = []
    targets: list[float] = []
    dispatch: list[float] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {
            "resource_id",
            "target_delivery_ratio",
            "target_dispatched_kw",
            *feature_names,
        }
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"holdout is missing columns: {sorted(missing)}")
        for row_number, row in enumerate(reader, start=2):
            resource_id = row["resource_id"].strip()
            if not resource_id:
                raise ValueError(f"holdout row {row_number} has a blank resource ID")
            feature_row = []
            for name in feature_names:
                raw = row[name].strip()
                value = float(medians[name]) if raw == "" else float(raw)
                if not np.isfinite(value):
                    raise ValueError(f"holdout row {row_number} has non-finite {name}")
                feature_row.append(value)
            target = float(row["target_delivery_ratio"])
            dispatched_kw = float(row["target_dispatched_kw"])
            if not 0.0 <= target <= 1.0:
                raise ValueError(f"holdout row {row_number} target is outside 0..1")
            if not np.isfinite(dispatched_kw) or dispatched_kw <= 0.0:
                raise ValueError(f"holdout row {row_number} dispatch must be positive")
            resource_ids.append(resource_id)
            features.append(feature_row)
            targets.append(target)
            dispatch.append(dispatched_kw)
    if not resource_ids:
        raise ValueError("holdout contains no rows")
    return {
        "resource_ids": tuple(resource_ids),
        "features": np.asarray(features, dtype=float),
        "targets": np.asarray(targets, dtype=float),
        "dispatch": np.asarray(dispatch, dtype=float),
    }


def evaluate_predictions(
    actual: np.ndarray,
    dispatch: np.ndarray,
    baseline: np.ndarray,
    expected: np.ndarray,
    trusted: np.ndarray,
    config: dict,
) -> dict:
    """Apply the locked safety and usefulness rules to final predictions."""
    if not len(actual) or len({len(actual), len(dispatch), len(baseline), len(expected), len(trusted)}) != 1:
        raise ValueError("final evaluation arrays must be non-empty and aligned")
    policy = config["safety_policy"]
    maximum_overprediction = float(policy["maximum_allowed_overprediction_rate_percent"])
    minimum_retention = float(policy["minimum_retention_percent"])
    thresholds = policy["dispatch_group_thresholds_kw"]
    masks = {
        "small": dispatch <= float(thresholds["small_max"]),
        "medium": (dispatch > float(thresholds["small_max"]))
        & (dispatch <= float(thresholds["medium_max"])),
        "large": dispatch > float(thresholds["medium_max"]),
    }
    groups = {}
    for name, mask in masks.items():
        if not np.any(mask):
            raise ValueError(f"final holdout dispatch group {name} is empty")
        rate = 100.0 * float(np.mean(trusted[mask] > actual[mask] + 1e-12))
        groups[name] = {
            "row_count": int(np.sum(mask)),
            "overprediction_rate_percent": round(rate, 6),
            "maximum_allowed_percent": maximum_overprediction,
            "passes": rate <= maximum_overprediction + 1e-9,
        }
    overall_rate = 100.0 * float(np.mean(trusted > actual + 1e-12))
    mean_expected_kw = float(np.mean(expected * dispatch))
    mean_trusted_kw = float(np.mean(trusted * dispatch))
    retained = 100.0 * mean_trusted_kw / mean_expected_kw if mean_expected_kw else 0.0
    baseline_metrics = _calculate_metrics(actual, baseline, dispatch)
    expected_metrics = _calculate_metrics(actual, expected, dispatch)
    trusted_metrics = _calculate_metrics(actual, trusted, dispatch)
    checks = {
        "expected_mae_ratio_beats_baseline": (
            float(expected_metrics["mae_ratio"]) < float(baseline_metrics["mae_ratio"])
        ),
        "expected_mae_kw_beats_baseline": (
            float(expected_metrics["mae_kw"]) < float(baseline_metrics["mae_kw"])
        ),
        "all_dispatch_groups_pass_overprediction_limit": all(
            group["passes"] for group in groups.values()
        ),
        "overall_passes_overprediction_limit": (
            overall_rate <= maximum_overprediction + 1e-9
        ),
        "trusted_kw_retention_passes_floor": retained >= minimum_retention,
        "trusted_never_exceeds_expected": bool(np.all(trusted <= expected + 1e-12)),
        "predictions_are_bounded": bool(
            np.all((expected >= 0.0) & (expected <= 1.0))
            and np.all((trusted >= 0.0) & (trusted <= 1.0))
        ),
    }
    return {
        "row_count": int(len(actual)),
        "baseline_metrics": baseline_metrics,
        "expected_metrics": expected_metrics,
        "trusted_metrics": trusted_metrics,
        "safety": {
            "overall_overprediction_rate_percent": round(overall_rate, 6),
            "maximum_allowed_overprediction_rate_percent": maximum_overprediction,
            "dispatch_groups": groups,
            "mean_expected_kw": round(mean_expected_kw, 6),
            "mean_trusted_kw": round(mean_trusted_kw, 6),
            "trusted_kw_retained_percent": round(retained, 6),
            "minimum_retention_percent": minimum_retention,
        },
        "acceptance_checks": checks,
        "accepted": all(checks.values()),
    }


def run_final_evaluation(
    training_path: Path = DEFAULT_INPUT_PATH,
    holdout_path: Path = DEFAULT_HOLDOUT_PATH,
    config_path: Path = DEFAULT_CONFIG_PATH,
    development_report_path: Path = DEFAULT_DEVELOPMENT_REPORT_PATH,
    original_sources_path: Path = DEFAULT_ORIGINAL_SOURCES,
    holdout_sources_path: Path = DEFAULT_HOLDOUT_SOURCES,
    report_path: Path = DEFAULT_REPORT_PATH,
    model_path: Path = DEFAULT_MODEL_PATH,
) -> dict:
    if report_path.exists():
        raise FileExistsError("candidate v2 final report already exists; refusing to evaluate twice")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("status") != "locked_for_new_holdout":
        raise ValueError("candidate v2 is not locked for final evaluation")
    evidence = config["evidence"]
    if evidence["training_table_canonical_sha256"] != canonical_sha256(training_path):
        raise ValueError("training data changed after candidate v2 was locked")
    if evidence["development_report_canonical_sha256"] != canonical_sha256(
        development_report_path
    ):
        raise ValueError("development report changed after candidate v2 was locked")

    original_sources = _source_paths(original_sources_path)
    holdout_sources = _source_paths(holdout_sources_path)
    overlap = original_sources & holdout_sources
    if overlap:
        raise ValueError(f"new holdout reuses {len(overlap)} original ACN source sessions")

    data = load_ev_training_data(training_path)
    if data.train.targets is None:
        raise ValueError("training targets are required")
    holdout = _load_holdout(holdout_path, config)
    expected_spec = config["model"]
    lower_spec = config["safety_policy"]["lower_bound_model"]
    expected_model = build_model(expected_spec["family"], expected_spec["parameters"])
    lower_model = build_model(lower_spec["family"], lower_spec["parameters"])
    expected_model.fit(data.train.features, data.train.targets)
    lower_model.fit(data.train.features, data.train.targets)
    features = holdout["features"]
    actual = holdout["targets"]
    dispatch = holdout["dispatch"]
    expected = np.clip(expected_model.predict(features), 0.0, 1.0)
    raw_lower = np.minimum(expected, np.clip(lower_model.predict(features), 0.0, 1.0))
    thresholds = config["safety_policy"]["dispatch_group_thresholds_kw"]
    adjustments = config["safety_policy"][
        "conformal_adjustment_ratio_by_dispatch_group"
    ]
    masks = {
        "small": dispatch <= float(thresholds["small_max"]),
        "medium": (dispatch > float(thresholds["small_max"]))
        & (dispatch <= float(thresholds["medium_max"])),
        "large": dispatch > float(thresholds["medium_max"]),
    }
    trusted = raw_lower.copy()
    for group, mask in masks.items():
        trusted[mask] = np.clip(raw_lower[mask] - float(adjustments[group]), 0.0, 1.0)

    prior_index = data.feature_names.index("prior_delivery_ratio_mean")
    count_index = data.feature_names.index("prior_event_count")
    global_train_mean = float(np.mean(data.train.targets))
    baseline = np.asarray(
        [
            global_train_mean if row[count_index] == 0 else row[prior_index]
            for row in features
        ],
        dtype=float,
    )
    result = evaluate_predictions(actual, dispatch, baseline, expected, trusted, config)
    result["acceptance_checks"]["acn_sources_are_disjoint"] = True
    result["accepted"] = all(result["acceptance_checks"].values())
    report = {
        "candidate_version": config["candidate_version"],
        "evaluation_status": "final_source_disjoint_holdout_evaluated_once",
        "decision": "accepted_for_offline_demo" if result["accepted"] else "rejected",
        "deployment_allowed": False,
        "demo_allowed": bool(result["accepted"]),
        "holdout_provenance": {
            "resource_count": len(set(holdout["resource_ids"])),
            "row_count": len(holdout["resource_ids"]),
            "original_acn_source_count": len(original_sources),
            "new_acn_source_count": len(holdout_sources),
            "source_overlap_count": 0,
            "prepared_holdout_canonical_sha256": canonical_sha256(holdout_path),
        },
        "result": result,
        "limitations": [
            "The holdout uses new real ACN session structures but synthetic EV behaviour.",
            "This is not real Ahmedabad or production grid validation.",
            "Candidate 1's consumed holdout was not reused.",
            "Offline gate acceptance permits a hackathon demo, not real dispatch.",
        ],
    }
    if result["accepted"]:
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "candidate_version": config["candidate_version"],
                "expected_model": expected_model,
                "lower_bound_model": lower_model,
                "config": config,
            },
            model_path,
        )
        report["model_artifact"] = {
            "saved": True,
            "use": "offline_hackathon_demo_only",
            "path": str(model_path),
            "sha256": file_sha256(model_path),
        }
    else:
        report["model_artifact"] = {
            "saved": False,
            "reason": "candidate v2 failed one or more locked checks",
        }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--holdout", type=Path, default=DEFAULT_HOLDOUT_PATH)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--development-report", type=Path, default=DEFAULT_DEVELOPMENT_REPORT_PATH)
    parser.add_argument("--original-sources", type=Path, default=DEFAULT_ORIGINAL_SOURCES)
    parser.add_argument("--holdout-sources", type=Path, default=DEFAULT_HOLDOUT_SOURCES)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    args = parser.parse_args()
    report = run_final_evaluation(
        args.training,
        args.holdout,
        args.config,
        args.development_report,
        args.original_sources,
        args.holdout_sources,
        args.report,
        args.model,
    )
    result = report["result"]
    print(f"Candidate v2 final decision: {report['decision']}")
    print(f"Holdout rows: {result['row_count']}")
    print(f"Expected MAE ratio: {result['expected_metrics']['mae_ratio']:.6f}")
    print(
        "Trusted overprediction rate: "
        f"{result['safety']['overall_overprediction_rate_percent']:.2f}%"
    )
    print(
        "Trusted kW retained: "
        f"{result['safety']['trusted_kw_retained_percent']:.2f}%"
    )
    for group, values in result["safety"]["dispatch_groups"].items():
        print(
            f"{group.title()} overprediction: "
            f"{values['overprediction_rate_percent']:.2f}% "
            f"({'PASS' if values['passes'] else 'FAIL'})"
        )


if __name__ == "__main__":
    main()
