from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.core.config import get_settings
from app.core.database import get_supabase_client
from app.games.trail_making.exceptions import (
    AssessmentNotFoundError,
    DuplicateCompletionError,
    FeatureComputationError,
    FeatureValidationError,
    InvalidAssessmentIdError,
    TelemetryValidationError,
)
from app.games.trail_making.schemas import TrailMakingCompleteRequest, TrailMakingCompleteResponse
from app.games.trail_making.service import TrailMakingService
from app.repositories.trail_making_repository import TrailMakingRepository

logger = logging.getLogger("neurodetect.trail_making")

router = APIRouter(prefix="/api/assessments", tags=["trail-making"])


def get_trail_making_service(client: Client = Depends(get_supabase_client)) -> TrailMakingService:
    return TrailMakingService(TrailMakingRepository(client))


@router.post(
    "/{assessment_id}/games/trail-making/complete",
    response_model=TrailMakingCompleteResponse,
    status_code=201,
)
def complete_trail_making_game(
    assessment_id: str,
    request: TrailMakingCompleteRequest,
    service: TrailMakingService = Depends(get_trail_making_service),
) -> TrailMakingCompleteResponse:
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
        logger.exception("Unhandled error completing Trail Making for %s", assessment_id)
        detail = str(exc) if get_settings().ENVIRONMENT == "development" else "Internal server error."
        raise HTTPException(status_code=500, detail=detail) from None
