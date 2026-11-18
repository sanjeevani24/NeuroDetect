from __future__ import annotations

import pytest

from app.games.trail_making.exceptions import AssessmentNotFoundError, DuplicateCompletionError, InvalidAssessmentIdError
from app.games.trail_making.schemas import TrailMakingCompleteRequest
from app.games.trail_making.service import TrailMakingService, process_trail_making_completion
from tests.games.trail_making.fixtures import ASSESSMENT_ID, GAME_SESSION_ID, perfect_request


class FakeTrailRepository:
    def __init__(self, *, assessment_exists=True, result_exists=False):
        self._assessment_exists = assessment_exists
        self._result_exists = result_exists
        self.inserted_result = None
        self.inserted_events = None

    def assessment_exists(self, assessment_id: str) -> bool:
        return self._assessment_exists

    def result_exists(self, assessment_id: str) -> bool:
        return self._result_exists

    def insert_result(self, assessment_id: str, game_session_id: str, features):
        self.inserted_result = (assessment_id, game_session_id, features)
        return {}

    def insert_events(self, events):
        self.inserted_events = list(events)


def build_request() -> TrailMakingCompleteRequest:
    layout, events = perfect_request()
    return TrailMakingCompleteRequest(game_session_id=GAME_SESSION_ID, node_layout=layout, events=events)


def test_process_trail_making_completion():
    features = process_trail_making_completion(ASSESSMENT_ID, build_request())
    assert features.correct_target_count == 25
    assert features.sequence_accuracy == pytest.approx(1.0)


def test_service_rejects_invalid_uuid():
    with pytest.raises(InvalidAssessmentIdError):
        TrailMakingService(FakeTrailRepository()).complete_game("not-a-uuid", build_request())


def test_service_rejects_missing_assessment():
    with pytest.raises(AssessmentNotFoundError):
        TrailMakingService(FakeTrailRepository(assessment_exists=False)).complete_game(ASSESSMENT_ID, build_request())


def test_service_rejects_duplicate_completion():
    with pytest.raises(DuplicateCompletionError):
        TrailMakingService(FakeTrailRepository(result_exists=True)).complete_game(ASSESSMENT_ID, build_request())


def test_service_persists_result_and_events():
    repo = FakeTrailRepository()
    service = TrailMakingService(repo)
    response = service.complete_game(ASSESSMENT_ID, build_request())
    assert response.status == "completed"
    assert repo.inserted_result is not None
    assert repo.inserted_events is not None
