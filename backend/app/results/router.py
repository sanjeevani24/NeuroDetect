from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.core.config import get_settings
from app.core.database import get_supabase_client
from app.ml.model1.exceptions import Model1SchemaNotReadyError
from app.repositories.results_repository import ResultsRepository
from app.results.schemas import AssessmentResultsResponse
from app.results.service import AssessmentResultsNotFoundError, ResultsService

router = APIRouter(prefix="/api/assessments", tags=["results"])


def get_results_service(client: Client = Depends(get_supabase_client)) -> ResultsService:
    return ResultsService(ResultsRepository(client))


@router.get("/{assessment_id}/results", response_model=AssessmentResultsResponse)
def get_assessment_results(
    assessment_id: str,
    service: ResultsService = Depends(get_results_service),
) -> AssessmentResultsResponse:
    try:
        UUID(assessment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="assessment_id must be a valid UUID.") from exc

    try:
        return AssessmentResultsResponse(**service.get_results(assessment_id))
    except AssessmentResultsNotFoundError:
        raise HTTPException(status_code=404, detail="Assessment not found.") from None
    except Model1SchemaNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    except Exception as exc:
        detail = str(exc) if get_settings().ENVIRONMENT == "development" else "Unable to load assessment results."
        raise HTTPException(status_code=500, detail=detail) from None
