from datetime import datetime, timedelta

import pytest

from app.games.nback.config import DEFAULT_CONFIG
from app.games.nback.schemas import (
    NBackCompleteRequest,
    NBackEventType,
    NBackPhase,
    NBackResponse,
    NBackTelemetryEvent,
)
from app.games.nback.service import (
    InsufficientTrialsError,
    TelemetryInvalidError,
    process_nback_completion,
    reconstruct_trials,
    select_scored_trials,
)

ASSESSMENT_ID = "22222222-2222-2222-2222-222222222222"
T0 = datetime(2026, 1, 1, 12, 0, 0)


def evt(event_type, offset_s, trial_id=None, phase=NBackPhase.RUNNING, value=None, metadata=None):
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


def build_trial_events(
    trial_id, t_start, trial_index, stimulus, is_target, is_warmup=False,
    response=None, response_offset=0.6, timeout=False, extra_response=None,
):
    events = [
        evt(NBackEventType.TRIAL_STARTED, t_start, trial_id=trial_id),
        evt(
            NBackEventType.STIMULUS_PRESENTED,
            t_start,
            trial_id=trial_id,
            metadata={"trial_index": trial_index, "stimulus": stimulus, "is_target": is_target, "is_warmup": is_warmup},
        ),
    ]
    if timeout:
        events.append(evt(NBackEventType.RESPONSE_TIMEOUT, t_start + 2.6, trial_id=trial_id))
    elif response is not None:
        events.append(
            evt(NBackEventType.RESPONSE_SUBMITTED, t_start + response_offset, trial_id=trial_id, value=response.value)
        )
        if extra_response is not None:
            # simulate a duplicate/late second response attempt
            events.append(
                evt(
                    NBackEventType.RESPONSE_SUBMITTED,
                    t_start + response_offset + 0.2,
                    trial_id=trial_id,
                    value=extra_response.value,
                )
            )
    events.append(evt(NBackEventType.TRIAL_COMPLETED, t_start + 3, trial_id=trial_id))
    return events


def full_valid_stream():
    """
    2 warmup trials + 4 scored trials (2 targets, 2 non-targets), practice
    phase included but must be excluded from scoring.
    """
    events = [
        evt(NBackEventType.GAME_STARTED, 0, phase=NBackPhase.INTRO),
        evt(NBackEventType.PRACTICE_STARTED, 1, phase=NBackPhase.PRACTICE),
    ]
    # one practice trial that would look like a "hit" if wrongly included
    events += build_trial_events(
        "p1", 2, 0, "A", is_target=False, response=NBackResponse.MATCH,
    )
    events[-2] = events[-2].model_copy(update={"phase": NBackPhase.PRACTICE})
    events.append(evt(NBackEventType.PRACTICE_COMPLETED, 6, phase=NBackPhase.PRACTICE))

    events.append(evt(NBackEventType.ASSESSMENT_STARTED, 7, phase=NBackPhase.RUNNING))

    # warmup trials (0, 1) - no valid 2-back comparison
    events += build_trial_events("w1", 8, 0, "A", is_target=None, is_warmup=True, response=NBackResponse.NO_MATCH)
    events += build_trial_events("w2", 12, 1, "B", is_target=None, is_warmup=True, response=NBackResponse.NO_MATCH)

    # scored trial 2: A -> target (matches trial 0's "A")
    events += build_trial_events("s1", 16, 2, "A", is_target=True, response=NBackResponse.MATCH)
    # scored trial 3: C -> non-target (trial 1 was "B")
    events += build_trial_events("s2", 20, 3, "C", is_target=False, response=NBackResponse.NO_MATCH)
    # scored trial 4: A -> non-target (trial 2 was "A", trial 2's 2-back is trial... ) explicit non-target for test
    events += build_trial_events("s3", 24, 4, "D", is_target=False, response=NBackResponse.MATCH)  # commission
    # scored trial 5: target with a timeout (omission)
    events += build_trial_events("s4", 28, 5, "C", is_target=True, timeout=True)

    events.append(evt(NBackEventType.GAME_COMPLETED, 35, phase=NBackPhase.COMPLETION))
    return events


def test_reconstruct_and_select_scored_trials_excludes_practice_and_warmup():
    events = full_valid_stream()
    all_trials = reconstruct_trials(events, DEFAULT_CONFIG)
    scored = select_scored_trials(all_trials)

    scored_ids = {t.trial_id for t in scored}
    assert "p1" not in scored_ids  # practice excluded
    assert "w1" not in scored_ids  # warmup excluded
    assert "w2" not in scored_ids  # warmup excluded
    assert scored_ids == {"s1", "s2", "s3", "s4"}


