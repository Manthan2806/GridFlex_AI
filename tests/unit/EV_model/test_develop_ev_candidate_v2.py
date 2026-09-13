from pathlib import Path
from unittest.mock import patch
import http.client

import numpy as np
import pytest

from ai_ml.EV_model.develop_ev_candidate_v2 import (
    conformal_margin,
    lower_bound_candidates,
    split_validation_by_resource,
)
from ai_ml.EV_model.evidence import canonical_sha256
from ai_ml.EV_model.generate_hybrid_ev_data import _excluded_source_paths, _request_bytes
from ai_ml.EV_model.evaluate_ev_candidate_v2 import evaluate_predictions
from ai_ml.EV_model.load_ev_training_data import EVSplit
from backend.app.integrations.ai_ml_client import OfflineDemoEVModelClientV2


def test_canonical_hash_ignores_line_endings(tmp_path: Path):
    unix = tmp_path / "unix.txt"
    windows = tmp_path / "windows.txt"
    unix.write_bytes(b"one\ntwo\n")
    windows.write_bytes(b"one\r\ntwo\r\n")
    assert canonical_sha256(unix) == canonical_sha256(windows)


def test_validation_partition_keeps_resources_disjoint():
    resource_ids = tuple(f"ev-{index:03d}" for index in range(40) for _ in range(2))
    rows = len(resource_ids)
    split = EVSplit(
        resource_ids=resource_ids,
        features=tuple((float(index),) for index in range(rows)),
        targets=tuple(0.5 for _ in range(rows)),
        evaluation_dispatched_kw=tuple(4.0 for _ in range(rows)),
    )
    selection, calibration = split_validation_by_resource(split)
    assert set(selection.resource_ids).isdisjoint(calibration.resource_ids)
    assert selection.row_count + calibration.row_count == rows


def test_conformal_margin_targets_one_sided_overprediction_control():
    actual = np.asarray([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    predicted = actual + 0.1
    margin = conformal_margin(actual, predicted, 0.90)
    trusted = predicted - margin
    assert margin >= 0.1
    assert np.mean(trusted > actual + 1e-12) <= 0.10


def test_lower_bound_candidates_are_quantile_models():
    candidates = lower_bound_candidates()
    assert candidates
    assert all(candidate.parameters["loss"] == "quantile" for candidate in candidates)
    assert all(0.0 < candidate.parameters["quantile"] < 0.5 for candidate in candidates)


def test_excluded_acn_sources_are_loaded_from_csv(tmp_path: Path):
    source_file = tmp_path / "sources.csv"
    source_file.write_text(
        "resource_id,source_session_path\n"
        "ev-1,time series data/site/garage/one.csv.gz\n"
        "ev-2,time series data/site/garage/two.csv.gz\n",
        encoding="utf-8",
    )
    assert _excluded_source_paths(source_file) == {
        "time series data/site/garage/one.csv.gz",
        "time series data/site/garage/two.csv.gz",
    }


def test_github_download_retries_an_incomplete_response():
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"complete"

    with (
        patch(
            "ai_ml.EV_model.generate_hybrid_ev_data.urllib.request.urlopen",
            side_effect=[http.client.IncompleteRead(b"partial"), Response()],
        ) as urlopen,
        patch("ai_ml.EV_model.generate_hybrid_ev_data.time.sleep"),
    ):
        assert _request_bytes("https://example.invalid", timeout=1) == b"complete"
    assert urlopen.call_count == 2


def test_v2_final_gate_requires_every_dispatch_group_to_pass():
    actual = np.asarray([0.1, 0.4, 0.8])
    dispatch = np.asarray([1.0, 4.0, 8.0])
    baseline = np.asarray([0.0, 0.3, 0.7])
    expected = np.asarray([0.1, 0.4, 0.8])
    trusted = np.asarray([0.2, 0.3, 0.7])
    config = {
        "safety_policy": {
            "maximum_allowed_overprediction_rate_percent": 15.0,
            "minimum_retention_percent": 50.0,
            "dispatch_group_thresholds_kw": {"small_max": 2.0, "medium_max": 6.0},
        }
    }
    result = evaluate_predictions(actual, dispatch, baseline, expected, trusted, config)
    assert result["safety"]["dispatch_groups"]["small"]["passes"] is False
    assert result["accepted"] is False


def test_v2_saved_bundle_maps_to_backend_trust_contract():
    client = OfflineDemoEVModelClientV2(demo_mode=True)
    feature_row = dict(client.config["feature_contract"]["imputation_medians"])
    result = client._predict_feature_row(feature_row, requested_dispatch_kw=4.0)
    trust = result.trust_state
    assert result.release_status == "accepted_for_offline_demo"
    assert trust.trusted_kw <= trust.expected_kw <= trust.potential_kw
    assert trust.confidence == pytest.approx(
        trust.trusted_kw / trust.expected_kw if trust.expected_kw else 0.0
    )
