from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


AssessmentStage = Literal[
    "PATIENT_INFO",
    "PHQ_GAD",
    "COGNITIVE",
    "MMSE",
    "MEMORY",
    "NBACK",
    "BOSTON_NAMING",
    "TRAIL_MAKING",
    "SPEECH",
    "RESULTS",
]


class PatientCreateRequest(BaseModel):
    full_name: str = Field(min_length=1)
    age: int = Field(gt=0)
    sex: str = Field(min_length=1)
    education_years: int = Field(ge=0)

    @field_validator("full_name", "sex")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Value is required.")
        return stripped


class AssessmentSessionResponse(BaseModel):
    patient_id: str
    assessment_id: str
    full_name: str
    age: int
    sex: str
    education_years: int
    current_stage: AssessmentStage
    completed_stages: list[AssessmentStage]
