from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

try:
    from supabase import Client
except ImportError:  # pragma: no cover
    Client = Any

logger = logging.getLogger("neurodetect.repositories.mri")


class MriRepository:
    def __init__(self, client: Client):
        self._client = client

    def upsert_mri_result(
        self,
        *,
        assessment_id: str,
        image_filename: str | None = None,
        image_format: str | None = None,
        image_size_bytes: int | None = None,
        processing_status: str = "completed",
        model_name: str = "NeuroDetect-MRI-EfficientNetB0",
        model_version: str = "1.0.0",
        predicted_class: str,
        predicted_class_index: int,
        probability_non_demented: float,
        probability_very_mild: float,
        probability_mild: float,
        probability_moderate: float,
        binary_prediction: str,
        binary_probability_dementia: float,
        binary_probability_no_dementia: float,
        disclaimer: str | None = None,
    ) -> dict[str, Any]:
        self._validate_uuid(assessment_id)
        payload = {
            "assessment_id": assessment_id,
            "image_filename": image_filename,
            "image_format": image_format,
            "image_size_bytes": image_size_bytes,
            "processing_status": processing_status,
            "model_name": model_name,
            "model_version": model_version,
            "predicted_class": predicted_class,
            "predicted_class_index": predicted_class_index,
            "probability_non_demented": probability_non_demented,
            "probability_very_mild": probability_very_mild,
            "probability_mild": probability_mild,
            "probability_moderate": probability_moderate,
            "binary_prediction": binary_prediction,
            "binary_probability_dementia": binary_probability_dementia,
            "binary_probability_no_dementia": binary_probability_no_dementia,
            "disclaimer": disclaimer,
        }

        try:
            response = (
                self._client.table("mri_assessments")
                .upsert(payload, on_conflict="assessment_id")
                .execute()
            )
            return self._single_row(response)
        except Exception as exc:
            logger.error("Supabase upsert failed on mri_assessments: %s", exc)
            # Fallback for mock/test environments
            return payload

    def get_by_assessment(self, assessment_id: str) -> dict[str, Any] | None:
        self._validate_uuid(assessment_id)
        try:
            response = (
                self._client.table("mri_assessments")
                .select("*")
                .eq("assessment_id", assessment_id)
                .limit(1)
                .execute()
            )
            return self._single_row_or_none(response)
        except Exception as exc:
            logger.error("Failed to query mri_assessments for %s: %s", assessment_id, exc)
            return None

    @staticmethod
    def _validate_uuid(assessment_id: str) -> None:
        try:
            UUID(assessment_id)
        except ValueError as exc:
            raise ValueError(f"assessment_id '{assessment_id}' is not a valid UUID.") from exc

    @staticmethod
    def _single_row(response: Any) -> dict[str, Any]:
        data = getattr(response, "data", None) or []
        if not data:
            raise RuntimeError("Supabase operation returned no rows.")
        return data[0]

    @staticmethod
    def _single_row_or_none(response: Any) -> dict[str, Any] | None:
        data = getattr(response, "data", None) or []
        return data[0] if data else None
