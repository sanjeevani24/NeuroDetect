from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.games.boston_naming.config import SCORED_STIMULI, PRACTICE_STIMULI
from app.games.boston_naming.exceptions import AssessmentNotFoundError, DuplicateCompletionError, InvalidAssessmentIdError
from app.games.boston_naming.schemas import (
    BostonNamingCompleteRequest,
    BostonNamingEventType,
    BostonNamingPhase,
    BostonNamingTelemetryEvent,
)
from app.games.boston_naming.service import BostonNamingService, process_boston_naming_completion, reconstruct_trials, select_scored_trials

ASSESSMENT_ID = "22222222-2222-2222-2222-222222222222"
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


def full_request() -> BostonNamingCompleteRequest:
    events = [
        evt(BostonNamingEventType.GAME_STARTED, 0, phase=BostonNamingPhase.INTRO),
        evt(BostonNamingEventType.PRACTICE_STARTED, 1, phase=BostonNamingPhase.PRACTICE),
    ]
    time_cursor = 2
    for index, stimulus in enumerate(PRACTICE_STIMULI, start=1):
        trial_id = f"p-{index}"
        events += [
            evt(BostonNamingEventType.PRACTICE_TRIAL_STARTED, time_cursor, phase=BostonNamingPhase.PRACTICE, trial_id=trial_id),
            evt(BostonNamingEventType.STIMULUS_PRESENTED, time_cursor, phase=BostonNamingPhase.PRACTICE, trial_id=trial_id, metadata={"trial_index": index, "stimulus_id": stimulus.stimulus_id}),
            evt(BostonNamingEventType.RESPONSE_RECORDING_STARTED, time_cursor + 0.2, phase=BostonNamingPhase.PRACTICE, trial_id=trial_id),
            evt(BostonNamingEventType.RESPONSE_RECORDING_STOPPED, time_cursor + 0.8, phase=BostonNamingPhase.PRACTICE, trial_id=trial_id, metadata={"response_duration_ms": 600, "recording_status": "SUCCESS"}),
            evt(BostonNamingEventType.TRANSCRIPTION_COMPLETED, time_cursor + 0.9, phase=BostonNamingPhase.PRACTICE, trial_id=trial_id, metadata={"transcript": stimulus.canonical_name, "final_response": stimulus.canonical_name, "transcription_status": "SUCCESS", "transcript_confidence": 0.9}),
            evt(BostonNamingEventType.PRACTICE_RESPONSE, time_cursor + 1.0, phase=BostonNamingPhase.PRACTICE, trial_id=trial_id),
            evt(BostonNamingEventType.TRIAL_COMPLETED, time_cursor + 1.2, phase=BostonNamingPhase.PRACTICE, trial_id=trial_id),
        ]
        time_cursor += 2
    events.append(evt(BostonNamingEventType.PRACTICE_COMPLETED, time_cursor, phase=BostonNamingPhase.PRACTICE))
    time_cursor += 1
    events.append(evt(BostonNamingEventType.ASSESSMENT_STARTED, time_cursor))
    time_cursor += 1

    for index, stimulus in enumerate(SCORED_STIMULI, start=1):
        trial_id = f"s-{index}"
        base = {
            "trial_index": index,
            "stimulus_id": stimulus.stimulus_id,
            "difficulty": stimulus.difficulty.value,
        }
        events.append(evt(BostonNamingEventType.TRIAL_STARTED, time_cursor, trial_id=trial_id))
        events.append(evt(BostonNamingEventType.STIMULUS_PRESENTED, time_cursor, trial_id=trial_id, metadata=base))
        if index in {5, 14}:
            events.append(evt(BostonNamingEventType.RESPONSE_TIMEOUT, time_cursor + 5.2, trial_id=trial_id))
        else:
            if index in {7, 16}:
                events.append(evt(BostonNamingEventType.CUE_PRESENTED, time_cursor + 5.0, trial_id=trial_id, metadata={"cue_type": "semantic"}))
            if index in {16}:
                events.append(evt(BostonNamingEventType.CUE_PRESENTED, time_cursor + 8.0, trial_id=trial_id, metadata={"cue_type": "phonemic"}))
            events.append(evt(BostonNamingEventType.RESPONSE_RECORDING_STARTED, time_cursor + 1.0, trial_id=trial_id))
            events.append(evt(BostonNamingEventType.RESPONSE_RECORDING_STOPPED, time_cursor + 1.8, trial_id=trial_id, metadata={"response_duration_ms": 800, "recording_status": "SUCCESS"}))
            transcript = stimulus.canonical_name
            if index == 7:
                transcript = stimulus.category
            if index == 9:
                transcript = "random word"
            if index == 16:
                transcript = stimulus.canonical_name
                events.append(evt(BostonNamingEventType.SELF_CORRECTION_DETECTED, time_cursor + 1.6, trial_id=trial_id, metadata={"initial_response": "wrong", "final_response": stimulus.canonical_name, "self_correction_latency_ms": 300}))
            events.append(evt(BostonNamingEventType.TRANSCRIPTION_COMPLETED, time_cursor + 1.9, trial_id=trial_id, metadata={"transcript": transcript, "final_response": transcript, "transcription_status": "SUCCESS", "transcript_confidence": 0.91}))
        events.append(evt(BostonNamingEventType.TRIAL_COMPLETED, time_cursor + 2.2, trial_id=trial_id))
        time_cursor += 3

    events.append(evt(BostonNamingEventType.GAME_COMPLETED, time_cursor + 1, phase=BostonNamingPhase.COMPLETION))
    return BostonNamingCompleteRequest(events=events)


class FakeRepository:
    def __init__(self, *, assessment_exists=True, result_exists=False):
        self._assessment_exists = assessment_exists
        self._result_exists = result_exists
        self.inserted = None

    def assessment_exists(self, assessment_id: str) -> bool:
        return self._assessment_exists

    def result_exists(self, assessment_id: str) -> bool:
        return self._result_exists

    def insert_result(self, assessment_id: str, features):
        self.inserted = (assessment_id, features)
        return {}


def test_reconstruct_trials_and_exclude_practice():
    request = full_request()
    trials = reconstruct_trials(request.events)
    assert len(trials) == 23
    assert len(select_scored_trials(trials)) == 20


def test_process_completion_computes_features():
    features = process_boston_naming_completion(ASSESSMENT_ID, full_request())
    assert 0 <= features.naming_accuracy <= 1
    assert len(features.raw_trials) == 20
    assert features.omission_errors == 2


def test_service_rejects_bad_uuid():
    with pytest.raises(InvalidAssessmentIdError):
        BostonNamingService(FakeRepository()).complete_game("not-a-uuid", full_request())


def test_service_rejects_missing_assessment():
    with pytest.raises(AssessmentNotFoundError):
        BostonNamingService(FakeRepository(assessment_exists=False)).complete_game(ASSESSMENT_ID, full_request())


def test_service_rejects_duplicate_completion():
    with pytest.raises(DuplicateCompletionError):
        BostonNamingService(FakeRepository(result_exists=True)).complete_game(ASSESSMENT_ID, full_request())
