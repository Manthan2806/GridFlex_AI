"""Apply a locked EV candidate recipe to new feature rows."""

from __future__ import annotations

from math import isfinite
from typing import Mapping, Sequence

import numpy as np


def _feature_matrix(rows: Sequence[Mapping[str, object]], config: dict) -> np.ndarray:
    contract = config["feature_contract"]
    names = contract["names_in_order"]
    medians = contract["imputation_medians"]
    imputable = set(contract["features_allowed_to_be_missing"])
    matrix: list[list[float]] = []
    for row_number, row in enumerate(rows, start=1):
        values: list[float] = []
        for name in names:
            raw = row.get(name)
            if raw is None or raw == "":
                if name not in imputable:
                    raise ValueError(f"row {row_number}: required feature {name!r} is missing")
                raw = medians[name]
            try:
                value = float(raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"row {row_number}: feature {name!r} must be numeric") from exc
            if not isfinite(value):
                raise ValueError(f"row {row_number}: feature {name!r} must be finite")
            values.append(value)
        matrix.append(values)
    if not matrix:
        raise ValueError("at least one feature row is required")
    return np.asarray(matrix, dtype=float)


def _dispatch_group(dispatched_kw: float, config: dict) -> str:
    thresholds = config["safety_policy"]["dispatch_group_thresholds_kw"]
    if dispatched_kw <= float(thresholds["small_max"]):
        return "small"
    if dispatched_kw <= float(thresholds["medium_max"]):
        return "medium"
    return "large"


def predict_flexibility(model, config: dict, feature_rows: Sequence[Mapping[str, object]], requested_dispatch_kw: Sequence[float]) -> list[dict]:
    """Return expected and conservative flexibility for aligned EV requests."""
    if len(feature_rows) != len(requested_dispatch_kw):
        raise ValueError("feature rows and dispatch values must have equal length")
    matrix = _feature_matrix(feature_rows, config)
    expected_ratios = np.clip(np.asarray(model.predict(matrix), dtype=float), 0.0, 1.0)
    if len(expected_ratios) != len(feature_rows):
        raise ValueError("model returned an unexpected prediction count")
    outputs: list[dict] = []
    margins = config["safety_policy"]["margin_ratio_by_dispatch_group"]
    coverage = float(config["safety_policy"]["coverage_target"])
    for expected_ratio, raw_dispatch in zip(expected_ratios, requested_dispatch_kw):
        dispatch = float(raw_dispatch)
        if not isfinite(dispatch) or dispatch < 0.0:
            raise ValueError("requested dispatch kW must be finite and non-negative")
        group = _dispatch_group(dispatch, config)
        trusted_ratio = max(0.0, float(expected_ratio) - float(margins[group]))
        outputs.append({
            "dispatch_group": group,
            "safety_coverage": coverage,
            "requested_dispatch_kw": dispatch,
            "expected_ratio": float(expected_ratio),
            "trusted_ratio": trusted_ratio,
            "expected_kw": dispatch * float(expected_ratio),
            "trusted_kw": dispatch * trusted_ratio,
        })
    return outputs
