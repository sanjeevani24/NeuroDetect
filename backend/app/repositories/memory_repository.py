"""
Data-access layer for the Memory Recall game.

Responsibilities ONLY:
    - check whether an assessment exists
    - check whether a memory_results row already exists for an assessment
    - insert a new memory_results row

No feature logic and no request/response shaping lives here.
"""
from __future__ import annotations

from typing import Any

try:
    from supabase import Client
except ImportError:  # pragma: no cover - unit tests use fakes
    Client = Any

from app.games.memory.features import ExtractedFeatures


class MemoryRepository:
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
            self._client.table("memory_results")
            .select("memory_id")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        )
        return len(response.data or []) > 0

    def insert_result(self, assessment_id: str, features: ExtractedFeatures) -> dict[str, Any]:
        payload = {
            "assessment_id": assessment_id,
            "immediate_recall_accuracy": features.immediate_recall_accuracy,
            "delayed_recall_accuracy": features.delayed_recall_accuracy,
            "recognition_accuracy": features.recognition_accuracy,
            "recall_decay_rate": features.recall_decay_rate,
            "recall_latency": features.recall_latency,
            "omission_errors": features.omission_errors,
            "intrusion_errors": features.intrusion_errors,
            "sequence_recall_accuracy": features.sequence_recall_accuracy,
            "hesitation_duration": features.hesitation_duration,
            "retry_frequency": features.retry_frequency,
            "confidence_variability": features.confidence_variability,
            "completion_time": features.completion_time,
            "memory_consistency_trend": features.memory_consistency_trend,
        }
        response = self._client.table("memory_results").insert(payload).execute()
        rows = response.data or []
        return rows[0] if rows else payload
