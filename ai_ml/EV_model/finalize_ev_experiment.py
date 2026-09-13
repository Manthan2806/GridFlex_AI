"""Create an honest release gate and model card for the completed EV experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ai_ml.EV_model.lock_ev_model_candidate import DEFAULT_OUTPUT_PATH as DEFAULT_CONFIG_PATH
from ai_ml.EV_model.evaluate_ev_final_holdout import DEFAULT_REPORT_PATH as DEFAULT_FINAL_REPORT_PATH


DEFAULT_STATUS_PATH = Path("data/processed/ev_training/ev_release_status.json")
DEFAULT_MODEL_CARD_PATH = Path("ai_ml/EV_model/MODEL_CARD.md")
HANDOFF_VERSION = "ev_experiment_handoff_v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_release_status(final_report: dict) -> dict:
    """Convert the final decision into a backend-readable deployment gate."""
    if final_report.get("status") != "final_holdout_evaluated_once":
        raise ValueError("final holdout evaluation is incomplete")
    holdout = final_report["holdout"]
    checks = holdout["acceptance_checks"]
    failed_checks = sorted(name for name, passed in checks.items() if not passed)
    accepted = bool(holdout.get("accepted")) and final_report.get("decision") == "accepted"
    artifact_saved = bool(final_report.get("model_artifact", {}).get("saved"))
    if accepted != artifact_saved:
        raise ValueError("final decision and model-artifact state are inconsistent")

    return {
        "handoff_version": HANDOFF_VERSION,
        "release_status": "approved_for_deployment" if accepted else "experimental_not_deployable",
        "deployment_allowed": accepted,
        "demo_allowed": True,
        "demo_label_required": "experimental offline estimate",
        "holdout": {
            "consumed": True,
            "reuse_for_tuning_allowed": False,
            "row_count": int(holdout["row_count"]),
        },
        "acceptance": {
            "passed": accepted,
            "failed_checks": failed_checks,
        },
        "model_artifact_saved": artifact_saved,
        "required_backend_action": (
            "allow model-backed dispatch" if accepted else "block model-backed power commitments"
        ),
        "next_valid_experiment_requires": [
            "a newly frozen candidate developed without using this holdout",
            "a genuinely new untouched holdout dataset",
            "acceptance rules declared before that new holdout is opened",
        ],
    }


def assert_deployment_allowed(release_status: dict) -> None:
    """Stop integration code from treating a rejected model as deployable."""
    if not release_status.get("deployment_allowed"):
        raise RuntimeError("EV model is experimental and not approved for deployment")


def build_model_card(config: dict, final_report: dict, release_status: dict) -> str:
    """Render the experiment evidence in plain language for reviewers."""
    holdout = final_report["holdout"]
    baseline = holdout["baseline_metrics"]
    expected = holdout["expected_metrics"]
    trusted = holdout["trusted_metrics"]
    safety = holdout["safety"]
    groups = safety["dispatch_groups"]
    failed = ", ".join(release_status["acceptance"]["failed_checks"])
    model = config["model"]
    feature_count = len(config["feature_contract"]["names_in_order"])
    return f"""# GridFlex AI EV model card

## Release status

**Experimental — not approved for deployment.**

This model may be shown in the hackathon as an offline prototype. It must not be used to promise or dispatch real power.

## What it predicts

The model estimates the fraction of requested EV power likely to be delivered. It reports a raw `expected_kw` value and a more conservative `trusted_kw` value.

## Model and data

- Algorithm: `{model['family']}` (`{model['selected_name']}` configuration)
- Input features: {feature_count}
- Safety target selected before final testing: {safety['coverage_target']:.0%}
- Final holdout rows: {holdout['row_count']:,}
- Data basis: ACN session structure combined with synthetic EV behaviour

## Final holdout results

| Measure | Rolling-history baseline | Random Forest expected estimate | Trusted estimate |
| --- | ---: | ---: | ---: |
| Delivery-ratio MAE | {baseline['mae_ratio']:.6f} | {expected['mae_ratio']:.6f} | {trusted['mae_ratio']:.6f} |
| Power MAE | {baseline['mae_kw']:.6f} kW | {expected['mae_kw']:.6f} kW | {trusted['mae_kw']:.6f} kW |

The trusted estimate retained {safety['trusted_kw_retained_percent_of_expected']:.2f}% of expected power. Its overall overprediction rate was {safety['overall_overprediction_rate_percent']:.2f}% against a maximum of {safety['maximum_allowed_overprediction_rate_percent']:.2f}%.

| Dispatch group | Overprediction rate | Limit | Result |
| --- | ---: | ---: | --- |
| Small | {groups['small']['overprediction_rate_percent']:.2f}% | {groups['small']['maximum_allowed_percent']:.2f}% | {'Pass' if groups['small']['passes'] else 'Fail'} |
| Medium | {groups['medium']['overprediction_rate_percent']:.2f}% | {groups['medium']['maximum_allowed_percent']:.2f}% | {'Pass' if groups['medium']['passes'] else 'Fail'} |
| Large | {groups['large']['overprediction_rate_percent']:.2f}% | {groups['large']['maximum_allowed_percent']:.2f}% | {'Pass' if groups['large']['passes'] else 'Fail'} |

## Decision

The candidate was rejected because it failed: `{failed}`. Small and medium dispatches crossed the pre-declared 15% limit. The production model artifact was therefore not saved.

## Allowed use

- Demonstrate the data pipeline and prediction flow.
- Show expected and trusted estimates with the label **experimental offline estimate**.
- Discuss the final result as an example of an honest model-validation gate.

## Not allowed

- Do not call the model production-ready, validated for Ahmedabad, or safe for real grid dispatch.
- Do not change the safety threshold after seeing the final results and then claim the same holdout as independent evidence.
- Do not reuse the consumed holdout for tuning.

## Next valid experiment

Develop the next candidate using training and validation evidence only. Evaluate it against a genuinely new untouched dataset with acceptance rules fixed in advance.
"""


def run_handoff(config_path: Path = DEFAULT_CONFIG_PATH, final_report_path: Path = DEFAULT_FINAL_REPORT_PATH, status_path: Path = DEFAULT_STATUS_PATH, model_card_path: Path = DEFAULT_MODEL_CARD_PATH) -> tuple[dict, str]:
    with config_path.open(encoding="utf-8") as handle:
        config = json.load(handle)
    with final_report_path.open(encoding="utf-8") as handle:
        final_report = json.load(handle)
    if final_report.get("locked_config", {}).get("sha256") != _sha256(config_path):
        raise ValueError("final report does not match the locked candidate configuration")
    release_status = build_release_status(final_report)
    release_status["evidence"] = {
        "locked_config": {"path": str(config_path), "sha256": _sha256(config_path)},
        "final_report": {"path": str(final_report_path), "sha256": _sha256(final_report_path)},
    }
    model_card = build_model_card(config, final_report, release_status)
    status_path.parent.mkdir(parents=True, exist_ok=True)
    model_card_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(release_status, indent=2) + "\n", encoding="utf-8")
    model_card_path.write_text(model_card, encoding="utf-8")
    return release_status, model_card


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--final-report", type=Path, default=DEFAULT_FINAL_REPORT_PATH)
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS_PATH)
    parser.add_argument("--model-card", type=Path, default=DEFAULT_MODEL_CARD_PATH)
    args = parser.parse_args()
    status, _ = run_handoff(args.config, args.final_report, args.status, args.model_card)
    print(f"EV release status: {status['release_status']}")
    print(f"Deployment allowed: {status['deployment_allowed']}")
    print("The consumed holdout was not reopened.")


if __name__ == "__main__":
    main()
