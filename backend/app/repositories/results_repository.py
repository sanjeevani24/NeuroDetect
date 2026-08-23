from __future__ import annotations

from typing import Any

try:
    from supabase import Client
except ImportError:  # pragma: no cover - unit tests use fakes
    Client = Any

from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.mental_health_repository import MentalHealthRepository
from app.repositories.model1_repository import Model1Repository


class ResultsRepository:
    def __init__(self, client: Client):
        self._assessment_repository = AssessmentRepository(client)
        self._mental_health_repository = MentalHealthRepository(client)
        self._model1_repository = Model1Repository(client)

    def get_assessment_session(self, assessment_id: str) -> dict[str, Any] | None:
        return self._assessment_repository.get_assessment_session(assessment_id)

    def get_phq9_result(self, assessment_id: str) -> dict[str, Any] | None:
        return self._mental_health_repository.get_phq9_result(assessment_id)

    def get_gad7_result(self, assessment_id: str) -> dict[str, Any] | None:
        return self._mental_health_repository.get_gad7_result(assessment_id)

    def get_model1_result(self, assessment_id: str) -> dict[str, Any] | None:
        return self._model1_repository.get_by_assessment(assessment_id)
