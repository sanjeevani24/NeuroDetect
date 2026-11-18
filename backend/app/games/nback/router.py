from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.core.config import get_settings
from app.core.database import get_supabase_client
from app.games.nback.schemas import NBackCompleteRequest, NBackCompleteResponse
from app.games.nback.service import (
    AssessmentNotFoundError,
    DuplicateCompletionError,
    FeaturesInvalidError,
    InvalidAssessmentIdError,
    NBackGameService,
    TelemetryInvalidError,
)
from app.repositories.nback_repository import NBackRepository

logger = logging.getLogger("neurodetect.nback")

router = APIRouter(prefix="/api/assessments", tags=["nback"])


def get_nback_service(client: Client = Depends(get_supabase_client)) -> NBackGameService:
    return NBackGameService(NBackRepository(client))


@router.post("/{assessment_id}/games/nback/complete", response_model=NBackCompleteResponse)
def complete_nback_game(
    assessment_id: str,
    request: NBackCompleteRequest,
    service: NBackGameService = Depends(get_nback_service),
) -> NBackCompleteResponse:
    try:
        return service.complete_game(assessment_id, request)
    except InvalidAssessmentIdError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AssessmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DuplicateCompletionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except TelemetryInvalidError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc
    except FeaturesInvalidError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc
    except Exception as exc:
        logger.exception("Unhandled error completing N-Back for %s", assessment_id)
        detail = str(exc) if get_settings().ENVIRONMENT == "development" else "Internal server error."
        raise HTTPException(status_code=500, detail=detail) from None
