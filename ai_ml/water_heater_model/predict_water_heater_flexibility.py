"""Load the locked bundle and predict expected_kw and trusted_kw."""

from __future__ import annotations

from math import isfinite
from pathlib import Path
from typing import Mapping, Sequence

import joblib
import numpy as np


DEFAULT_ARTIFACT = Path("ai_ml/water_heater_model/artifacts/water_heater_candidate_v1_demo_bundle.joblib")


def load_bundle(path: Path = DEFAULT_ARTIFACT) -> dict:
    bundle = joblib.load(path)
    required = {"expected_model", "lower_bound_model", "config"}
    if not required <= set(bundle):
        raise ValueError("water-heater model bundle is incomplete")
    return bundle


def predict_flexibility(bundle: dict, rows: Sequence[Mapping[str, object]]) -> list[dict]:
    if not rows:
        raise ValueError("at least one feature row is required")
    config = bundle["config"]
    names = config["feature_contract"]["names_in_order"]
    medians = config["feature_contract"]["imputation_medians"]
    imputable = set(config["feature_contract"]["features_allowed_to_be_missing"])
    matrix, potential = [], []
    for number, row in enumerate(rows, start=1):
        vector = []
        for name in names:
            raw = row.get(name)
            if raw is None or raw == "":
                if name not in imputable:
                    raise ValueError(f"row {number}: required feature {name!r} is missing")
                raw = medians[name]
            value = float(raw)
            if not isfinite(value):
                raise ValueError(f"row {number}: feature {name!r} must be finite")
            vector.append(value)
        if float(row["potential_kw"]) < 0:
            raise ValueError(f"row {number}: potential_kw must be non-negative")
        matrix.append(vector)
        potential.append(float(row["potential_kw"]))
    x = np.asarray(matrix)
    expected = np.clip(bundle["expected_model"].predict(x), 0.0, 1.0)
    trusted = np.minimum(expected, np.clip(bundle["lower_bound_model"].predict(x), 0.0, 1.0))
    return [
        {"potential_kw": kw, "expected_ratio": float(er), "trusted_ratio": float(tr), "expected_kw": kw * float(er), "trusted_kw": kw * float(tr), "confidence": float(tr / er) if er > 0 else 0.0}
        for kw, er, tr in zip(potential, expected, trusted)
    ]
