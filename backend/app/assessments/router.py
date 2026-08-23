from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.assessments.schemas import AssessmentSessionResponse
from app.core.config import get_settings
from app.core.database import get_supabase_client
from app.repositories.assessment_repository import AssessmentRepository

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


def get_assessment_repository(client: Client = Depends(get_supabase_client)) -> AssessmentRepository:
    return AssessmentRepository(client)


@router.post("", response_model=AssessmentSessionResponse, status_code=201)
def create_assessment_session(
    repository: AssessmentRepository = Depends(get_assessment_repository),
) -> AssessmentSessionResponse:
    try:
        return AssessmentSessionResponse(**repository.create_assessment_session())
    except Exception as exc:
        detail = str(exc) if get_settings().ENVIRONMENT == "development" else "Internal server error."
        raise HTTPException(status_code=500, detail=detail) from None
