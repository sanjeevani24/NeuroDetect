from __future__ import annotations

from typing import Any

try:
    from supabase import Client
except ImportError:  # pragma: no cover
    Client = Any

from app.games.trail_making.schemas import TrailMakingFeatures, TrailMakingTelemetryEvent


RESULTS_TABLE = "trail_making_results"
EVENTS_TABLE = "trail_making_events"


class TrailMakingRepository:
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
            self._client.table(RESULTS_TABLE)
            .select("trail_id")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        )
        return bool(response.data)

    def insert_result(self, assessment_id: str, game_session_id: str, features: TrailMakingFeatures) -> dict[str, Any]:
        payload = {
            "assessment_id": assessment_id,
            "game_session_id": game_session_id,
            **features.model_dump(),
        }
        response = self._client.table(RESULTS_TABLE).insert(payload).execute()
        return response.data[0] if response.data else payload

    def insert_events(self, events: list[TrailMakingTelemetryEvent]) -> None:
        payloads = [
            {
                "event_id": event.event_id,
                "assessment_id": event.assessment_id,
                "game_session_id": event.game_session_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "relative_time_ms": event.relative_time_ms,
                "node_id": event.node_id,
                "node_label": event.node_label,
                "node_type": event.node_type.value if event.node_type else None,
                "sequence_index": event.sequence_index,
                "expected_sequence_index": event.expected_sequence_index,
                "x": event.x,
                "y": event.y,
                "pointer_x": event.pointer_x,
                "pointer_y": event.pointer_y,
                "was_correct": event.was_correct,
                "error_type": event.error_type.value if event.error_type else None,
                "event_payload": event.event_payload,
            }
            for event in events
        ]
        if payloads:
            self._client.table(EVENTS_TABLE).insert(payloads).execute()

    def get_by_assessment(self, assessment_id: str) -> dict[str, Any] | None:
        response = (
            self._client.table(RESULTS_TABLE)
            .select("*")
            .eq("assessment_id", assessment_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None
