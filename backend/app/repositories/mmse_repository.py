from __future__ import annotations

from typing import Any

try:
    from supabase import Client
except ImportError:  # pragma: no cover - unit tests use fakes
    Client = Any

from app.games.mmse.features import ExtractedMMSEFeatures


class MMSERepository:
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
        return len(response.data or []) > 0

    def result_exists(self, assessment_id: str) -> bool:
        response = (
            self._client.table("mmse_results")
            .select("mmse_id")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        )
        return len(response.data or []) > 0

    def insert_result(self, assessment_id: str, features: ExtractedMMSEFeatures) -> dict[str, Any]:
        payload = {
            "assessment_id": assessment_id,
            "orientation_accuracy": features.orientation_accuracy,
            "registration_accuracy": features.registration_accuracy,
            "attention_accuracy": features.attention_accuracy,
            "serial7_accuracy": features.serial7_accuracy,
            "delayed_recall_accuracy": features.delayed_recall_accuracy,
            "language_accuracy": features.language_accuracy,
            "command_following_accuracy": features.command_following_accuracy,
            "response_latency": features.response_latency,
            "latency_variability": features.latency_variability,
            "omission_errors": features.omission_errors,
            "intrusion_errors": features.intrusion_errors,
            "correction_frequency": features.correction_frequency,
            "completion_time": features.completion_time,
            "performance_consistency": features.performance_consistency,
        }
        response = self._client.table("mmse_results").insert(payload).execute()
        rows = response.data or []
        return rows[0] if rows else payload

    def get_by_assessment(self, assessment_id: str) -> dict[str, Any] | None:
        response = (
            self._client.table("mmse_results")
            .select("*")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None
