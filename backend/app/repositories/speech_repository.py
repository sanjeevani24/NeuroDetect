from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid

try:
    from supabase import Client
except ImportError:  # pragma: no cover
    Client = Any

SPEECH_ASSESSMENTS_TABLE = "speech_assessments"
MODEL3_RESULTS_TABLE = "model3_results"
LEGACY_TABLE = "speech_results"


class SpeechSchemaNotReadyError(Exception):
    """Raised when the speech_assessments or model3_results table is not available in Supabase."""


class SpeechRepository:
    def __init__(self, client: Client):
        self._client = client

    def get_speech_assessment(self, assessment_id: str) -> dict[str, Any] | None:
        """Retrieves row from speech_assessments table."""
        response = self._execute_table_query(
            self._client.table(SPEECH_ASSESSMENTS_TABLE)
            .select("*")
            .eq("assessment_id", assessment_id)
            .limit(1)
        )
        data = getattr(response, "data", None) or []
        if data:
            return data[0]

        # Fallback to legacy single table if present
        try:
            legacy_resp = self._client.table(LEGACY_TABLE).select("*").eq("assessment_id", assessment_id).limit(1).execute()
            legacy_data = getattr(legacy_resp, "data", None) or []
            if legacy_data:
                return legacy_data[0]
        except Exception:
            pass

        return None

    def get_model3_result(self, assessment_id: str) -> dict[str, Any] | None:
        """Retrieves row from model3_results table."""
        response = self._execute_table_query(
            self._client.table(MODEL3_RESULTS_TABLE)
            .select("*")
            .eq("assessment_id", assessment_id)
            .limit(1)
        )
        data = getattr(response, "data", None) or []
        if data:
            return data[0]

        # Fallback to legacy single table if present
        try:
            legacy_resp = self._client.table(LEGACY_TABLE).select("*").eq("assessment_id", assessment_id).limit(1).execute()
            legacy_data = getattr(legacy_resp, "data", None) or []
            if legacy_data:
                row = legacy_data[0]
                return {
                    "model3_id": row.get("speech_id"),
                    "speech_id": row.get("speech_id"),
                    "assessment_id": row.get("assessment_id"),
                    "predicted_class": row.get("predicted_class"),
                    "probability_hc": row.get("hc_probability") or row.get("probability_hc"),
                    "probability_mci": row.get("mci_probability") or row.get("probability_mci"),
                    "probability_dementia": row.get("dementia_probability") or row.get("probability_dementia"),
                    "branch_probabilities": row.get("branch_probabilities") or {},
                    "components_used": row.get("components_used") or [],
                    "model_name": "NeuroDetect Model 3 - PROCESS-2 CTD Classifier",
                    "model_version": row.get("model_version"),
                    "inference_status": row.get("inference_status"),
                    "disclaimer": row.get("disclaimer"),
                    "error_message": row.get("error_message"),
                    "created_at": row.get("created_at"),
                }
        except Exception:
            pass

        return None

    def get_by_assessment(self, assessment_id: str) -> dict[str, Any] | None:
        """
        Returns unified speech assessment & Model 3 prediction record.
        Maintains compatibility across both probability_hc and hc_probability naming conventions.
        """
        speech_row = self.get_speech_assessment(assessment_id)
        model3_row = self.get_model3_result(assessment_id)

        if not speech_row and not model3_row:
            return None

        combined: dict[str, Any] = {}
        if speech_row:
            combined.update(speech_row)
        if model3_row:
            combined.update(model3_row)

        # Standardize probability fields for both naming conventions
        prob_hc = combined.get("probability_hc") if combined.get("probability_hc") is not None else combined.get("hc_probability")
        prob_mci = combined.get("probability_mci") if combined.get("probability_mci") is not None else combined.get("mci_probability")
        prob_dem = combined.get("probability_dementia") if combined.get("probability_dementia") is not None else combined.get("dementia_probability")

        combined["probability_hc"] = prob_hc
        combined["hc_probability"] = prob_hc
        combined["probability_mci"] = prob_mci
        combined["mci_probability"] = prob_mci
        combined["probability_dementia"] = prob_dem
        combined["dementia_probability"] = prob_dem

        return combined

    def upsert_result(
        self,
        *,
        assessment_id: str,
        audio_storage_path: str | None = None,
        transcript: str | None = None,
        transcription_status: str = "pending",
        transcription_engine: str = "pluggable_local_asr",
        audio_duration_seconds: float | None = None,
        audio_format: str | None = None,
        inference_status: str = "pending",
        predicted_class: str | None = None,
        probability_hc: float | None = None,
        hc_probability: float | None = None,
        probability_mci: float | None = None,
        mci_probability: float | None = None,
        probability_dementia: float | None = None,
        dementia_probability: float | None = None,
        branch_probabilities: dict[str, Any] | None = None,
        components_used: list[str] | None = None,
        model_name: str = "NeuroDetect Model 3 - PROCESS-2 CTD Classifier",
        model_version: str | None = None,
        disclaimer: str | None = None,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        """
        Persists speech assessment metadata to `speech_assessments` and Model 3
        predictions to `model3_results`.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        resolved_hc = probability_hc if probability_hc is not None else hc_probability
        resolved_mci = probability_mci if probability_mci is not None else mci_probability
        resolved_dem = probability_dementia if probability_dementia is not None else dementia_probability

        # 1. Upsert speech_assessments
        existing_speech = self.get_speech_assessment(assessment_id)
        speech_id = existing_speech.get("speech_id") if existing_speech else str(uuid.uuid4())

        speech_payload = {
            "speech_id": speech_id,
            "assessment_id": assessment_id,
            "task_type": "cookie_theft",
            "audio_storage_path": audio_storage_path,
            "transcript": transcript,
            "processing_status": transcription_status,
            "transcription_status": transcription_status,
            "transcription_engine": transcription_engine,
            "audio_duration_seconds": audio_duration_seconds,
            "duration_seconds": audio_duration_seconds,
            "audio_format": audio_format,
            "mime_type": f"audio/{audio_format}" if audio_format else "audio/wav",
            "model_name": model_name,
            "model_version": model_version,
            "predicted_class": predicted_class,
            "probability_hc": resolved_hc,
            "probability_mci": resolved_mci,
            "probability_dementia": resolved_dem,
            "updated_at": now_iso,
        }

        if existing_speech:
            self._execute_table_query(
                self._client.table(SPEECH_ASSESSMENTS_TABLE)
                .update(speech_payload)
                .eq("assessment_id", assessment_id)
            )
        else:
            speech_payload["created_at"] = now_iso
            self._execute_table_query(
                self._client.table(SPEECH_ASSESSMENTS_TABLE).insert(speech_payload)
            )

        # 2. Upsert model3_results
        existing_model3 = self.get_model3_result(assessment_id)
        model3_id = existing_model3.get("model3_id") if existing_model3 else str(uuid.uuid4())

        model3_payload = {
            "model3_id": model3_id,
            "speech_id": speech_id,
            "assessment_id": assessment_id,
            "predicted_class": predicted_class,
            "probability_hc": resolved_hc,
            "probability_mci": resolved_mci,
            "probability_dementia": resolved_dem,
            "branch_probabilities": branch_probabilities or {},
            "components_used": components_used or [],
            "model_name": model_name,
            "model_version": model_version,
            "inference_status": inference_status,
            "disclaimer": disclaimer,
            "error_message": error_message,
            "updated_at": now_iso,
        }

        if existing_model3:
            self._execute_table_query(
                self._client.table(MODEL3_RESULTS_TABLE)
                .update(model3_payload)
                .eq("assessment_id", assessment_id)
            )
        else:
            model3_payload["created_at"] = now_iso
            self._execute_table_query(
                self._client.table(MODEL3_RESULTS_TABLE).insert(model3_payload)
            )

        return self.get_by_assessment(assessment_id) or {**speech_payload, **model3_payload}

    @staticmethod
    def _execute_table_query(query):
        try:
            return query.execute()
        except Exception as exc:
            message = str(exc)
            if "speech_assessments" in message or "model3_results" in message or "speech_results" in message:
                raise SpeechSchemaNotReadyError(
                    "Speech database tables missing in Supabase. Apply database/speech_and_model3_schema.sql, then retry."
                ) from exc
            raise
