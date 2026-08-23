from __future__ import annotations

import json
import math
from functools import lru_cache
from typing import Any

import xgboost as xgb

from app.ml.model1.config import FEATURE_SCHEMA_PATH, MODEL_FEATURE_NAMES, MODEL_METADATA_PATH, MODEL_PATH
from app.ml.model1.exceptions import Model1ArtifactError, Model1PredictionError


def _load_json(path) -> dict[str, Any]:
    if not path.exists():
        raise Model1ArtifactError(f"Model artifact missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache
def load_model_metadata() -> dict[str, Any]:
    return _load_json(MODEL_METADATA_PATH)


@lru_cache
def load_feature_schema() -> dict[str, Any]:
    return _load_json(FEATURE_SCHEMA_PATH)


@lru_cache
def get_model1_booster() -> xgb.Booster:
    if not MODEL_PATH.exists():
        raise Model1ArtifactError(f"Model artifact missing: {MODEL_PATH}")
    booster = xgb.Booster()
    booster.load_model(str(MODEL_PATH))
    return booster


def predict_cognitive_performance(feature_vector: dict[str, float]) -> float:
    values = [feature_vector[name] for name in MODEL_FEATURE_NAMES]
    matrix = xgb.DMatrix([values], feature_names=MODEL_FEATURE_NAMES)
    prediction = float(get_model1_booster().predict(matrix)[0])
    if not math.isfinite(prediction):
        raise Model1PredictionError("Model 1 prediction was not finite.")
    return prediction
