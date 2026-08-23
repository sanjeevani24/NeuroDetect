"""
Repository for the nback_results table.

Mirrors the Memory Recall repository pattern: a thin wrapper around the
Supabase client, no business logic. Feature computation happens upstream in
app.games.nback.service — this module only persists an already-validated
NBackFeatures payload.
"""
from __future__ import annotations

from typing import Any, Optional

try:
    from supabase import Client
except ImportError:  # pragma: no cover - unit tests use fakes
    Client = Any

from app.games.nback.schemas import NBackFeatures

TABLE_NAME = "nback_results"


class NBackRepository:
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
            .select("nback_id")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        )
        return bool(response.data)

    def insert_result(self, assessment_id: str, features: NBackFeatures) -> dict[str, Any]:
        payload = {
            "assessment_id": assessment_id,
            **features.model_dump(),
        }
        response = self._client.table(TABLE_NAME).insert(payload).execute()
        return response.data[0] if response.data else payload

    def get_by_assessment(self, assessment_id: str) -> Optional[dict[str, Any]]:
        response = (
            self._client.table(TABLE_NAME)
            .select("*")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None
