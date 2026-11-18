"""
Speech Assessment Service for NeuroDetect.

Orchestrates audio validation, temporary file storage, transcription,
Model 3 inference, and Supabase result persistence.
"""
from __future__ import annotations

import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

import numpy as np
import soundfile as sf

from app.repositories.assessment_repository import AssessmentRepository
from app.repositories.speech_repository import SpeechRepository
from app.speech.audio_converter import (
    AudioConversionError,
    FFmpegNotFoundError,
    convert_to_pcm_wav,
)
from app.speech.config import (
    ASR_VERIFICATION_NOTICE,
    MAX_AUDIO_SIZE_BYTES,
    MAX_DURATION_SECONDS,
    MIN_DURATION_SECONDS,
    MODEL3_DISCLAIMER,
)
from app.speech.inference import Model3InferenceError, Model3Manager, get_model3_manager
from app.speech.transcription_service import (
    BaseTranscriptionService,
    EmptyTranscriptError,
    TranscriptionError,
    get_transcription_service,
)

logger = logging.getLogger("neurodetect.speech.service")


def clean_transcript(text: Optional[str]) -> str:
    """
    Normalizes transcript according to Model 3 preprocessing requirements:
    strips bracketed tokens ([...], <...>, {...}), collapses whitespace, and trims.
    """
    if not text:
        return ""
    t = re.sub(r"\[[^\]]*\]|<[^>]*>|\{[^}]*\}", " ", str(text))
    return re.sub(r"\s+", " ", t).strip()


class AssessmentNotFoundError(Exception):
    """Raised when assessment does not exist."""


class InvalidAudioError(Exception):
    """Raised when uploaded audio is corrupt, empty, unsupported, or too short."""


