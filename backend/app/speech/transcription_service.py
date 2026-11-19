"""
Transcription Service for NeuroDetect Speech Assessment.

CRITICAL ARCHITECTURAL CONTEXT (PHASE 2):
Model 3 was trained on ground-truth human clinical transcripts from CognoSpeak/PROCESS-2.
Its 12 linguistic features (filler counts, word counts, sentence lengths, subordination)
and acoustic speech-rate features depend directly on preserved verbal hesitations ("um", "uh"),
disfluencies, and punctuation.

Standard ASR models (e.g., vanilla Whisper) omit or normalize disfluencies, creating an
uncalibrated distribution shift against the training data. This service isolates transcription
behind a replaceable, privacy-preserving interface.
"""
from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from app.speech.config import TRANSCRIPTION_ENGINE

logger = logging.getLogger("neurodetect.speech.transcription")

_MODEL_CACHE: dict[str, Any] = {}


class TranscriptionError(Exception):
    """Raised when audio transcription fails."""


class EmptyTranscriptError(TranscriptionError):
    """Raised when transcription yields an empty or whitespace-only transcript."""


class BaseTranscriptionService(ABC):
    """Abstract base class for transcription providers."""

    @abstractmethod
    async def transcribe(self, audio_path: str) -> str:
        """Transcribe an audio file and return the non-empty text transcript."""
        pass

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Identifies the active transcription engine."""
        pass


class PluggableLocalASRService(BaseTranscriptionService):
    """
    Local privacy-preserving ASR engine powered by faster-whisper (with fallback to openai-whisper).
    Loads the model once, caches it in memory across requests, and runs inference on CPU with INT8 quantization.
    Never transmits participant audio to external third-party cloud APIs.
    """

    def __init__(
        self,
        model_size: Optional[str] = None,
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
        initial_prompt: Optional[str] = None,
    ):
        self._model_size = model_size or os.getenv("WHISPER_MODEL_SIZE", "base")
        self._device = device or os.getenv("WHISPER_DEVICE", "cpu")
        self._compute_type = compute_type or os.getenv("WHISPER_COMPUTE_TYPE", "int8")
        self._initial_prompt = initial_prompt

    @property
    def engine_name(self) -> str:
        return f"faster_whisper_{self._model_size}"

    def _get_or_load_model(self) -> tuple[str, Any]:
        cache_key = f"{self._model_size}_{self._device}_{self._compute_type}"
        if cache_key in _MODEL_CACHE:
            return _MODEL_CACHE[cache_key]

        # 1. Try faster-whisper first
        try:
            from faster_whisper import WhisperModel  # type: ignore

            logger.info(
                "Loading faster-whisper model '%s' (device=%s, compute_type=%s)...",
                self._model_size,
                self._device,
                self._compute_type,
            )
            try:
                model = WhisperModel(
                    self._model_size,
                    device=self._device,
                    compute_type=self._compute_type,
                )
            except Exception as init_exc:
                logger.warning(
                    "faster-whisper failed with compute_type='%s': %s. Falling back to 'default'.",
                    self._compute_type,
                    init_exc,
                )
                model = WhisperModel(
                    self._model_size,
                    device=self._device,
                    compute_type="default",
                )
            _MODEL_CACHE[cache_key] = ("faster_whisper", model)
            return _MODEL_CACHE[cache_key]
        except ImportError:
            pass

        # 2. Try standard openai-whisper fallback
        try:
            import whisper  # type: ignore

            logger.info("faster-whisper not found, loading openai-whisper '%s'...", self._model_size)
            model = whisper.load_model(self._model_size, device=self._device)
            _MODEL_CACHE[cache_key] = ("whisper", model)
            return _MODEL_CACHE[cache_key]
        except ImportError:
            pass

        # If neither is installed, fail safely without fabricating
        logger.warning("Local ASR engine (faster-whisper or whisper) not installed in runtime environment.")
        raise TranscriptionError(
            "Local ASR engine is not installed. To transcribe speech locally, install faster-whisper. "
            "Transcripts must not be fabricated."
        )

    async def transcribe(self, audio_path: str) -> str:
        path = Path(audio_path)
        if not path.is_file():
            logger.error("Transcription input audio file does not exist: %s", path)
            raise TranscriptionError("Audio file for transcription was not found.")

        backend_type, model = self._get_or_load_model()

        try:
            if backend_type == "faster_whisper":
                transcribe_kwargs: dict[str, Any] = {
                    "beam_size": 5,
                    "language": "en",
                    "vad_filter": False,
                }
                # Use neutral transcription without scene-specific linguistic guidance
                if self._initial_prompt:
                    transcribe_kwargs["initial_prompt"] = self._initial_prompt

                segments, info = model.transcribe(
                    str(path),
                    **transcribe_kwargs,
                )
                text_parts = [segment.text.strip() for segment in segments if segment.text and segment.text.strip()]
                text = " ".join(text_parts).strip()
            else:
                whisper_kwargs: dict[str, Any] = {
                    "language": "en",
                }
                if self._initial_prompt:
                    whisper_kwargs["initial_prompt"] = self._initial_prompt

                result = model.transcribe(
                    str(path),
                    **whisper_kwargs,
                )
                text = (result.get("text") or "").strip()
        except Exception as exc:
            logger.error("Local ASR engine failed during transcription execution: %s", exc)
            raise TranscriptionError(f"Speech transcription failed during audio processing: {exc}") from exc

        if not text:
            logger.warning("Local ASR returned an empty transcript for audio.")
            raise EmptyTranscriptError("Speech transcription produced no intelligible words.")

        return text


class ManualVerifiedTranscriptionService(BaseTranscriptionService):
    """
    Transcriber for clinically verified or manual transcripts.
    """

    def __init__(self, transcript_override: Optional[str] = None):
        self._transcript_override = transcript_override

    @property
    def engine_name(self) -> str:
        return "manual_verified"

    async def transcribe(self, audio_path: str) -> str:
        if not self._transcript_override or not self._transcript_override.strip():
            raise EmptyTranscriptError("No manual verified transcript was provided.")
        return self._transcript_override.strip()


class MockTranscriptionService(BaseTranscriptionService):
    """
    Test & verification transcription service for unit and integration testing.
    Produces a standard Cookie Theft picture description with fillers.
    """

    def __init__(self, fixed_transcript: Optional[str] = None):
        self._fixed_transcript = fixed_transcript or (
            "Well, um, the boy is taking cookies from the jar, and the stool is tipping over. "
            "The mother is washing dishes, uh, but the sink is overflowing onto the kitchen floor."
        )

    @property
    def engine_name(self) -> str:
        return "mock_test_transcription"

    async def transcribe(self, audio_path: str) -> str:
        path = Path(audio_path)
        if not path.is_file():
            logger.error("Mock transcription called with missing file")
            raise TranscriptionError("Audio file was not found.")
        return self._fixed_transcript


def get_transcription_service(engine: Optional[str] = None) -> BaseTranscriptionService:
    """Factory to get the configured transcription engine."""
    selected_engine = (engine or TRANSCRIPTION_ENGINE).lower().strip()

    if selected_engine in ("mock", "test", "mock_test_transcription"):
        return MockTranscriptionService()
    if selected_engine in ("manual", "verified", "manual_verified"):
        return ManualVerifiedTranscriptionService()

    # Default to PluggableLocalASRService (or fallback to mock if running in test environment)
    return PluggableLocalASRService()


async def transcribe_audio(audio_path: str, engine: Optional[str] = None) -> str:
    """Stable public helper for audio transcription."""
    service = get_transcription_service(engine)
    return await service.transcribe(audio_path)
