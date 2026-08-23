from __future__ import annotations

import uuid

from app.games.mmse.config import REQUIRED_PHASES
from app.games.mmse.exceptions import (
    AssessmentNotFoundError,
    DuplicateCompletionError,
    InvalidAssessmentIdError,
    InvalidEventSequenceError,
)
from app.games.mmse.features import extract_features
from app.games.mmse.schemas import MMSECompletionRequest, MMSEEventType, MMSEFeatureSet, MMSEGameResult
from app.games.mmse.validators import validate_features
from app.repositories.mmse_repository import MMSERepository


def _assert_required_phases_completed(request: MMSECompletionRequest) -> None:
    completed_phases = {
        event.phase.value for event in request.events if event.event_type == MMSEEventType.PHASE_COMPLETED
    }
    missing = [phase for phase in REQUIRED_PHASES if phase not in completed_phases]
    if missing:
        raise InvalidEventSequenceError(
            f"Missing phase_completed events for required phase(s): {', '.join(missing)}"
        )

    has_game_completed = any(event.event_type == MMSEEventType.GAME_COMPLETED for event in request.events)
    if not has_game_completed:
        raise InvalidEventSequenceError("Missing game_completed event.")


class MMSEGameService:
    def __init__(self, repository: MMSERepository):
        self._repository = repository

    def complete_game(self, assessment_id: str, request: MMSECompletionRequest) -> MMSEGameResult:
        try:
            uuid.UUID(assessment_id)
        except ValueError as exc:
            raise InvalidAssessmentIdError("assessment_id must be a valid UUID.") from exc

        if not self._repository.assessment_exists(assessment_id):
            raise AssessmentNotFoundError(f"assessment_id '{assessment_id}' does not exist.")

        if self._repository.result_exists(assessment_id):
            raise DuplicateCompletionError(
                f"MMSE has already been completed for assessment_id '{assessment_id}'."
            )

        mismatched = [event.event_id for event in request.events if event.assessment_id != assessment_id]
        if mismatched:
            raise InvalidEventSequenceError(
                "One or more events reference a different assessment_id than the URL."
            )

        _assert_required_phases_completed(request)

        extracted = extract_features(request.events)
        validate_features(extracted)
        self._repository.insert_result(assessment_id, extracted)

        return MMSEGameResult(
            assessment_id=assessment_id,
            features=MMSEFeatureSet(**extracted.__dict__),
        )
