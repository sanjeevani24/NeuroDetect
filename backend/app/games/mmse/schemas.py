from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class MMSEEventType(str, Enum):
    GAME_STARTED = "game_started"
    PHASE_STARTED = "phase_started"
    QUESTION_PRESENTED = "question_presented"
    RESPONSE_STARTED = "response_started"
    RESPONSE_SUBMITTED = "response_submitted"
    RESPONSE_EDITED = "response_edited"
    ITEM_PRESENTED = "item_presented"
    ITEM_SELECTED = "item_selected"
    ITEM_COMPLETED = "item_completed"
    PHASE_COMPLETED = "phase_completed"
    GAME_COMPLETED = "game_completed"
    ERROR = "error"


class MMSEPhase(str, Enum):
    INTRO = "INTRO"
    ORIENTATION = "ORIENTATION"
    REGISTRATION = "REGISTRATION"
    ATTENTION = "ATTENTION"
    LANGUAGE = "LANGUAGE"
    DELAYED_RECALL = "DELAYED_RECALL"
    COMMAND = "COMMAND"
    COMPLETION = "COMPLETION"


class MMSEEvent(BaseModel):
    event_id: str
    assessment_id: str
    game: str = Field(default="mmse")
    phase: MMSEPhase
    event_type: MMSEEventType
    timestamp: datetime
    question_id: str | None = None
    item_id: str | None = None
    value: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("game")
    @classmethod
    def game_must_be_mmse(cls, value: str) -> str:
        if value != "mmse":
            raise ValueError("game must be 'mmse' for this endpoint")
        return value


class MMSECompletionRequest(BaseModel):
    events: list[MMSEEvent]

    @field_validator("events")
    @classmethod
    def events_not_empty(cls, value: list[MMSEEvent]) -> list[MMSEEvent]:
        if not value:
            raise ValueError("events must not be empty")
        return value


class MMSEFeatureSet(BaseModel):
    orientation_accuracy: float = Field(ge=0, le=1)
    registration_accuracy: float = Field(ge=0, le=1)
    attention_accuracy: float = Field(ge=0, le=1)
    serial7_accuracy: float = Field(ge=0, le=1)
    delayed_recall_accuracy: float = Field(ge=0, le=1)
    language_accuracy: float = Field(ge=0, le=1)
    command_following_accuracy: float = Field(ge=0, le=1)
    response_latency: float = Field(ge=0)
    latency_variability: float = Field(ge=0)
    omission_errors: int = Field(ge=0)
    intrusion_errors: int = Field(ge=0)
    correction_frequency: float = Field(ge=0, le=1)
    completion_time: float = Field(gt=0)
    performance_consistency: float = Field(ge=0, le=1)


class MMSEGameResult(BaseModel):
    assessment_id: str
    game: str = "mmse"
    status: str = "completed"
    features: MMSEFeatureSet
