from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.mental_health.schemas import (
    GAD7Answers,
    GAD7ResultResponse,
    MentalHealthCompleteRequest,
    MentalHealthCompleteResponse,
    PHQ9Answers,
    PHQ9ResultResponse,
)


class MentalHealthAssessmentNotFoundError(ValueError):
    """Raised when the referenced assessment does not exist."""


class InvalidMentalHealthAssessmentIdError(ValueError):
    """Raised when assessment_id is not a UUID."""


@dataclass(frozen=True)
class ScoreResult:
    total_score: int
    severity: str
    evaluation_cutoff_met: bool


def calculate_phq9_score(answers: PHQ9Answers) -> int:
    return sum(answers.model_dump().values())


def calculate_gad7_score(answers: GAD7Answers) -> int:
    return sum(answers.model_dump().values())


def classify_phq9_score(total_score: int) -> str:
    if total_score <= 4:
        return "Minimal"
    if total_score <= 9:
        return "Mild"
    if total_score <= 14:
        return "Moderate"
    if total_score <= 19:
        return "Moderately severe"
    return "Severe"


def classify_gad7_score(total_score: int) -> str:
    if total_score <= 5:
        return "Mild"
    if total_score <= 10:
        return "Moderate"
    if total_score <= 14:
        return "Moderately severe"
    return "Severe"


class MentalHealthService:
    def __init__(self, repository):
        self._repository = repository

    def complete_screening(
        self,
        assessment_id: str,
        request: MentalHealthCompleteRequest,
    ) -> MentalHealthCompleteResponse:
        self._validate_assessment_id(assessment_id)
        if not self._repository.assessment_exists(assessment_id):
            raise MentalHealthAssessmentNotFoundError(
                f"assessment_id '{assessment_id}' does not exist."
            )

        if self._repository.phq9_result_exists(assessment_id) and self._repository.gad7_result_exists(
            assessment_id
        ):
            return self._build_response(
                assessment_id=assessment_id,
                status="already_completed",
                phq_row=self._repository.get_phq9_result(assessment_id),
                gad_row=self._repository.get_gad7_result(assessment_id),
            )

        phq_score = self._score_phq9(request.phq9)
        gad_score = self._score_gad7(request.gad7)

        if not self._repository.phq9_result_exists(assessment_id):
            self._repository.insert_phq9_result(
                {
                    "assessment_id": assessment_id,
                    **request.phq9.model_dump(),
                    "total_score": phq_score.total_score,
                    "severity": phq_score.severity,
                }
            )
        if not self._repository.gad7_result_exists(assessment_id):
            self._repository.insert_gad7_result(
                {
                    "assessment_id": assessment_id,
                    **request.gad7.model_dump(),
                    "total_score": gad_score.total_score,
                    "severity": gad_score.severity,
                }
            )

        return MentalHealthCompleteResponse(
            assessment_id=assessment_id,
            status="completed",
            phq9=PHQ9ResultResponse(**phq_score.__dict__),
            gad7=GAD7ResultResponse(**gad_score.__dict__),
        )

    @staticmethod
    def _validate_assessment_id(assessment_id: str) -> None:
        try:
            UUID(assessment_id)
        except ValueError as exc:
            raise InvalidMentalHealthAssessmentIdError(
                "assessment_id must be a valid UUID."
            ) from exc

    @staticmethod
    def _score_phq9(answers: PHQ9Answers) -> ScoreResult:
        total_score = calculate_phq9_score(answers)
        return ScoreResult(
            total_score=total_score,
            severity=classify_phq9_score(total_score),
            evaluation_cutoff_met=total_score >= 10,
        )

    @staticmethod
    def _score_gad7(answers: GAD7Answers) -> ScoreResult:
        total_score = calculate_gad7_score(answers)
        return ScoreResult(
            total_score=total_score,
            severity=classify_gad7_score(total_score),
            evaluation_cutoff_met=total_score >= 10,
        )

    def _build_response(
        self,
        *,
        assessment_id: str,
        status: str,
        phq_row: dict | None,
        gad_row: dict | None,
    ) -> MentalHealthCompleteResponse:
        if phq_row is None or gad_row is None:
            raise RuntimeError("Existing mental health results are incomplete.")
        return MentalHealthCompleteResponse(
            assessment_id=assessment_id,
            status=status,
            phq9=PHQ9ResultResponse(
                total_score=int(phq_row["total_score"]),
                severity=phq_row["severity"],
                evaluation_cutoff_met=int(phq_row["total_score"]) >= 10,
            ),
            gad7=GAD7ResultResponse(
                total_score=int(gad_row["total_score"]),
                severity=gad_row["severity"],
                evaluation_cutoff_met=int(gad_row["total_score"]) >= 10,
            ),
        )
