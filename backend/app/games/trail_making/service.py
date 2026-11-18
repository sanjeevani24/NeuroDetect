from __future__ import annotations

import uuid

from app.games.trail_making.exceptions import (
    AssessmentNotFoundError,
    DuplicateCompletionError,
    FeatureComputationError,
    FeatureValidationError,
    InvalidAssessmentIdError,
    TelemetryValidationError,
)
from app.games.trail_making.features import compute_all_features
from app.games.trail_making.schemas import (
    TrailMakingCompleteRequest,
    TrailMakingCompleteResponse,
    TrailMakingFeatures,
)
from app.games.trail_making.validators import validate_features, validate_telemetry
from app.repositories.trail_making_repository import TrailMakingRepository


def process_trail_making_completion(
    assessment_id: str,
    request: TrailMakingCompleteRequest,
) -> TrailMakingFeatures:
    validate_telemetry(request, assessment_id)
    raw_features = compute_all_features(request.events, request.node_layout)
    features = TrailMakingFeatures(**raw_features)
    validate_features(features)
    return features


class TrailMakingService:
    def __init__(self, repository: TrailMakingRepository):
        self._repository = repository

    def complete_game(
        self,
        assessment_id: str,
        request: TrailMakingCompleteRequest,
    ) -> TrailMakingCompleteResponse:
        try:
            uuid.UUID(assessment_id)
        except ValueError as exc:
            raise InvalidAssessmentIdError("assessment_id must be a valid UUID.") from exc

        if not self._repository.assessment_exists(assessment_id):
            raise AssessmentNotFoundError(f"assessment_id '{assessment_id}' does not exist.")

        if self._repository.result_exists(assessment_id):
            raise DuplicateCompletionError(
                f"Trail Making has already been completed for assessment_id '{assessment_id}'."
            )

        features = process_trail_making_completion(assessment_id, request)
        self._repository.insert_result(assessment_id, request.game_session_id, features)
        self._repository.insert_events(request.events)
        return TrailMakingCompleteResponse(
            assessment_id=assessment_id,
            game="trail_making",
            status="completed",
            features=features,
        )
