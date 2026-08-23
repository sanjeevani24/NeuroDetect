from __future__ import annotations

from typing import Any

try:
    from supabase import Client
except ImportError:  # pragma: no cover - unit tests use fakes
    Client = Any


class MentalHealthRepository:
    def __init__(self, client: Client):
        self._client = client

    def assessment_exists(self, assessment_id: str) -> bool:
        return self._single_row_or_none(
            self._client.table("assessments")
            .select("assessment_id")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        ) is not None

    def phq9_result_exists(self, assessment_id: str) -> bool:
        return self._table_has_assessment("phq9_results", assessment_id)

    def gad7_result_exists(self, assessment_id: str) -> bool:
        return self._table_has_assessment("gad7_results", assessment_id)

    def insert_phq9_result(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._single_row(self._client.table("phq9_results").insert(payload).execute())

    def insert_gad7_result(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._single_row(self._client.table("gad7_results").insert(payload).execute())

    def get_phq9_result(self, assessment_id: str) -> dict[str, Any] | None:
        return self._single_row_or_none(
            self._client.table("phq9_results")
            .select("*")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        )

    def get_gad7_result(self, assessment_id: str) -> dict[str, Any] | None:
        return self._single_row_or_none(
            self._client.table("gad7_results")
            .select("*")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        )

    def _table_has_assessment(self, table_name: str, assessment_id: str) -> bool:
        return self._single_row_or_none(
            self._client.table(table_name)
            .select("assessment_id")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        ) is not None

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
