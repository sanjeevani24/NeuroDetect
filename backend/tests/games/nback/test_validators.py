from datetime import datetime, timedelta

import pytest

from app.games.nback.config import DEFAULT_CONFIG
from app.games.nback.schemas import (
    NBackCompleteRequest,
    NBackEventType,
    NBackFeatures,
    NBackPhase,
    NBackTelemetryEvent,
)
from app.games.nback.validators import (
    FeatureValidationError,
    TelemetryValidationError,
    validate_features,
    validate_telemetry,
)

ASSESSMENT_ID = "11111111-1111-1111-1111-111111111111"
T0 = datetime(2026, 1, 1, 12, 0, 0)


def evt(event_type, offset_s=0, trial_id=None, phase=NBackPhase.RUNNING, value=None, metadata=None):
    return NBackTelemetryEvent(
        event_id=f"evt-{event_type.value}-{offset_s}-{trial_id}",
        assessment_id=ASSESSMENT_ID,
        phase=phase,
        event_type=event_type,
        timestamp=T0 + timedelta(seconds=offset_s),
        trial_id=trial_id,
        value=value,
        metadata=metadata or {},
    )


def minimal_valid_event_stream():
    events = [
        evt(NBackEventType.GAME_STARTED, 0, phase=NBackPhase.INTRO),
        evt(NBackEventType.ASSESSMENT_STARTED, 1, phase=NBackPhase.RUNNING),
        evt(NBackEventType.TRIAL_STARTED, 2, trial_id="t1"),
        evt(
            NBackEventType.STIMULUS_PRESENTED,
            2,
            trial_id="t1",
            metadata={"trial_index": 0, "stimulus": "A", "is_warmup": True},
        ),
        evt(NBackEventType.TRIAL_COMPLETED, 3, trial_id="t1"),
        evt(NBackEventType.TRIAL_STARTED, 4, trial_id="t2"),
        evt(
            NBackEventType.STIMULUS_PRESENTED,
            4,
            trial_id="t2",
            metadata={"trial_index": 1, "stimulus": "B", "is_warmup": True},
        ),
        evt(NBackEventType.TRIAL_COMPLETED, 5, trial_id="t2"),
        evt(NBackEventType.TRIAL_STARTED, 6, trial_id="t3"),
        evt(
            NBackEventType.STIMULUS_PRESENTED,
            6,
            trial_id="t3",
            metadata={"trial_index": 2, "stimulus": "A", "is_target": True, "is_warmup": False},
        ),
        evt(NBackEventType.TRIAL_COMPLETED, 7, trial_id="t3"),
        evt(NBackEventType.GAME_COMPLETED, 10, phase=NBackPhase.COMPLETION),
    ]
    return events


# ---------------------------------------------------------------------------
# Telemetry validation
# ---------------------------------------------------------------------------

def test_valid_minimal_stream_passes():
    req = NBackCompleteRequest(events=minimal_valid_event_stream())
    validate_telemetry(req, ASSESSMENT_ID, DEFAULT_CONFIG)  # should not raise


def test_empty_events_rejected():
    req = NBackCompleteRequest(events=[])
    with pytest.raises(TelemetryValidationError):
        validate_telemetry(req, ASSESSMENT_ID, DEFAULT_CONFIG)


def test_mismatched_assessment_id_rejected():
    events = minimal_valid_event_stream()
    bad_event = events[0].model_copy(update={"assessment_id": "other-assessment"})
    events[0] = bad_event
    req = NBackCompleteRequest(events=events)
    with pytest.raises(TelemetryValidationError):
        validate_telemetry(req, ASSESSMENT_ID, DEFAULT_CONFIG)


def test_missing_required_event_types_rejected():
    events = [e for e in minimal_valid_event_stream() if e.event_type != NBackEventType.GAME_COMPLETED]
    req = NBackCompleteRequest(events=events)
    with pytest.raises(TelemetryValidationError):
        validate_telemetry(req, ASSESSMENT_ID, DEFAULT_CONFIG)


def test_orphaned_trial_completed_rejected():
    events = minimal_valid_event_stream()
    events.append(evt(NBackEventType.TRIAL_COMPLETED, 20, trial_id="ghost-trial"))
    req = NBackCompleteRequest(events=events)
    with pytest.raises(TelemetryValidationError):
        validate_telemetry(req, ASSESSMENT_ID, DEFAULT_CONFIG)


def test_duplicate_trial_completed_rejected():
    events = minimal_valid_event_stream()
    events.append(evt(NBackEventType.TRIAL_COMPLETED, 3.5, trial_id="t1"))
    req = NBackCompleteRequest(events=events)
    with pytest.raises(TelemetryValidationError):
        validate_telemetry(req, ASSESSMENT_ID, DEFAULT_CONFIG)


def test_duplicate_game_completed_rejected():
    events = minimal_valid_event_stream()
    events.append(evt(NBackEventType.GAME_COMPLETED, 11, phase=NBackPhase.COMPLETION))
    req = NBackCompleteRequest(events=events)
    with pytest.raises(TelemetryValidationError):
        validate_telemetry(req, ASSESSMENT_ID, DEFAULT_CONFIG)


# ---------------------------------------------------------------------------
# Feature validation (LOCKED ranges, spec section 16)
# ---------------------------------------------------------------------------

def valid_features(**overrides) -> dict:
    base = dict(
        nback_accuracy=0.8,
        hit_rate=0.75,
        false_alarm_rate=0.1,
        sensitivity=0.65,
        response_latency=0.6,
        latency_variability=0.15,
        omission_errors=2,
        commission_errors=1,
        d_prime=1.8,
        response_consistency=0.7,
        fatigue_trend=-0.1,
        completion_time=120.0,
    )
    base.update(overrides)
    return base


def test_valid_features_pass():
    validate_features(NBackFeatures(**valid_features()))  # should not raise


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("nback_accuracy", 1.5),
        ("nback_accuracy", -0.1),
        ("hit_rate", 1.1),
        ("false_alarm_rate", -0.01),
        ("sensitivity", 1.5),
        ("sensitivity", -1.5),
        ("response_latency", -0.5),
        ("latency_variability", -0.5),
        ("omission_errors", -1),
        ("commission_errors", -1),
        ("response_consistency", -0.1),
        ("fatigue_trend", 1.5),
        ("fatigue_trend", -1.5),
        ("completion_time", 0.0),
        ("completion_time", -10.0),
    ],
)
def test_out_of_range_feature_rejected(field, bad_value):
    with pytest.raises(FeatureValidationError):
        validate_features(NBackFeatures(**valid_features(**{field: bad_value})))


def test_non_finite_d_prime_rejected():
    with pytest.raises(FeatureValidationError):
        validate_features(NBackFeatures(**valid_features(d_prime=float("inf"))))
    with pytest.raises(FeatureValidationError):
        validate_features(NBackFeatures(**valid_features(d_prime=float("nan"))))
