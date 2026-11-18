from __future__ import annotations

import math

from app.games.boston_naming.config import DEFAULT_CONFIG, SCORED_STIMULI, STIMULUS_LOOKUP
from app.games.boston_naming.exceptions import FeatureValidationError, TelemetryValidationError
from app.games.boston_naming.schemas import (
    BostonNamingCompleteRequest,
    BostonNamingEventType,
    BostonNamingFeatures,
)


def validate_telemetry(
    request: BostonNamingCompleteRequest,
    assessment_id: str,
) -> None:
    events = request.events
    if not events:
        raise TelemetryValidationError("event list is empty")

    for event in events:
        if event.assessment_id != assessment_id:
            raise TelemetryValidationError(
                f"event.assessment_id '{event.assessment_id}' does not match path assessment_id '{assessment_id}'"
            )

    event_types = {event.event_type for event in events}
    required = {
        BostonNamingEventType.GAME_STARTED,
        BostonNamingEventType.PRACTICE_STARTED,
        BostonNamingEventType.PRACTICE_COMPLETED,
        BostonNamingEventType.ASSESSMENT_STARTED,
        BostonNamingEventType.GAME_COMPLETED,
    }
    missing = required - event_types
    if missing:
        raise TelemetryValidationError(
            f"missing required event types: {sorted(item.value for item in missing)}"
        )

    completed_trial_ids = [event.trial_id for event in events if event.event_type == BostonNamingEventType.TRIAL_COMPLETED]
    if len(completed_trial_ids) != len(set(completed_trial_ids)):
        raise TelemetryValidationError("duplicate trial_completed events detected")

    scored_presented = [
        event for event in events
        if event.event_type == BostonNamingEventType.STIMULUS_PRESENTED and event.phase.value == "running"
    ]
    if len(scored_presented) != DEFAULT_CONFIG.TOTAL_SCORED_TRIALS:
        raise TelemetryValidationError(
            f"expected {DEFAULT_CONFIG.TOTAL_SCORED_TRIALS} scored stimuli, received {len(scored_presented)}"
        )

    practice_presented = [
        event for event in events
        if event.event_type == BostonNamingEventType.STIMULUS_PRESENTED and event.phase.value == "practice"
    ]
    if len(practice_presented) != DEFAULT_CONFIG.PRACTICE_TRIALS:
        raise TelemetryValidationError(
            f"expected {DEFAULT_CONFIG.PRACTICE_TRIALS} practice stimuli, received {len(practice_presented)}"
        )

    expected_stimulus_ids = {stimulus.stimulus_id for stimulus in SCORED_STIMULI}
    presented_stimulus_ids = {
        str(event.metadata.get("stimulus_id"))
        for event in scored_presented
        if event.metadata.get("stimulus_id") is not None
    }
    if presented_stimulus_ids != expected_stimulus_ids:
        raise TelemetryValidationError("scored stimuli do not match the configured deterministic set")

    for event in scored_presented + practice_presented:
        stimulus_id = str(event.metadata.get("stimulus_id"))
        if stimulus_id not in STIMULUS_LOOKUP:
            raise TelemetryValidationError(f"unknown stimulus_id '{stimulus_id}' in telemetry")


def _ensure_finite(name: str, value: float | None) -> None:
    if value is None:
        return
    if not math.isfinite(value):
        raise FeatureValidationError(f"{name} must be finite")


def _ensure_rate(name: str, value: float | None) -> None:
    if value is None:
        return
    _ensure_finite(name, value)
    if not 0.0 <= value <= 1.0:
        raise FeatureValidationError(f"{name}={value} must be between 0 and 1")


def _ensure_non_negative(name: str, value: float | int | None) -> None:
    if value is None:
        return
    if value < 0:
        raise FeatureValidationError(f"{name}={value} must be >= 0")
    if isinstance(value, float):
        _ensure_finite(name, value)


def validate_features(features: BostonNamingFeatures) -> None:
    _ensure_rate("naming_accuracy", features.naming_accuracy)
    _ensure_rate("uncued_accuracy", features.uncued_accuracy)
    _ensure_rate("cued_accuracy", features.cued_accuracy)
    _ensure_rate("semantic_cue_rate", features.semantic_cue_rate)
    _ensure_rate("phonemic_cue_rate", features.phonemic_cue_rate)
    _ensure_rate("total_cue_rate", features.total_cue_rate)
    _ensure_non_negative("mean_response_latency_ms", features.mean_response_latency_ms)
    _ensure_non_negative("median_response_latency_ms", features.median_response_latency_ms)
    _ensure_non_negative("response_latency_std_ms", features.response_latency_std_ms)
    _ensure_non_negative("hesitation_duration_ms", features.hesitation_duration_ms)
    _ensure_non_negative("hesitation_variability_ms", features.hesitation_variability_ms)
    _ensure_non_negative("omission_errors", features.omission_errors)
    _ensure_non_negative("semantic_errors", features.semantic_errors)
    _ensure_non_negative("phonemic_errors", features.phonemic_errors)
    _ensure_non_negative("visual_errors", features.visual_errors)
    _ensure_non_negative("unrelated_errors", features.unrelated_errors)
    _ensure_non_negative("ambiguous_errors", features.ambiguous_errors)
    _ensure_rate("self_correction_rate", features.self_correction_rate)
    _ensure_rate("successful_self_correction_rate", features.successful_self_correction_rate)
    _ensure_non_negative("mean_response_duration_ms", features.mean_response_duration_ms)
    _ensure_non_negative("response_duration_std_ms", features.response_duration_std_ms)
    _ensure_non_negative("correct_response_latency_ms", features.correct_response_latency_ms)
    _ensure_non_negative("incorrect_response_latency_ms", features.incorrect_response_latency_ms)
    _ensure_rate("difficulty_adjusted_accuracy", features.difficulty_adjusted_accuracy)
    _ensure_rate("easy_accuracy", features.easy_accuracy)
    _ensure_rate("medium_accuracy", features.medium_accuracy)
    _ensure_rate("hard_accuracy", features.hard_accuracy)
    _ensure_rate("naming_consistency", features.naming_consistency)
    _ensure_finite("fatigue_trend", features.fatigue_trend)
    if features.completion_time_ms <= 0:
        raise FeatureValidationError("completion_time_ms must be > 0")
