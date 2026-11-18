import pytest

from app.games.memory.exceptions import (
    AssessmentNotFoundError,
    DuplicateCompletionError,
    InvalidEventSequenceError,
)
from app.games.memory.schemas import MemoryGameCompletionRequest
from app.games.memory.service import MemoryGameService
from tests.games.memory.fixtures import ASSESSMENT_ID, build_full_happy_path_events, default_confidence


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


def _request() -> MemoryGameCompletionRequest:
    return MemoryGameCompletionRequest(
        events=build_full_happy_path_events(), confidence=default_confidence()
    )


def test_successful_completion_inserts_and_returns_result():
    repo = FakeRepository()
    service = MemoryGameService(repo)
    result = service.complete_game(ASSESSMENT_ID, _request())
    assert result.assessment_id == ASSESSMENT_ID
    assert result.status == "completed"
    assert repo.inserted is not None
    assert repo.inserted[0] == ASSESSMENT_ID


def test_unknown_assessment_rejected():
    repo = FakeRepository(assessment_exists=False)
    service = MemoryGameService(repo)
    with pytest.raises(AssessmentNotFoundError):
        service.complete_game(ASSESSMENT_ID, _request())


def test_duplicate_completion_rejected():
    repo = FakeRepository(assessment_exists=True, result_exists=True)
    service = MemoryGameService(repo)
    with pytest.raises(DuplicateCompletionError):
        service.complete_game(ASSESSMENT_ID, _request())


def test_missing_required_phase_rejected():
    repo = FakeRepository()
    service = MemoryGameService(repo)
    events = [e for e in build_full_happy_path_events() if e.phase.value != "RECOGNITION"]
    request = MemoryGameCompletionRequest(events=events, confidence=default_confidence())
    with pytest.raises(InvalidEventSequenceError):
        service.complete_game(ASSESSMENT_ID, request)


def test_events_from_other_assessment_rejected():
    repo = FakeRepository()
    service = MemoryGameService(repo)
    events = build_full_happy_path_events()
    events[0] = events[0].model_copy(update={"assessment_id": "different-assessment"})
    request = MemoryGameCompletionRequest(events=events, confidence=default_confidence())
    with pytest.raises(InvalidEventSequenceError):
        service.complete_game(ASSESSMENT_ID, request)
