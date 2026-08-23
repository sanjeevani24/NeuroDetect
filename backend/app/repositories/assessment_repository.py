from __future__ import annotations

import uuid
from typing import Any

try:
    from supabase import Client
except ImportError:  # pragma: no cover - unit tests use fakes
    Client = Any


class AssessmentRepository:
    def __init__(self, client: Client):
        self._client = client

    def create_assessment_session(self) -> dict[str, str]:
        patient_id = str(uuid.uuid4())
        assessment_id = str(uuid.uuid4())

        self._client.table("patients").insert({"patient_id": patient_id}).execute()
        self._client.table("assessments").insert(
            {"assessment_id": assessment_id, "patient_id": patient_id}
        ).execute()

        return {
            "patient_id": patient_id,
            "assessment_id": assessment_id,
        }
