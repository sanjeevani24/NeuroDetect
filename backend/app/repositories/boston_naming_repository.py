from __future__ import annotations

from typing import Any

try:
    from supabase import Client
except ImportError:  # pragma: no cover
    Client = Any

from app.games.boston_naming.schemas import BostonNamingFeatures

TABLE_NAME = "boston_naming_results"


class BostonNamingRepository:
    def __init__(self, client: Client):
        self._client = client

    def assessment_exists(self, assessment_id: str) -> bool:
        response = (
            self._client.table("assessments")
            .select("assessment_id")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        )
        return bool(response.data)

    def result_exists(self, assessment_id: str) -> bool:
        response = (
            self._client.table(TABLE_NAME)
            .select("boston_id")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        )
        return bool(response.data)

    def insert_result(self, assessment_id: str, features: BostonNamingFeatures) -> dict[str, Any]:
        payload = {"assessment_id": assessment_id, **features.model_dump()}
        response = self._client.table(TABLE_NAME).insert(payload).execute()
        return response.data[0] if response.data else payload

    def get_by_assessment(self, assessment_id: str) -> dict[str, Any] | None:
        response = (
            self._client.table(TABLE_NAME)
            .select("*")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None
