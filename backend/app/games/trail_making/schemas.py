from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.games.trail_making.config import TrailNodeType


class TrailMakingPhase(str, Enum):
    INTRO = "intro"
    RUNNING = "running"
    COMPLETION = "completion"


class TrailMakingEventType(str, Enum):
    GAME_STARTED = "game_started"
    POINTER_SAMPLE = "pointer_sample"
    NODE_CLICKED = "node_clicked"
    TARGET_COMPLETED = "target_completed"
    GAME_COMPLETED = "game_completed"
    GAME_SUBMISSION_STARTED = "game_submission_started"
    GAME_SUBMISSION_SUCCEEDED = "game_submission_succeeded"
    GAME_SUBMISSION_FAILED = "game_submission_failed"


class TrailMakingErrorType(str, Enum):
    CORRECT = "CORRECT"
    WRONG_TARGET = "WRONG_TARGET"
    REPEAT_TARGET = "REPEAT_TARGET"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    WRONG_NUMBER = "WRONG_NUMBER"
    WRONG_LETTER = "WRONG_LETTER"
    INVALID_CLICK = "INVALID_CLICK"
    OTHER = "OTHER"


class TrailMakingNodeLayout(BaseModel):
    node_id: str
    label: str
    node_type: TrailNodeType
    sequence_index: int
    x: float
    y: float


class TrailMakingTelemetryEvent(BaseModel):
    event_id: str
    assessment_id: str
    game_session_id: str
    game: str = "trail_making"
    phase: TrailMakingPhase
    event_type: TrailMakingEventType
    timestamp: datetime
    relative_time_ms: float = Field(ge=0)
    node_id: str | None = None
    node_label: str | None = None
    node_type: TrailNodeType | None = None
    sequence_index: int | None = None
    expected_sequence_index: int | None = None
    x: float | None = None
    y: float | None = None
    pointer_x: float | None = None
    pointer_y: float | None = None
    was_correct: bool | None = None
    error_type: TrailMakingErrorType | None = None
    event_payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("game")
    @classmethod
    def game_must_be_trail_making(cls, value: str) -> str:
        if value != "trail_making":
            raise ValueError("event.game must equal 'trail_making'")
        return value


class TrailMakingCompleteRequest(BaseModel):
    game_session_id: str
    node_layout: list[TrailMakingNodeLayout]
    events: list[TrailMakingTelemetryEvent]

    @field_validator("events")
    @classmethod
    def events_not_empty(cls, value: list[TrailMakingTelemetryEvent]) -> list[TrailMakingTelemetryEvent]:
        if not value:
            raise ValueError("events must not be empty")
        return value


class TrailMakingFeatures(BaseModel):
    path_efficiency: float
    sequence_accuracy: float
    switching_delay: float
    backtracking_frequency: float
    rule_violation_count: int
    cursor_movement_entropy: float
    trajectory_deviation: float
    tremor_jitter_frequency: float
    total_completion_time: float
    total_error_count: int
    correct_target_count: int
    mean_reaction_time: float | None = None
    median_reaction_time: float | None = None
    reaction_time_variance: float | None = None
    hesitation_duration: float
    error_recovery_time: float | None = None
    first_half_time: float | None = None
    second_half_time: float | None = None
    time_degradation_ratio: float | None = None
    switch_count: int
    correct_switch_count: int
    incorrect_switch_count: int
    backtracking_distance: float
    trajectory_length: float
    ideal_path_length: float
    correction_count: int
    idle_time: float
    layout: list[dict[str, Any]]


class TrailMakingCompleteResponse(BaseModel):
    assessment_id: str
    game: str = "trail_making"
    status: str = "completed"
    features: TrailMakingFeatures