def test_practice_excluded_end_to_end():
    events = full_valid_stream()
    req = NBackCompleteRequest(events=events)
    features = process_nback_completion(ASSESSMENT_ID, req, DEFAULT_CONFIG)
    # 4 scored trials: s1 hit, s2 correct rejection, s3 commission, s4 omission
    assert features.commission_errors == 1
    assert features.omission_errors == 1
    assert features.nback_accuracy == pytest.approx(2 / 4)  # s1 + s2 correct


def test_timeout_classified_as_omission_not_silent_no_response():
    events = full_valid_stream()
    all_trials = reconstruct_trials(events, DEFAULT_CONFIG)
    s4 = next(t for t in all_trials if t.trial_id == "s4")
    assert s4.timed_out is True
    assert s4.response == NBackResponse.NONE
    assert s4.response_latency_ms is None


def test_duplicate_response_uses_first_chronological_response():
    events = [
        evt(NBackEventType.GAME_STARTED, 0, phase=NBackPhase.INTRO),
        evt(NBackEventType.ASSESSMENT_STARTED, 1, phase=NBackPhase.RUNNING),
    ]
    events += build_trial_events(
        "s1", 2, 0, "A", is_target=True,
        response=NBackResponse.MATCH, response_offset=0.5,
        extra_response=NBackResponse.NO_MATCH,
    )
    events.append(evt(NBackEventType.GAME_COMPLETED, 10, phase=NBackPhase.COMPLETION))

    all_trials = reconstruct_trials(events, DEFAULT_CONFIG)
    s1 = next(t for t in all_trials if t.trial_id == "s1")
    # `next()` over timestamp-sorted events picks the earliest response_submitted
    assert s1.response == NBackResponse.MATCH


def test_late_response_beyond_window_reclassified_as_timeout():
    events = [
        evt(NBackEventType.GAME_STARTED, 0, phase=NBackPhase.INTRO),
        evt(NBackEventType.ASSESSMENT_STARTED, 1, phase=NBackPhase.RUNNING),
    ]
    # response arrives 3000ms after presentation; RESPONSE_WINDOW_MS default is 2500
    events += build_trial_events(
        "s1", 2, 0, "A", is_target=True, response=NBackResponse.MATCH, response_offset=3.0,
    )
    events.append(evt(NBackEventType.GAME_COMPLETED, 10, phase=NBackPhase.COMPLETION))

    all_trials = reconstruct_trials(events, DEFAULT_CONFIG)
    s1 = next(t for t in all_trials if t.trial_id == "s1")
    assert s1.timed_out is True
    assert s1.response == NBackResponse.NONE


def test_missing_assessment_started_raises_telemetry_error():
    events = [
        evt(NBackEventType.GAME_STARTED, 0, phase=NBackPhase.INTRO),
    ]
    events += build_trial_events("s1", 2, 0, "A", is_target=True, response=NBackResponse.MATCH)
    events.append(evt(NBackEventType.GAME_COMPLETED, 10, phase=NBackPhase.COMPLETION))
    req = NBackCompleteRequest(events=events)
    with pytest.raises(TelemetryInvalidError):
        process_nback_completion(ASSESSMENT_ID, req, DEFAULT_CONFIG)


def test_no_scored_trials_raises_insufficient_trials():
    events = [
        evt(NBackEventType.GAME_STARTED, 0, phase=NBackPhase.INTRO),
        evt(NBackEventType.ASSESSMENT_STARTED, 1, phase=NBackPhase.RUNNING),
    ]
    # 3 completed trials, all marked warmup -> passes the coarse telemetry
    # "enough completed trials" sanity check, but zero are scoreable, so the
    # failure must surface as InsufficientTrialsError from feature extraction.
    events += build_trial_events("w1", 2, 0, "A", is_target=None, is_warmup=True, response=NBackResponse.NO_MATCH)
    events += build_trial_events("w2", 6, 1, "B", is_target=None, is_warmup=True, response=NBackResponse.NO_MATCH)
    events += build_trial_events("w3", 10, 2, "C", is_target=None, is_warmup=True, response=NBackResponse.NO_MATCH)
    events.append(evt(NBackEventType.GAME_COMPLETED, 20, phase=NBackPhase.COMPLETION))
    req = NBackCompleteRequest(events=events)
    with pytest.raises(InsufficientTrialsError):
        process_nback_completion(ASSESSMENT_ID, req, DEFAULT_CONFIG)
