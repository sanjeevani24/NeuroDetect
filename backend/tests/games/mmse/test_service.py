import pytest

from app.games.mmse.exceptions import (
    AssessmentNotFoundError,
    DuplicateCompletionError,
    InvalidAssessmentIdError,
    InvalidEventSequenceError,
)
from app.games.mmse.service import MMSEGameService
from tests.games.mmse.fixtures import ASSESSMENT_ID, build_request


class FakeRepository:
    def __init__(self, assessment_exists: bool = True, result_exists: bool = False):
        self._assessment_exists = assessment_exists
        self._result_exists = result_exists
        self.inserted = None

    def assessment_exists(self, assessment_id: str) -> bool:
        return self._assessment_exists

    def result_exists(self, assessment_id: str) -> bool:
        return self._result_exists

    def insert_result(self, assessment_id: str, features):
        self.inserted = (assessment_id, features)
        return {"assessment_id": assessment_id}


def test_successful_completion_inserts_and_returns_result():
    service = MMSEGameService(FakeRepository())
    result = service.complete_game(ASSESSMENT_ID, build_request())
    assert result.assessment_id == ASSESSMENT_ID
    assert result.status == "completed"


def test_invalid_assessment_uuid():
    service = MMSEGameService(FakeRepository())
    with pytest.raises(InvalidAssessmentIdError):
        service.complete_game("not-a-uuid", build_request())


def test_assessment_not_found():
    service = MMSEGameService(FakeRepository(assessment_exists=False))
    with pytest.raises(AssessmentNotFoundError):
        service.complete_game(ASSESSMENT_ID, build_request())


def test_duplicate_completion():
    service = MMSEGameService(FakeRepository(result_exists=True))
    with pytest.raises(DuplicateCompletionError):
        service.complete_game(ASSESSMENT_ID, build_request())


def test_incomplete_game():
    request = build_request()
    request.events = [event for event in request.events if event.phase.value != "COMMAND"]
    service = MMSEGameService(FakeRepository())
    with pytest.raises(InvalidEventSequenceError):
        service.complete_game(ASSESSMENT_ID, request)
