from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.games.boston_naming.config import DEFAULT_CONFIG, DifficultyLevel, SCORED_STIMULI, PRACTICE_STIMULI
from app.games.boston_naming.schemas import (
    BostonNamingCompleteRequest,
    BostonNamingEventType,
    BostonNamingFeatures,
    BostonNamingPhase,
    BostonNamingTelemetryEvent,
)
from app.games.boston_naming.validators import validate_features, validate_telemetry
from app.games.boston_naming.exceptions import FeatureValidationError, TelemetryValidationError

ASSESSMENT_ID = "11111111-1111-1111-1111-111111111111"
T0 = datetime(2026, 1, 1, 12, 0, 0)


def evt(event_type, offset_s, *, trial_id=None, phase=BostonNamingPhase.RUNNING, metadata=None, value=None):
    return BostonNamingTelemetryEvent(
        event_id=f"evt-{event_type.value}-{offset_s}-{trial_id}",
        assessment_id=ASSESSMENT_ID,
        phase=phase,
        event_type=event_type,
        timestamp=T0 + timedelta(seconds=offset_s),
        trial_id=trial_id,
        value=value,
        metadata=metadata or {},
    )


def valid_request() -> BostonNamingCompleteRequest:
    events = [
        evt(BostonNamingEventType.GAME_STARTED, 0, phase=BostonNamingPhase.INTRO),
        evt(BostonNamingEventType.PRACTICE_STARTED, 1, phase=BostonNamingPhase.PRACTICE),
    ]
    for index, stimulus in enumerate(PRACTICE_STIMULI, start=1):
        events.append(evt(BostonNamingEventType.PRACTICE_TRIAL_STARTED, index + 1, phase=BostonNamingPhase.PRACTICE, trial_id=f"p-{index}"))
        events.append(evt(BostonNamingEventType.STIMULUS_PRESENTED, index + 1, phase=BostonNamingPhase.PRACTICE, trial_id=f"p-{index}", metadata={"trial_index": index, "stimulus_id": stimulus.stimulus_id}))
        events.append(evt(BostonNamingEventType.TRIAL_COMPLETED, index + 2, phase=BostonNamingPhase.PRACTICE, trial_id=f"p-{index}"))
    events.append(evt(BostonNamingEventType.PRACTICE_COMPLETED, 10, phase=BostonNamingPhase.PRACTICE))
    events.append(evt(BostonNamingEventType.ASSESSMENT_STARTED, 11))
    for index, stimulus in enumerate(SCORED_STIMULI, start=1):
        offset = 12 + index
        events.append(evt(BostonNamingEventType.TRIAL_STARTED, offset, trial_id=f"s-{index}"))
        events.append(evt(BostonNamingEventType.STIMULUS_PRESENTED, offset, trial_id=f"s-{index}", metadata={"trial_index": index, "stimulus_id": stimulus.stimulus_id, "difficulty": stimulus.difficulty.value}))
        events.append(evt(BostonNamingEventType.TRIAL_COMPLETED, offset + 1, trial_id=f"s-{index}"))
    events.append(evt(BostonNamingEventType.GAME_COMPLETED, 99, phase=BostonNamingPhase.COMPLETION))
    return BostonNamingCompleteRequest(events=events)


def test_valid_telemetry_passes():
    validate_telemetry(valid_request(), ASSESSMENT_ID)


def test_missing_required_event_rejected():
    request = valid_request()
    request.events = [event for event in request.events if event.event_type != BostonNamingEventType.GAME_COMPLETED]
    with pytest.raises(TelemetryValidationError):
        validate_telemetry(request, ASSESSMENT_ID)


def test_duplicate_trial_completion_rejected():
    request = valid_request()
    request.events.append(request.events[-2])
    with pytest.raises(TelemetryValidationError):
        validate_telemetry(request, ASSESSMENT_ID)


def valid_features() -> BostonNamingFeatures:
    return BostonNamingFeatures(
        naming_accuracy=0.7,
        uncued_accuracy=0.6,
        cued_accuracy=0.8,
        semantic_cue_rate=0.2,
        phonemic_cue_rate=0.1,
        total_cue_rate=0.3,
        mean_response_latency_ms=1400.0,
        median_response_latency_ms=1300.0,
        response_latency_std_ms=120.0,
        hesitation_duration_ms=1400.0,
        hesitation_variability_ms=90.0,
        omission_errors=1,
        semantic_errors=1,
        phonemic_errors=1,
        visual_errors=0,
        unrelated_errors=0,
        ambiguous_errors=0,
        self_correction_rate=0.2,
        successful_self_correction_rate=0.5,
        mean_response_duration_ms=700.0,
        response_duration_std_ms=80.0,
        correct_response_latency_ms=1200.0,
        incorrect_response_latency_ms=1500.0,
        difficulty_adjusted_accuracy=0.68,
        easy_accuracy=0.8,
        medium_accuracy=0.7,
        hard_accuracy=0.5,
        naming_consistency=0.75,
        fatigue_trend=-0.1,
        completion_time_ms=50000.0,
        raw_trials=[],
    )


def test_feature_validation_passes():
    validate_features(valid_features())


def test_non_finite_feature_rejected():
    with pytest.raises(FeatureValidationError):
        validate_features(valid_features().model_copy(update={"naming_consistency": float("inf")}))
