from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.assessments.schemas import AssessmentSessionResponse, PatientCreateRequest
from app.core.config import get_settings
from app.core.database import get_supabase_client
from app.repositories.assessment_repository import AssessmentRepository

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


def get_assessment_repository(client: Client = Depends(get_supabase_client)) -> AssessmentRepository:
    return AssessmentRepository(client)


@router.post("", response_model=AssessmentSessionResponse, status_code=201)
def create_assessment_session(
    request: PatientCreateRequest,
    repository: AssessmentRepository = Depends(get_assessment_repository),
) -> AssessmentSessionResponse:
    try:
        return AssessmentSessionResponse(
            **repository.create_assessment_session(
                full_name=request.full_name,
                age=request.age,
                sex=request.sex,
                education_years=request.education_years,
            )
        )
    except Exception as exc:
        detail = str(exc) if get_settings().ENVIRONMENT == "development" else "Internal server error."
        raise HTTPException(status_code=500, detail=detail) from None


@router.get("/{assessment_id}", response_model=AssessmentSessionResponse)
def get_assessment_session(
    assessment_id: str,
    repository: AssessmentRepository = Depends(get_assessment_repository),
) -> AssessmentSessionResponse:
    try:
        UUID(assessment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="assessment_id must be a valid UUID.") from exc

    try:
        session = repository.get_assessment_session(assessment_id)
    except Exception as exc:
        detail = str(exc) if get_settings().ENVIRONMENT == "development" else "Internal server error."
        raise HTTPException(status_code=500, detail=detail) from None

    if session is None:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    return AssessmentSessionResponse(**session)
