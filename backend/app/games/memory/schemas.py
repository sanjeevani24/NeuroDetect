"""
Pydantic schemas for the Memory Recall game.

These are the ONLY shapes the API accepts/returns. No arbitrary unvalidated
dictionaries are passed through the backend.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class MemoryEventType(str, Enum):
    GAME_STARTED = "game_started"
    PHASE_STARTED = "phase_started"
    ITEM_PRESENTED = "item_presented"
    ITEM_HIDDEN = "item_hidden"
    ITEM_SELECTED = "item_selected"
    ITEM_DESELECTED = "item_deselected"
    RESPONSE_STARTED = "response_started"
    RESPONSE_SUBMITTED = "response_submitted"
    RESPONSE_EDITED = "response_edited"
    RETRY = "retry"
    RECOGNITION_RESPONSE = "recognition_response"
    CONFIDENCE_SUBMITTED = "confidence_submitted"
    PHASE_COMPLETED = "phase_completed"
    GAME_COMPLETED = "game_completed"


class MemoryPhase(str, Enum):
    INTRO = "INTRO"
    LEARNING = "LEARNING"
    IMMEDIATE_RECALL = "IMMEDIATE_RECALL"
    DISTRACTOR = "DISTRACTOR"
    DELAYED_RECALL = "DELAYED_RECALL"
    RECOGNITION = "RECOGNITION"
    CONFIDENCE = "CONFIDENCE"
    COMPLETE = "COMPLETE"


class MemoryEvent(BaseModel):
    """
    A single, immutable telemetry event. The full event stream must be
    sufficient to reconstruct final state for every phase — nothing about
    game outcome is ever computed client-side and sent pre-aggregated,
    except for the raw facts contained in an event's own fields.
    """

    event_id: str
    assessment_id: str
    game: str = Field(default="memory")
    phase: MemoryPhase
    event_type: MemoryEventType
    timestamp: datetime
    item_id: Optional[str] = None
    trial_id: Optional[str] = None
    value: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("game")
    @classmethod
    def game_must_be_memory(cls, v: str) -> str:
        if v != "memory":
            raise ValueError("game must be 'memory' for this endpoint")
        return v


class MemoryConfidence(BaseModel):
    immediate_recall: int = Field(ge=1, le=5)
    delayed_recall: int = Field(ge=1, le=5)
    recognition: int = Field(ge=1, le=5)


class MemoryGameCompletionRequest(BaseModel):
    events: list[MemoryEvent]
    confidence: MemoryConfidence

    @field_validator("events")
    @classmethod
    def events_not_empty(cls, v: list[MemoryEvent]) -> list[MemoryEvent]:
        if not v:
            raise ValueError("events must not be empty")
        return v


class MemoryFeatureSet(BaseModel):
    immediate_recall_accuracy: float = Field(ge=0, le=1)
    delayed_recall_accuracy: float = Field(ge=0, le=1)
    recognition_accuracy: float = Field(ge=0, le=1)
    recall_decay_rate: float = Field(ge=0, le=1)
    recall_latency: float = Field(ge=0)
    omission_errors: int = Field(ge=0)
    intrusion_errors: int = Field(ge=0)
    sequence_recall_accuracy: float = Field(ge=0, le=1)
    hesitation_duration: float = Field(ge=0)
    retry_frequency: int = Field(ge=0)
    confidence_variability: float = Field(ge=0)
    completion_time: float = Field(gt=0)
    memory_consistency_trend: float = Field(ge=0, le=1)


class MemoryGameResult(BaseModel):
    assessment_id: str
    game: str = "memory"
    status: str = "completed"
    features: MemoryFeatureSet
