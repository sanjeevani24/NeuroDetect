from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.core.config import get_settings
from app.core.database import get_supabase_client
from app.games.boston_naming.exceptions import (
    AssessmentNotFoundError,
    DuplicateCompletionError,
    FeatureComputationError,
    FeatureValidationError,
    InvalidAssessmentIdError,
    TelemetryValidationError,
)
from app.games.boston_naming.schemas import BostonNamingCompleteRequest, BostonNamingCompleteResponse
from app.games.boston_naming.service import BostonNamingService
from app.repositories.boston_naming_repository import BostonNamingRepository

logger = logging.getLogger("neurodetect.boston_naming")

router = APIRouter(prefix="/api/assessments", tags=["boston-naming"])


def get_boston_naming_service(client: Client = Depends(get_supabase_client)) -> BostonNamingService:
    return BostonNamingService(BostonNamingRepository(client))


@router.post("/{assessment_id}/games/boston-naming/complete", response_model=BostonNamingCompleteResponse, status_code=201)
def complete_boston_naming_game(
    assessment_id: str,
    request: BostonNamingCompleteRequest,
    service: BostonNamingService = Depends(get_boston_naming_service),
) -> BostonNamingCompleteResponse:
    try:
        return service.complete_game(assessment_id, request)
    except InvalidAssessmentIdError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AssessmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DuplicateCompletionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (TelemetryValidationError, FeatureValidationError, FeatureComputationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unhandled error completing Boston Naming for %s", assessment_id)
        detail = str(exc) if get_settings().ENVIRONMENT == "development" else "Internal server error."
        raise HTTPException(status_code=500, detail=detail) from None
