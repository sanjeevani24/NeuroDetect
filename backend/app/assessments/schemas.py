from __future__ import annotations

from pydantic import BaseModel


class AssessmentSessionResponse(BaseModel):
    patient_id: str
    assessment_id: str
