from __future__ import annotations

<<<<<<< HEAD
from typing import Literal
=======
from typing import Any, Literal
>>>>>>> neurodetect-model_3

from pydantic import BaseModel, Field

from app.assessments.schemas import AssessmentStage
<<<<<<< HEAD
=======
from app.fusion.schemas import FusionResultSummary
>>>>>>> neurodetect-model_3


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


<<<<<<< HEAD
=======
class Model3ResultSummary(BaseModel):
    available: bool
    status: str = "pending"
    title: str = "Speech Assessment"
    description: str | None = None
    predicted_class: str | None = None
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
    disclaimer: str | None = None
    error_message: str | None = None
    transcription_engine: str | None = None


>>>>>>> neurodetect-model_3
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
<<<<<<< HEAD
    model3: PendingModuleSummary
    fusion: PendingModuleSummary
=======
    model3: Model3ResultSummary | PendingModuleSummary
    fusion: FusionResultSummary | PendingModuleSummary
>>>>>>> neurodetect-model_3
    completed_components: list[ResultChecklistItem]
    missing_components: list[str]
