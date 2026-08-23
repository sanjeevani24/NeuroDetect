from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.core.config import get_settings
from app.core.database import get_supabase_client
from app.mental_health.schemas import MentalHealthCompleteRequest, MentalHealthCompleteResponse
from app.mental_health.service import (
    InvalidMentalHealthAssessmentIdError,
    MentalHealthAssessmentNotFoundError,
    MentalHealthService,
)
from app.repositories.mental_health_repository import MentalHealthRepository

router = APIRouter(prefix="/api/assessments", tags=["mental-health"])


def get_mental_health_repository(
    client: Client = Depends(get_supabase_client),
) -> MentalHealthRepository:
    return MentalHealthRepository(client)


def get_mental_health_service(
    repository: MentalHealthRepository = Depends(get_mental_health_repository),
) -> MentalHealthService:
    return MentalHealthService(repository)


@router.post("/{assessment_id}/mental-health/complete", response_model=MentalHealthCompleteResponse)
def complete_mental_health_screening(
    assessment_id: str,
    request: MentalHealthCompleteRequest,
    service: MentalHealthService = Depends(get_mental_health_service),
) -> MentalHealthCompleteResponse:
    try:
        return service.complete_screening(assessment_id, request)
    except InvalidMentalHealthAssessmentIdError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except MentalHealthAssessmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        detail = str(exc) if get_settings().ENVIRONMENT == "development" else "Internal server error."
        raise HTTPException(status_code=500, detail=detail) from None
