from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.core.config import get_settings
from app.core.database import get_supabase_client
from app.games.mmse.exceptions import (
    AssessmentNotFoundError,
    DuplicateCompletionError,
    FeatureValidationError,
    IncompleteGameDataError,
    InvalidAssessmentIdError,
    InvalidEventSequenceError,
)
from app.games.mmse.schemas import MMSECompletionRequest, MMSEGameResult
from app.games.mmse.service import MMSEGameService
from app.repositories.mmse_repository import MMSERepository

logger = logging.getLogger("neurodetect.mmse")

router = APIRouter(prefix="/api/assessments", tags=["mmse"])


def get_mmse_service(client: Client = Depends(get_supabase_client)) -> MMSEGameService:
    return MMSEGameService(MMSERepository(client))


@router.post("/{assessment_id}/games/mmse/complete", response_model=MMSEGameResult)
def complete_mmse_game(
    assessment_id: str,
    request: MMSECompletionRequest,
    service: MMSEGameService = Depends(get_mmse_service),
) -> MMSEGameResult:
    try:
        return service.complete_game(assessment_id, request)
    except InvalidAssessmentIdError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AssessmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DuplicateCompletionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (InvalidEventSequenceError, IncompleteGameDataError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FeatureValidationError as exc:
        raise HTTPException(status_code=422, detail={"feature_errors": exc.errors}) from exc
    except Exception as exc:
        logger.exception("Unhandled error completing MMSE for %s", assessment_id)
        detail = str(exc) if get_settings().ENVIRONMENT == "development" else "Internal server error."
        raise HTTPException(status_code=500, detail=detail) from None
