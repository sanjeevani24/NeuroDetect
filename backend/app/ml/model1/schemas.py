from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.ml.model1.config import MODEL_FEATURE_NAMES


class Model1PredictionResponse(BaseModel):
    assessment_id: str
    model: str
    model_version: str
    cognitive_performance_score: float
    status: Literal["success", "existing"]


class Model1FeatureVectorResponse(BaseModel):
    assessment_id: str
    model: str
    model_version: str
    cognitive_performance_score: float
    feature_vector: dict[str, float]
    feature_order: list[str] = Field(default_factory=lambda: list(MODEL_FEATURE_NAMES))
