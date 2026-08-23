from __future__ import annotations

from typing import Any
from uuid import UUID

try:
    from supabase import Client
except ImportError:  # pragma: no cover - unit tests use fakes
    Client = Any


class AssessmentRepository:
    def __init__(self, client: Client):
        self._client = client

    def create_assessment_session(
        self,
        *,
        full_name: str,
        age: int,
        sex: str,
        education_years: int,
    ) -> dict[str, Any]:
        patient_row = self._single_row(
            self._client.table("patients")
            .insert(
                {
                    "full_name": full_name,
                    "age": age,
                    "sex": sex,
                    "education_years": education_years,
                }
            )
            .execute()
        )
        assessment_row = self._single_row(
            self._client.table("assessments")
            .insert({"patient_id": patient_row["patient_id"]})
            .execute()
        )

        return self.get_assessment_session(str(assessment_row["assessment_id"]))

    def get_assessment_session(self, assessment_id: str) -> dict[str, Any] | None:
        assessment_row = self._single_row_or_none(
            self._client.table("assessments")
            .select("assessment_id, patient_id")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        )
        if assessment_row is None:
            return None

        patient_row = self._single_row_or_none(
            self._client.table("patients")
            .select("patient_id, full_name, age, sex, education_years")
            .eq("patient_id", assessment_row["patient_id"])
            .limit(1)
            .execute()
        )
        if patient_row is None:
            return None

        completed_stages = self._completed_stages(assessment_id)
        return {
            "patient_id": str(patient_row["patient_id"]),
            "assessment_id": str(assessment_row["assessment_id"]),
            "full_name": patient_row["full_name"],
            "age": int(patient_row["age"]),
            "sex": patient_row["sex"],
            "education_years": int(patient_row["education_years"]),
            "current_stage": self._current_stage(completed_stages),
            "completed_stages": completed_stages,
        }

    def assessment_exists(self, assessment_id: str) -> bool:
        try:
            UUID(assessment_id)
        except ValueError:
            return False
        row = self._single_row_or_none(
            self._client.table("assessments")
            .select("assessment_id")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        )
        return row is not None

    def _completed_stages(self, assessment_id: str) -> list[str]:
        completed: list[str] = []
        if self._table_has_assessment("phq9_results", assessment_id) and self._table_has_assessment(
            "gad7_results", assessment_id
        ):
            completed.append("PHQ_GAD")
        if self._table_has_assessment("mmse_results", assessment_id):
            completed.append("MMSE")
        if self._table_has_assessment("memory_results", assessment_id):
            completed.append("MEMORY")
        if self._table_has_assessment("nback_results", assessment_id):
            completed.append("NBACK")
        if self._table_has_assessment("boston_naming_results", assessment_id):
            completed.append("BOSTON_NAMING")
        if self._table_has_assessment("trail_making_results", assessment_id):
            completed.append("TRAIL_MAKING")
        return completed

    def _current_stage(self, completed_stages: list[str]) -> str:
        if "PHQ_GAD" not in completed_stages:
            return "PHQ_GAD"
        if "MMSE" not in completed_stages:
            return "COGNITIVE"
        if "MEMORY" not in completed_stages:
            return "MEMORY"
        if "NBACK" not in completed_stages:
            return "NBACK"
        if "BOSTON_NAMING" not in completed_stages:
            return "BOSTON_NAMING"
        if "TRAIL_MAKING" not in completed_stages:
            return "TRAIL_MAKING"
        return "RESULTS"

    def _table_has_assessment(self, table_name: str, assessment_id: str) -> bool:
        row = self._single_row_or_none(
            self._client.table(table_name)
            .select("assessment_id")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        )
        return row is not None

    @staticmethod
    def _single_row(response: Any) -> dict[str, Any]:
        data = getattr(response, "data", None) or []
        if not data:
            raise RuntimeError("Supabase insert returned no rows.")
        return data[0]

    @staticmethod
    def _single_row_or_none(response: Any) -> dict[str, Any] | None:
        data = getattr(response, "data", None) or []
        return data[0] if data else None
