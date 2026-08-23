"""
Pydantic schemas for the N-Back vertical slice.

Follows the same telemetry-event-as-source-of-truth pattern as Memory Recall:
the frontend ships a flat list of timestamped events, and the backend
reconstructs trials from them rather than trusting a pre-aggregated summary.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class NBackEventType(str, Enum):
    GAME_STARTED = "game_started"
    PRACTICE_STARTED = "practice_started"
    PRACTICE_TRIAL_STARTED = "practice_trial_started"
    PRACTICE_RESPONSE = "practice_response"
    PRACTICE_COMPLETED = "practice_completed"
    ASSESSMENT_STARTED = "assessment_started"
    TRIAL_STARTED = "trial_started"
    STIMULUS_PRESENTED = "stimulus_presented"
    RESPONSE_SUBMITTED = "response_submitted"
    RESPONSE_TIMEOUT = "response_timeout"
    TRIAL_COMPLETED = "trial_completed"
    PHASE_COMPLETED = "phase_completed"
    GAME_COMPLETED = "game_completed"


class NBackPhase(str, Enum):
    INTRO = "intro"
    PRACTICE = "practice"
    READY = "ready"
    RUNNING = "running"
    COMPLETION = "completion"


class NBackResponse(str, Enum):
    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    NONE = "NONE"  # no response received within the response window


# ---------------------------------------------------------------------------
# Inbound telemetry
# ---------------------------------------------------------------------------

class NBackTelemetryEvent(BaseModel):
    event_id: str
    assessment_id: str
    game: str = "nback"
    phase: NBackPhase
    event_type: NBackEventType
    timestamp: datetime
    trial_id: Optional[str] = None
    value: Optional[Any] = None
    metadata: dict = Field(default_factory=dict)

    @field_validator("game")
    @classmethod
    def game_must_be_nback(cls, v: str) -> str:
        if v != "nback":
            raise ValueError("event.game must equal 'nback'")
        return v


class NBackCompleteRequest(BaseModel):
    events: list[NBackTelemetryEvent]


# ---------------------------------------------------------------------------
# Internal reconstructed trial (not a DB table — feature-extraction input)
# ---------------------------------------------------------------------------

class ReconstructedTrial(BaseModel):
    trial_id: str
    trial_index: int
    stimulus: str
    is_warmup: bool
    is_practice: bool
    is_target: Optional[bool] = None  # None for warmup trials (undefined)
    presented_at: datetime
    response_started_at: Optional[datetime] = None
    response_at: Optional[datetime] = None
    response: NBackResponse = NBackResponse.NONE
    correct_answer: Optional[NBackResponse] = None
    response_latency_ms: Optional[float] = None
    timed_out: bool = False


# ---------------------------------------------------------------------------
# Feature output
# ---------------------------------------------------------------------------

class NBackFeatures(BaseModel):
    nback_accuracy: float
    hit_rate: float
    false_alarm_rate: float
    sensitivity: float
    response_latency: float
    latency_variability: float
    omission_errors: int
    commission_errors: int
    d_prime: float
    response_consistency: float
    fatigue_trend: float
    completion_time: float


class NBackCompleteResponse(BaseModel):
    assessment_id: str
    game: str = "nback"
    status: str = "completed"
    features: NBackFeatures
