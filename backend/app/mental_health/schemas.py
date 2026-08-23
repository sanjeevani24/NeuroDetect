from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AnswerValue = int
PHQ9Severity = Literal["Minimal", "Mild", "Moderate", "Moderately severe", "Severe"]
GAD7Severity = Literal["Mild", "Moderate", "Moderately severe", "Severe"]


class PHQ9Answers(BaseModel):
    q1: AnswerValue = Field(ge=0, le=3)
    q2: AnswerValue = Field(ge=0, le=3)
    q3: AnswerValue = Field(ge=0, le=3)
    q4: AnswerValue = Field(ge=0, le=3)
    q5: AnswerValue = Field(ge=0, le=3)
    q6: AnswerValue = Field(ge=0, le=3)
    q7: AnswerValue = Field(ge=0, le=3)
    q8: AnswerValue = Field(ge=0, le=3)
    q9: AnswerValue = Field(ge=0, le=3)


class GAD7Answers(BaseModel):
    q1: AnswerValue = Field(ge=0, le=3)
    q2: AnswerValue = Field(ge=0, le=3)
    q3: AnswerValue = Field(ge=0, le=3)
    q4: AnswerValue = Field(ge=0, le=3)
    q5: AnswerValue = Field(ge=0, le=3)
    q6: AnswerValue = Field(ge=0, le=3)
    q7: AnswerValue = Field(ge=0, le=3)


class MentalHealthCompleteRequest(BaseModel):
    phq9: PHQ9Answers
    gad7: GAD7Answers


class PHQ9ResultResponse(BaseModel):
    total_score: int
    severity: PHQ9Severity
    evaluation_cutoff_met: bool


class GAD7ResultResponse(BaseModel):
    total_score: int
    severity: GAD7Severity
    evaluation_cutoff_met: bool


class MentalHealthCompleteResponse(BaseModel):
    assessment_id: str
    status: Literal["completed", "already_completed"]
    phq9: PHQ9ResultResponse
    gad7: GAD7ResultResponse
