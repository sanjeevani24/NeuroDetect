"""
HTTP layer for the Memory Recall game.

Responsibilities ONLY: receive request, validate through Pydantic, call the
service, translate domain exceptions to HTTP status codes, return response.
No feature formulas and no SQL live here.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.core.config import get_settings
from app.core.database import get_supabase_client
from app.games.memory.exceptions import (
    AssessmentNotFoundError,
    DuplicateCompletionError,
    FeatureValidationError,
    IncompleteGameDataError,
    InvalidEventSequenceError,
)
from app.games.memory.schemas import MemoryGameCompletionRequest, MemoryGameResult
from app.games.memory.service import MemoryGameService
from app.repositories.memory_repository import MemoryRepository

logger = logging.getLogger("neurodetect.memory")

router = APIRouter(prefix="/api/assessments", tags=["memory"])


def get_memory_service(client: Client = Depends(get_supabase_client)) -> MemoryGameService:
    return MemoryGameService(MemoryRepository(client))


@router.post("/{assessment_id}/games/memory/complete", response_model=MemoryGameResult)
def complete_memory_game(
    assessment_id: str,
    request: MemoryGameCompletionRequest,
    service: MemoryGameService = Depends(get_memory_service),
) -> MemoryGameResult:
    try:
        return service.complete_game(assessment_id, request)
    except AssessmentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DuplicateCompletionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (InvalidEventSequenceError, IncompleteGameDataError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FeatureValidationError as exc:
        raise HTTPException(status_code=422, detail={"feature_errors": exc.errors}) from exc
    except Exception as exc:  # noqa: BLE001 - never leak internals to the client
        logger.exception("Unhandled error completing memory game for %s", assessment_id)
        detail = str(exc) if get_settings().ENVIRONMENT == "development" else "Internal server error."
        raise HTTPException(status_code=500, detail=detail) from None
