from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.assessments.schemas import AssessmentStage


class ResultChecklistItem(BaseModel):
    key: str
    label: str
    completed: bool


class RegressionTestMetrics(BaseModel):
    mae: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    rmse: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    r2: float | None = Field(default=None, le=1, allow_inf_nan=False)
    median_absolute_error: float | None = Field(default=None, ge=0, allow_inf_nan=False)


class ModelEvaluationSummary(BaseModel):
    source: str = "model_metadata.json"
    data_type: str | None = None
    clinical_validation: bool | None = None
    test_samples: int | None = Field(default=None, ge=1)
    test_metrics: RegressionTestMetrics


class Model1ResultSummary(BaseModel):
    available: bool
    cognitive_performance_score: float | None = None
    model_name: str | None = None
    model_version: str | None = None
    feature_count: int | None = None
    model_type: str | None = None
    score_scale_max: float | None = None
    evaluation: ModelEvaluationSummary | None = None


class ScreeningScoreSummary(BaseModel):
    available: bool
    score: int | None = None
    score_max: int
    severity: str | None = None


class MentalHealthResultsSummary(BaseModel):
    phq9: ScreeningScoreSummary
    gad7: ScreeningScoreSummary


class PendingModuleSummary(BaseModel):
    available: Literal[False]
    status: Literal["pending"]
    title: str
    description: str


class AssessmentResultsResponse(BaseModel):
    assessment_id: str
    assessment_short_id: str
    participant_name: str
    status: Literal["completed", "incomplete", "awaiting_model1"]
    current_stage: AssessmentStage
    next_stage: AssessmentStage
    completion_message: str
    model1: Model1ResultSummary
    mental_health: MentalHealthResultsSummary
    model3: PendingModuleSummary
    fusion: PendingModuleSummary
    completed_components: list[ResultChecklistItem]
    missing_components: list[str]
