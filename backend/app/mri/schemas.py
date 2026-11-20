from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class BinaryProbabilities(BaseModel):
    no_dementia: float = Field(ge=0.0, le=1.0)
    dementia: float = Field(ge=0.0, le=1.0)


class MriResultResponse(BaseModel):
    assessment_id: str
    status: str = "completed"
    processing_status: str = "completed"
    image_filename: str | None = None
    image_format: str | None = None
    image_size_bytes: int | None = None
    predicted_class: str
    predicted_class_index: int
    probability_non_demented: float = Field(ge=0.0, le=1.0)
    probability_very_mild: float = Field(ge=0.0, le=1.0)
    probability_mild: float = Field(ge=0.0, le=1.0)
    probability_moderate: float = Field(ge=0.0, le=1.0)
    class_probabilities: dict[str, float]
    binary_prediction: str
    binary_probabilities: BinaryProbabilities
    model_name: str = "NeuroDetect-MRI-EfficientNetB0"
    model_version: str = "1.0.0"
    disclaimer: str
    created_at: str | None = None
    updated_at: str | None = None
