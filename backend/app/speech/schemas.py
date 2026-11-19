from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


TranscriptionStatus = Literal["pending", "completed", "failed", "verified"]
InferenceStatus = Literal["pending", "completed", "failed", "awaiting_asr_verification"]
SpeechPredictedClass = Literal["HC", "MCI", "Dementia"]


class SpeechUploadResponse(BaseModel):
    assessment_id: str
    status: str
    transcription_status: TranscriptionStatus
    transcription_engine: str
    inference_status: InferenceStatus
    predicted_class: SpeechPredictedClass | None = None
    probability_hc: float | None = None
    hc_probability: float | None = None
    probability_mci: float | None = None
    mci_probability: float | None = None
    probability_dementia: float | None = None
    dementia_probability: float | None = None
    probabilities: dict[str, float] | None = None
    branch_probabilities: dict[str, Any] | None = None
    model_name: str | None = None
    model_version: str | None = None
    disclaimer: str
    error_message: str | None = None


class SpeechResultResponse(BaseModel):
    assessment_id: str
    status: str
    speech_id: str | None = None
    transcript: str | None = None
    transcription_status: TranscriptionStatus
    transcription_engine: str
    inference_status: InferenceStatus
    predicted_class: SpeechPredictedClass | None = None
    probability_hc: float | None = None
    hc_probability: float | None = None
    probability_mci: float | None = None
    mci_probability: float | None = None
    probability_dementia: float | None = None
    dementia_probability: float | None = None
    probabilities: dict[str, float] | None = None
    branch_probabilities: dict[str, Any] | None = None
    components_used: list[str] | None = None
    model_name: str | None = None
    model_version: str | None = None
    disclaimer: str
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
