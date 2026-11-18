from __future__ import annotations

from typing import Any

try:
    from supabase import Client
except ImportError:  # pragma: no cover
    Client = Any

from app.ml.model1.exceptions import Model1SchemaNotReadyError

TABLE_NAME = "model1_results"


class Model1Repository:
    def __init__(self, client: Client):
        self._client = client

    def result_exists(self, assessment_id: str) -> bool:
        response = self._execute_table_query(
            self._client.table(TABLE_NAME)
            .select("model1_id")
            .eq("assessment_id", assessment_id)
            .limit(1)
        )
        return bool(response.data)

    def get_by_assessment(self, assessment_id: str) -> dict[str, Any] | None:
        response = self._execute_table_query(
            self._client.table(TABLE_NAME)
            .select("*")
            .eq("assessment_id", assessment_id)
            .limit(1)
        )
        return response.data[0] if response.data else None

    def insert_result(
        self,
        *,
        assessment_id: str,
        cognitive_performance_score: float,
        model_name: str,
        model_version: str,
        feature_vector: dict[str, float],
    ) -> dict[str, Any]:
        payload = {
            "assessment_id": assessment_id,
            "cognitive_performance_score": cognitive_performance_score,
            "model_name": model_name,
            "model_version": model_version,
            "feature_vector": feature_vector,
        }
        response = self._execute_table_query(self._client.table(TABLE_NAME).insert(payload))
        return response.data[0] if response.data else payload

    @staticmethod
    def _execute_table_query(query):
        try:
            return query.execute()
        except Exception as exc:
            message = str(exc)
            if "public.model1_results" in message or "model1_results" in message:
                raise Model1SchemaNotReadyError(
                    "Model 1 database table is missing in Supabase. Apply database/schema.sql so the model1_results table exists, then retry."
                ) from exc
            raise
