from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from supabase import Client

from app.core.config import get_settings
from app.core.database import get_supabase_client
from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.speech_repository import SpeechRepository, SpeechSchemaNotReadyError
from app.speech.audio_converter import FFmpegNotFoundError
from app.speech.config import MODEL3_DISCLAIMER
from app.speech.inference import Model3InferenceError
from app.speech.schemas import SpeechResultResponse, SpeechUploadResponse
from app.speech.service import AssessmentNotFoundError, InvalidAudioError, SpeechService
from app.speech.transcription_service import TranscriptionError

logger = logging.getLogger("neurodetect.speech.router")

router = APIRouter(prefix="/api/assessments", tags=["speech"])


def get_speech_service(client: Client = Depends(get_supabase_client)) -> SpeechService:
    return SpeechService(
        assessment_repository=AssessmentRepository(client),
        speech_repository=SpeechRepository(client),
    )


@router.post(
    "/{assessment_id}/speech/upload",
    response_model=SpeechUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_speech_recording(
    assessment_id: str,
    audio: UploadFile = File(...),
    manual_transcript: str | None = Form(None),
    service: SpeechService = Depends(get_speech_service),
) -> SpeechUploadResponse:
    """
    Receives participant's speech audio, validates it, runs transcription and
    Model 3 inference, and persists the result.
    """
    try:
        UUID(assessment_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="assessment_id must be a valid UUID.",
        ) from exc

    if not audio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio file was uploaded.",
        )

    try:
        audio_bytes = await audio.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded audio stream.",
        ) from exc

    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio recording is empty (0 bytes).",
        )

    try:
        result = await service.process_speech_upload(
            assessment_id=assessment_id,
            audio_bytes=audio_bytes,
            filename=audio.filename or "recording.wav",
            content_type=audio.content_type,
            manual_transcript=manual_transcript,
        )
        return SpeechUploadResponse(**result)
    except AssessmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        ) from None
    except InvalidAudioError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from None
    except FFmpegNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from None
    except TranscriptionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Speech transcription failed: {exc}",
        ) from None
    except Model3InferenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model 3 inference failed: {exc}",
        ) from None
    except SpeechSchemaNotReadyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from None
    except Exception as exc:
        detail = str(exc) if get_settings().ENVIRONMENT == "development" else "Internal speech processing error."
        logger.exception("Unexpected error during speech upload: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from None


@router.get("/{assessment_id}/speech", response_model=SpeechResultResponse)
def get_speech_assessment_result(
    assessment_id: str,
    service: SpeechService = Depends(get_speech_service),
) -> SpeechResultResponse:
    """Retrieves the stored speech assessment result for a session."""
    try:
        UUID(assessment_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="assessment_id must be a valid UUID.",
        ) from exc

    try:
        record = service.get_speech_result(assessment_id)
    except SpeechSchemaNotReadyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from None
    except Exception as exc:
        detail = str(exc) if get_settings().ENVIRONMENT == "development" else "Unable to load speech result."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from None

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Speech result not found for this assessment.",
        )

    p_hc = record.get("probability_hc") if record.get("probability_hc") is not None else record.get("hc_probability")
    p_mci = record.get("probability_mci") if record.get("probability_mci") is not None else record.get("mci_probability")
    p_dem = record.get("probability_dementia") if record.get("probability_dementia") is not None else record.get("dementia_probability")

    probabilities = None
    if p_hc is not None:
        probabilities = {
            "HC": float(p_hc),
            "MCI": float(p_mci),
            "Dementia": float(p_dem),
        }

    return SpeechResultResponse(
        assessment_id=record["assessment_id"],
        status=record.get("inference_status") or "completed",
        speech_id=record.get("speech_id"),
        transcript=record.get("transcript"),
        transcription_status=record.get("transcription_status") or "pending",
        transcription_engine=record.get("transcription_engine") or "unknown",
        inference_status=record.get("inference_status") or "pending",
        predicted_class=record.get("predicted_class"),
        probability_hc=float(p_hc) if p_hc is not None else None,
        hc_probability=float(p_hc) if p_hc is not None else None,
        probability_mci=float(p_mci) if p_mci is not None else None,
        mci_probability=float(p_mci) if p_mci is not None else None,
        probability_dementia=float(p_dem) if p_dem is not None else None,
        dementia_probability=float(p_dem) if p_dem is not None else None,
        probabilities=probabilities,
        branch_probabilities=record.get("branch_probabilities") or {},
        components_used=record.get("components_used") or [],
        model_name=record.get("model_name") or "NeuroDetect Model 3 - PROCESS-2 CTD Classifier",
        model_version=record.get("model_version"),
        disclaimer=record.get("disclaimer") or MODEL3_DISCLAIMER,
        error_message=record.get("error_message"),
        created_at=record.get("created_at"),
        updated_at=record.get("updated_at"),
    )