class SpeechService:
    def __init__(
        self,
        assessment_repository: AssessmentRepository,
        speech_repository: SpeechRepository,
        transcription_service: Optional[BaseTranscriptionService] = None,
        model3_manager: Optional[Model3Manager] = None,
    ):
        self._assessment_repo = assessment_repository
        self._speech_repo = speech_repository
        self._transcription_service = transcription_service or get_transcription_service()
        self._model3_manager = model3_manager or get_model3_manager()

    def get_speech_result(self, assessment_id: str) -> Optional[dict[str, Any]]:
        self._validate_uuid(assessment_id)
        return self._speech_repo.get_by_assessment(assessment_id)

    async def process_speech_upload(
        self,
        *,
        assessment_id: str,
        audio_bytes: bytes,
        filename: str = "recording.wav",
        content_type: Optional[str] = None,
        manual_transcript: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Validates audio, converts browser recording to PCM WAV via FFmpeg,
        transcribes, executes Model 3 inference, and persists results.
        Cleans up all temporary files (both raw and converted) in all execution paths.
        """
        self._validate_uuid(assessment_id)

        # 1. Confirm assessment session exists
        if not self._assessment_repo.assessment_exists(assessment_id):
            logger.warning("Upload rejected: assessment_id %s not found", assessment_id)
            raise AssessmentNotFoundError("Assessment not found.")

        # 2. Validate audio size
        if not audio_bytes or len(audio_bytes) == 0:
            raise InvalidAudioError("Recorded audio is empty (0 bytes).")
        if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
            raise InvalidAudioError(f"Audio file exceeds maximum size limit of {MAX_AUDIO_SIZE_BYTES // (1024 * 1024)} MB.")

        # Determine input extension
        ext = Path(filename).suffix.lower()
        if not ext:
            if content_type and "webm" in content_type:
                ext = ".webm"
            elif content_type and ("mp4" in content_type or "m4a" in content_type):
                ext = ".mp4"
            elif content_type and "ogg" in content_type:
                ext = ".ogg"
            else:
                ext = ".wav"

        temp_raw_file: Optional[str] = None
        temp_wav_file: Optional[str] = None

        try:
            # 3. Create secure temporary file for uploaded bytes
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(audio_bytes)
                temp_raw_file = tmp.name

            # 4. Create destination path for converted PCM WAV
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                temp_wav_file = tmp_wav.name

            # Convert browser-recorded audio (WebM, Ogg, MP4, etc.) to standard PCM WAV
            try:
                convert_to_pcm_wav(temp_raw_file, temp_wav_file)
            except AudioConversionError as exc:
                logger.error("Audio decoding/conversion failed: %s", exc)
                raise InvalidAudioError("Uploaded audio could not be decoded. Unsupported or corrupted audio format.") from exc

            # 5. Validate converted audio frames, sample rate, channels, duration, and silence
            duration = self._validate_audio(temp_wav_file)

            # 6. Transcription phase using the converted WAV file
            engine_name = self._transcription_service.engine_name
            raw_transcript: str
            if manual_transcript and manual_transcript.strip():
                raw_transcript = manual_transcript.strip()
                engine_name = "manual_verified"
                transcription_status = "verified"
            else:
                try:
                    raw_transcript = await self._transcription_service.transcribe(temp_wav_file)
                    transcription_status = "completed"
                except EmptyTranscriptError as exc:
                    self._speech_repo.upsert_result(
                        assessment_id=assessment_id,
                        audio_duration_seconds=duration,
                        audio_format="wav",
                        transcription_status="failed",
                        transcription_engine=engine_name,
                        inference_status="failed",
                        error_message="Speech transcription produced no intelligible words.",
                    )
                    raise InvalidAudioError("Speech recording contained no detectable or intelligible words.") from exc
                except TranscriptionError as exc:
                    self._speech_repo.upsert_result(
                        assessment_id=assessment_id,
                        audio_duration_seconds=duration,
                        audio_format="wav",
                        transcription_status="failed",
                        transcription_engine=engine_name,
                        inference_status="failed",
                        error_message=str(exc),
                    )
                    raise

            # 7. Clean transcript according to Model 3 preprocessing requirements
            transcript = clean_transcript(raw_transcript)
            if not transcript:
                self._speech_repo.upsert_result(
                    assessment_id=assessment_id,
                    audio_duration_seconds=duration,
                    audio_format="wav",
                    transcription_status="failed",
                    transcription_engine=engine_name,
                    inference_status="failed",
                    error_message="Speech transcription produced no intelligible words.",
                )
                raise InvalidAudioError("Speech recording contained no detectable or intelligible words.")

            # 8. Model 3 Inference phase using the SAME converted WAV and cleaned transcript
            try:
                prediction = self._model3_manager.predict(
                    audio_path=temp_wav_file,
                    transcript=transcript,
                )
            except Model3InferenceError as exc:
                self._speech_repo.upsert_result(
                    assessment_id=assessment_id,
                    transcript=transcript,
                    audio_duration_seconds=duration,
                    audio_format="wav",
                    transcription_status=transcription_status,
                    transcription_engine=engine_name,
                    inference_status="failed",
                    error_message=str(exc),
                )
                raise

            # In accordance with scientific requirements:
            # If ASR was used instead of human clinical transcript, flag status
            inference_status = "awaiting_asr_verification" if engine_name != "manual_verified" else "completed"

            # 9. Persist result in Supabase
            result = self._speech_repo.upsert_result(
                assessment_id=assessment_id,
                audio_storage_path=None,  # Audio kept private, not stored in relational DB
                transcript=transcript,
                transcription_status=transcription_status,
                transcription_engine=engine_name,
                audio_duration_seconds=duration,
                audio_format="wav",
                inference_status=inference_status,
                predicted_class=prediction["predicted_class"],
                probability_hc=prediction["hc_probability"],
                hc_probability=prediction["hc_probability"],
                probability_mci=prediction["mci_probability"],
                mci_probability=prediction["mci_probability"],
                probability_dementia=prediction["dementia_probability"],
                dementia_probability=prediction["dementia_probability"],
                branch_probabilities=prediction.get("branch_probabilities"),
                components_used=prediction.get("components_used"),
                model_name="NeuroDetect Model 3 - PROCESS-2 CTD Classifier",
                model_version=prediction.get("model_version"),
                disclaimer=prediction.get("disclaimer") or MODEL3_DISCLAIMER,
                error_message=None,
            )

            return {
                "assessment_id": assessment_id,
                "status": "completed",
                "transcription_status": transcription_status,
                "transcription_engine": engine_name,
                "inference_status": inference_status,
                "predicted_class": prediction["predicted_class"],
                "probabilities": prediction["probabilities"],
                "probability_hc": prediction["hc_probability"],
                "hc_probability": prediction["hc_probability"],
                "probability_mci": prediction["mci_probability"],
                "mci_probability": prediction["mci_probability"],
                "probability_dementia": prediction["dementia_probability"],
                "dementia_probability": prediction["dementia_probability"],
                "branch_probabilities": prediction.get("branch_probabilities"),
                "components_used": prediction.get("components_used"),
                "model_version": prediction.get("model_version"),
                "disclaimer": prediction.get("disclaimer") or MODEL3_DISCLAIMER,
                "created_at": result.get("created_at"),
                "updated_at": result.get("updated_at"),
            }

        finally:
            # 10. Reliable cleanup of all temporary audio files in all execution paths
            for path in (temp_raw_file, temp_wav_file):
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except Exception as exc:
                        logger.warning("Failed to clean up temporary audio file %s: %s", path, exc)

    @staticmethod
    def _validate_uuid(assessment_id: str) -> None:
        try:
            UUID(assessment_id)
        except ValueError as exc:
            raise ValueError(f"assessment_id '{assessment_id}' is not a valid UUID.") from exc

    @staticmethod
    def _validate_audio(file_path: str) -> float:
        """
        Validates that converted PCM WAV audio is decodable, meets duration limits,
        has valid audio frames/channels/sample rate, and is non-silent.
        Returns duration in seconds.
        """
        try:
            info = sf.info(file_path)
        except Exception as exc:
            logger.error("Audio decoding failed: unsupported or corrupted audio format: %s", exc)
            raise InvalidAudioError("Uploaded audio could not be decoded. Unsupported or corrupted audio format.") from exc

        if info.frames <= 0:
            raise InvalidAudioError("Audio recording contains no valid audio frames.")

        if info.samplerate <= 0:
            raise InvalidAudioError("Audio recording has an invalid sample rate.")

        if info.channels < 1:
            raise InvalidAudioError("Audio recording has an invalid channel count.")

        duration = float(info.duration)
        if duration < MIN_DURATION_SECONDS:
            raise InvalidAudioError(f"Audio recording is too short ({duration:.2f}s). Minimum required duration is {MIN_DURATION_SECONDS}s.")
        if duration > MAX_DURATION_SECONDS:
            raise InvalidAudioError(f"Audio recording exceeds maximum allowed duration of {MAX_DURATION_SECONDS}s.")

        try:
            data, _ = sf.read(file_path, dtype="float32")
            max_amplitude = float(np.max(np.abs(data))) if len(data) > 0 else 0.0
        except Exception as exc:
            logger.error("Failed to read audio waveform for silence validation: %s", exc)
            raise InvalidAudioError("Uploaded audio could not be read for waveform validation.") from exc

        if max_amplitude < 1e-5:
            raise InvalidAudioError("Audio recording is completely silent. Please speak clearly into the microphone.")

        return duration
