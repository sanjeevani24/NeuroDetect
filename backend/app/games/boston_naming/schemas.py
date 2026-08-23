from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.games.boston_naming.config import DifficultyLevel


class BostonNamingPhase(str, Enum):
    INTRO = "intro"
    PRACTICE = "practice"
    READY = "ready"
    RUNNING = "running"
    COMPLETION = "completion"


class BostonNamingEventType(str, Enum):
    GAME_STARTED = "game_started"
    PRACTICE_STARTED = "practice_started"
    PRACTICE_TRIAL_STARTED = "practice_trial_started"
    PRACTICE_RESPONSE = "practice_response"
    PRACTICE_COMPLETED = "practice_completed"
    ASSESSMENT_STARTED = "assessment_started"
    TRIAL_STARTED = "trial_started"
    STIMULUS_PRESENTED = "stimulus_presented"
    RESPONSE_RECORDING_STARTED = "response_recording_started"
    RESPONSE_RECORDING_STOPPED = "response_recording_stopped"
    TRANSCRIPTION_COMPLETED = "transcription_completed"
    RESPONSE_CLASSIFIED = "response_classified"
    CUE_PRESENTED = "cue_presented"
    SELF_CORRECTION_DETECTED = "self_correction_detected"
    TRIAL_COMPLETED = "trial_completed"
    RESPONSE_TIMEOUT = "response_timeout"
    GAME_COMPLETED = "game_completed"
    GAME_SUBMISSION_STARTED = "game_submission_started"
    GAME_SUBMISSION_SUCCEEDED = "game_submission_succeeded"
    GAME_SUBMISSION_FAILED = "game_submission_failed"


class CorrectnessLabel(str, Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    AMBIGUOUS = "ambiguous"


class ErrorType(str, Enum):
    NONE = "NONE"
    SEMANTIC = "SEMANTIC"
    VISUAL = "VISUAL"
    PHONEMIC = "PHONEMIC"
    UNRELATED = "UNRELATED"
    NO_RESPONSE = "NO_RESPONSE"
    UNINTELLIGIBLE = "UNINTELLIGIBLE"
    UNKNOWN = "UNKNOWN"


class TranscriptionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"


class RecordingStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    DENIED = "DENIED"
    NOT_SUPPORTED = "NOT_SUPPORTED"


class CueType(str, Enum):
    SEMANTIC = "semantic"
    PHONEMIC = "phonemic"


class BostonNamingTelemetryEvent(BaseModel):
    event_id: str
    assessment_id: str
    game: str = "boston_naming"
    phase: BostonNamingPhase
    event_type: BostonNamingEventType
    timestamp: datetime
    trial_id: str | None = None
    value: Any | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("game")
    @classmethod
    def game_must_be_boston_naming(cls, value: str) -> str:
        if value != "boston_naming":
            raise ValueError("event.game must equal 'boston_naming'")
        return value


class BostonNamingCompleteRequest(BaseModel):
    events: list[BostonNamingTelemetryEvent]

    @field_validator("events")
    @classmethod
    def events_not_empty(cls, value: list[BostonNamingTelemetryEvent]) -> list[BostonNamingTelemetryEvent]:
        if not value:
            raise ValueError("events must not be empty")
        return value


class ReconstructedNamingTrial(BaseModel):
    trial_id: str
    trial_index: int
    stimulus_id: str
    difficulty: DifficultyLevel
    is_practice: bool
    stimulus_presented_at: datetime
    response_started_at: datetime | None = None
    response_completed_at: datetime | None = None
    audio_start_timestamp: datetime | None = None
    audio_end_timestamp: datetime | None = None
    response_duration_ms: float | None = None
    response_latency_ms: float | None = None
    transcript: str | None = None
    transcript_confidence: float | None = None
    transcription_status: TranscriptionStatus = TranscriptionStatus.UNAVAILABLE
    normalized_response: str | None = None
    initial_response: str | None = None
    final_response: str | None = None
    correctness: CorrectnessLabel = CorrectnessLabel.AMBIGUOUS
    error_type: ErrorType = ErrorType.UNKNOWN
    cue_used: bool = False
    semantic_cue_used: bool = False
    phonemic_cue_used: bool = False
    time_to_cue_ms: float | None = None
    response_after_cue_ms: float | None = None
    correct_after_cue: bool = False
    self_corrected: bool | None = None
    self_correction_latency_ms: float | None = None
    hesitation_duration_ms: float | None = None
    number_of_hesitation_markers: int = 0
    timeout: bool = False
    recording_status: RecordingStatus = RecordingStatus.SUCCESS


class BostonNamingFeatures(BaseModel):
    naming_accuracy: float
    uncued_accuracy: float
    cued_accuracy: float | None = None
    semantic_cue_rate: float
    phonemic_cue_rate: float
    total_cue_rate: float
    mean_response_latency_ms: float | None = None
    median_response_latency_ms: float | None = None
    response_latency_std_ms: float
    hesitation_duration_ms: float
    hesitation_variability_ms: float
    omission_errors: int
    semantic_errors: int
    phonemic_errors: int
    visual_errors: int
    unrelated_errors: int
    ambiguous_errors: int
    self_correction_rate: float
    successful_self_correction_rate: float | None = None
    mean_response_duration_ms: float | None = None
    response_duration_std_ms: float
    correct_response_latency_ms: float | None = None
    incorrect_response_latency_ms: float | None = None
    difficulty_adjusted_accuracy: float
    easy_accuracy: float | None = None
    medium_accuracy: float | None = None
    hard_accuracy: float | None = None
    naming_consistency: float
    fatigue_trend: float
    completion_time_ms: float
    raw_trials: list[dict[str, Any]]


class BostonNamingCompleteResponse(BaseModel):
    assessment_id: str
    game: str = "boston_naming"
    status: str = "completed"
    features: BostonNamingFeatures
