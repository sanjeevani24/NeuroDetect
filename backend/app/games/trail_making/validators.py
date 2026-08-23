from __future__ import annotations

import math

from app.games.trail_making.config import DEFAULT_CONFIG
from app.games.trail_making.exceptions import FeatureValidationError, TelemetryValidationError
from app.games.trail_making.schemas import (
    TrailMakingCompleteRequest,
    TrailMakingEventType,
    TrailMakingFeatures,
)


def validate_telemetry(request: TrailMakingCompleteRequest, assessment_id: str) -> None:
    if not request.node_layout:
        raise TelemetryValidationError("node_layout must not be empty")

    events = request.events
    for event in events:
        if event.assessment_id != assessment_id:
            raise TelemetryValidationError(
                f"event.assessment_id '{event.assessment_id}' does not match path assessment_id '{assessment_id}'"
            )
        if event.game_session_id != request.game_session_id:
            raise TelemetryValidationError("event.game_session_id does not match request.game_session_id")

    event_types = {event.event_type for event in events}
    required = {
        TrailMakingEventType.GAME_STARTED,
        TrailMakingEventType.GAME_COMPLETED,
    }
    missing = required - event_types
    if missing:
        raise TelemetryValidationError(
            f"missing required event types: {sorted(item.value for item in missing)}"
        )

    target_completed = [event for event in events if event.event_type == TrailMakingEventType.TARGET_COMPLETED]
    if len(target_completed) != len(DEFAULT_CONFIG.sequence_labels):
        raise TelemetryValidationError(
            f"expected {len(DEFAULT_CONFIG.sequence_labels)} target_completed events, received {len(target_completed)}"
        )

    seen_target_ids = [event.node_id for event in target_completed]
    if len(seen_target_ids) != len(set(seen_target_ids)):
        raise TelemetryValidationError("duplicate target_completed events detected")

    if len(request.node_layout) != len(DEFAULT_CONFIG.sequence_labels):
        raise TelemetryValidationError(
            f"expected {len(DEFAULT_CONFIG.sequence_labels)} layout nodes, received {len(request.node_layout)}"
        )


def _ensure_finite(name: str, value: float | None) -> None:
    if value is None:
        return
    if not math.isfinite(value):
        raise FeatureValidationError(f"{name} must be finite")


def _ensure_non_negative(name: str, value: float | int | None) -> None:
    if value is None:
        return
    if value < 0:
        raise FeatureValidationError(f"{name}={value} must be >= 0")
    if isinstance(value, float):
        _ensure_finite(name, value)


def _ensure_ratio(name: str, value: float | None) -> None:
    if value is None:
        return
    _ensure_finite(name, value)
    if not 0.0 <= value <= 1.0:
        raise FeatureValidationError(f"{name}={value} must be between 0 and 1")


def validate_features(features: TrailMakingFeatures) -> None:
    _ensure_ratio("path_efficiency", features.path_efficiency)
    _ensure_ratio("sequence_accuracy", features.sequence_accuracy)
    _ensure_non_negative("switching_delay", features.switching_delay)
    _ensure_non_negative("backtracking_frequency", features.backtracking_frequency)
    _ensure_non_negative("rule_violation_count", features.rule_violation_count)
    _ensure_non_negative("cursor_movement_entropy", features.cursor_movement_entropy)
    _ensure_non_negative("trajectory_deviation", features.trajectory_deviation)
    _ensure_non_negative("tremor_jitter_frequency", features.tremor_jitter_frequency)
    if features.total_completion_time <= 0:
        raise FeatureValidationError("total_completion_time must be > 0")
    _ensure_non_negative("total_error_count", features.total_error_count)
    _ensure_non_negative("correct_target_count", features.correct_target_count)
    _ensure_non_negative("mean_reaction_time", features.mean_reaction_time)
    _ensure_non_negative("median_reaction_time", features.median_reaction_time)
    _ensure_non_negative("reaction_time_variance", features.reaction_time_variance)
    _ensure_non_negative("hesitation_duration", features.hesitation_duration)
    _ensure_non_negative("error_recovery_time", features.error_recovery_time)
    _ensure_non_negative("first_half_time", features.first_half_time)
    _ensure_non_negative("second_half_time", features.second_half_time)
    _ensure_non_negative("time_degradation_ratio", features.time_degradation_ratio)
    _ensure_non_negative("switch_count", features.switch_count)
    _ensure_non_negative("correct_switch_count", features.correct_switch_count)
    _ensure_non_negative("incorrect_switch_count", features.incorrect_switch_count)
    _ensure_non_negative("backtracking_distance", features.backtracking_distance)
    _ensure_non_negative("trajectory_length", features.trajectory_length)
    _ensure_non_negative("ideal_path_length", features.ideal_path_length)
    _ensure_non_negative("correction_count", features.correction_count)
    _ensure_non_negative("idle_time", features.idle_time)
