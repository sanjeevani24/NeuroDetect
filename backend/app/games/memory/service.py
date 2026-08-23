"""
Service layer for the Memory Recall game.

Orchestrates: validate completion preconditions -> extract features ->
validate features -> persist -> return result. No HTTP concerns, no SQL.
"""
from __future__ import annotations

from app.games.memory.config import REQUIRED_PHASES
from app.games.memory.exceptions import (
    AssessmentNotFoundError,
    DuplicateCompletionError,
    InvalidEventSequenceError,
)
from app.games.memory.features import extract_features
from app.games.memory.schemas import (
    MemoryEventType,
    MemoryFeatureSet,
    MemoryGameCompletionRequest,
    MemoryGameResult,
    MemoryPhase,
)
from app.games.memory.validators import validate_features
from app.repositories.memory_repository import MemoryRepository


def _assert_required_phases_completed(request: MemoryGameCompletionRequest) -> None:
    completed_phases = {
        e.phase.value
        for e in request.events
        if e.event_type == MemoryEventType.PHASE_COMPLETED
    }
    missing = [p for p in REQUIRED_PHASES if p not in completed_phases]
    if missing:
        raise InvalidEventSequenceError(
            f"Missing phase_completed events for required phase(s): {', '.join(missing)}"
        )

    has_game_completed = any(
        e.event_type == MemoryEventType.GAME_COMPLETED for e in request.events
    )
    if not has_game_completed:
        raise InvalidEventSequenceError("Missing game_completed event.")


class MemoryGameService:
    def __init__(self, repository: MemoryRepository):
        self._repository = repository

    def complete_game(
        self, assessment_id: str, request: MemoryGameCompletionRequest
    ) -> MemoryGameResult:
        if not self._repository.assessment_exists(assessment_id):
            raise AssessmentNotFoundError(f"assessment_id '{assessment_id}' does not exist.")

        if self._repository.result_exists(assessment_id):
            raise DuplicateCompletionError(
                f"Memory Recall has already been completed for assessment_id '{assessment_id}'."
            )

        # every event must belong to the assessment being completed
        mismatched = [e.event_id for e in request.events if e.assessment_id != assessment_id]
        if mismatched:
            raise InvalidEventSequenceError(
                "One or more events reference a different assessment_id than the URL."
            )

        _assert_required_phases_completed(request)

        extracted = extract_features(request.events, request.confidence)
        validate_features(extracted)

        feature_set = MemoryFeatureSet(**extracted.__dict__)

        self._repository.insert_result(assessment_id, extracted)

        return MemoryGameResult(assessment_id=assessment_id, features=feature_set)
