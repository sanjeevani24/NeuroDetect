import pytest

from app.mental_health.schemas import GAD7Answers, MentalHealthCompleteRequest, PHQ9Answers
from app.mental_health.service import (
    InvalidMentalHealthAssessmentIdError,
    MentalHealthAssessmentNotFoundError,
    MentalHealthService,
    calculate_gad7_score,
    calculate_phq9_score,
    classify_gad7_score,
    classify_phq9_score,
)


ASSESSMENT_ID = "22222222-2222-4222-8222-222222222222"


class FakeRepository:
    def __init__(
        self,
        *,
        assessment_exists: bool = True,
        phq_exists: bool = False,
        gad_exists: bool = False,
    ):
        self._assessment_exists = assessment_exists
        self._phq_exists = phq_exists
        self._gad_exists = gad_exists
        self.inserted_phq = None
        self.inserted_gad = None

    def assessment_exists(self, assessment_id: str) -> bool:
        return self._assessment_exists

    def phq9_result_exists(self, assessment_id: str) -> bool:
        return self._phq_exists

    def gad7_result_exists(self, assessment_id: str) -> bool:
        return self._gad_exists

    def insert_phq9_result(self, payload):
        self.inserted_phq = payload
        self._phq_exists = True
        return payload

    def insert_gad7_result(self, payload):
        self.inserted_gad = payload
        self._gad_exists = True
        return payload

    def get_phq9_result(self, assessment_id: str):
        return self.inserted_phq or {
            "assessment_id": assessment_id,
            "total_score": 12,
            "severity": "Moderate",
        }

    def get_gad7_result(self, assessment_id: str):
        return self.inserted_gad or {
            "assessment_id": assessment_id,
            "total_score": 11,
            "severity": "Moderately severe",
        }


def build_request() -> MentalHealthCompleteRequest:
    return MentalHealthCompleteRequest(
        phq9=PHQ9Answers(q1=1, q2=2, q3=1, q4=2, q5=1, q6=1, q7=1, q8=0, q9=0),
        gad7=GAD7Answers(q1=2, q2=2, q3=2, q4=1, q5=1, q6=1, q7=0),
    )


def test_calculate_phq9_score():
    total = calculate_phq9_score(build_request().phq9)
    assert total == 9
    assert classify_phq9_score(total) == "Mild"


def test_calculate_gad7_score():
    total = calculate_gad7_score(build_request().gad7)
    assert total == 9
    assert classify_gad7_score(total) == "Moderate"


def test_complete_screening_persists_scores():
    repository = FakeRepository()
    service = MentalHealthService(repository)

    result = service.complete_screening(ASSESSMENT_ID, build_request())

    assert result.status == "completed"
    assert result.assessment_id == ASSESSMENT_ID
    assert result.phq9.total_score == 9
    assert result.gad7.total_score == 9
    assert repository.inserted_phq is not None
    assert repository.inserted_gad is not None
    assert repository.inserted_phq["severity"] == "Mild"
    assert repository.inserted_gad["severity"] == "Moderate"


def test_duplicate_completion_returns_existing_scores():
    repository = FakeRepository(phq_exists=True, gad_exists=True)
    service = MentalHealthService(repository)

    result = service.complete_screening(ASSESSMENT_ID, build_request())

    assert result.status == "already_completed"
    assert result.phq9.total_score == 12
    assert result.gad7.total_score == 11


def test_invalid_assessment_id_rejected():
    service = MentalHealthService(FakeRepository())
    with pytest.raises(InvalidMentalHealthAssessmentIdError):
        service.complete_screening("not-a-uuid", build_request())


def test_unknown_assessment_rejected():
    service = MentalHealthService(FakeRepository(assessment_exists=False))
    with pytest.raises(MentalHealthAssessmentNotFoundError):
        service.complete_screening(ASSESSMENT_ID, build_request())
