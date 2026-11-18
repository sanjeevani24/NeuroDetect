from __future__ import annotations

import uuid
from datetime import datetime

from app.games.boston_naming.config import DEFAULT_CONFIG, STIMULUS_LOOKUP
from app.games.boston_naming.exceptions import (
    AssessmentNotFoundError,
    DuplicateCompletionError,
    FeatureComputationError,
    FeatureValidationError,
    InvalidAssessmentIdError,
    TelemetryValidationError,
)
from app.games.boston_naming.features import classify_response, compute_all_features, detect_hesitation_markers
from app.games.boston_naming.schemas import (
    BostonNamingCompleteRequest,
    BostonNamingCompleteResponse,
    BostonNamingEventType,
    BostonNamingFeatures,
    BostonNamingPhase,
    BostonNamingTelemetryEvent,
    CorrectnessLabel,
    CueType,
    ErrorType,
    RecordingStatus,
    ReconstructedNamingTrial,
    TranscriptionStatus,
)
from app.games.boston_naming.validators import validate_features, validate_telemetry
from app.repositories.boston_naming_repository import BostonNamingRepository


def _assessment_window(events: list[BostonNamingTelemetryEvent]) -> tuple[datetime, datetime]:
    started = next((event for event in events if event.event_type == BostonNamingEventType.ASSESSMENT_STARTED), None)
    completed = next((event for event in events if event.event_type == BostonNamingEventType.GAME_COMPLETED), None)
    if started is None or completed is None:
        raise TelemetryValidationError("cannot determine assessment window")
    return started.timestamp, completed.timestamp


def reconstruct_trials(events: list[BostonNamingTelemetryEvent]) -> list[ReconstructedNamingTrial]:
    by_trial: dict[str, list[BostonNamingTelemetryEvent]] = {}
    for event in events:
        if not event.trial_id:
            continue
        by_trial.setdefault(event.trial_id, []).append(event)

    trials: list[ReconstructedNamingTrial] = []
    for trial_id, bucket in by_trial.items():
        ordered = sorted(bucket, key=lambda event: event.timestamp)
        presented = next((event for event in ordered if event.event_type == BostonNamingEventType.STIMULUS_PRESENTED), None)
        completed = next((event for event in ordered if event.event_type == BostonNamingEventType.TRIAL_COMPLETED), None)
        if presented is None or completed is None:
            continue

        stimulus_id = str(presented.metadata.get("stimulus_id"))
        if stimulus_id not in STIMULUS_LOOKUP:
            continue
        stimulus = STIMULUS_LOOKUP[stimulus_id]
        is_practice = presented.phase == BostonNamingPhase.PRACTICE
        recording_started = next((event for event in ordered if event.event_type == BostonNamingEventType.RESPONSE_RECORDING_STARTED), None)
        recording_stopped = next((event for event in ordered if event.event_type == BostonNamingEventType.RESPONSE_RECORDING_STOPPED), None)
        transcription = next((event for event in ordered if event.event_type == BostonNamingEventType.TRANSCRIPTION_COMPLETED), None)
        timeout_event = next((event for event in ordered if event.event_type == BostonNamingEventType.RESPONSE_TIMEOUT), None)
        self_corrected = next((event for event in ordered if event.event_type == BostonNamingEventType.SELF_CORRECTION_DETECTED), None)
        cue_events = [event for event in ordered if event.event_type == BostonNamingEventType.CUE_PRESENTED]

        transcript = None
        transcript_confidence = None
        transcription_status = TranscriptionStatus.UNAVAILABLE
        initial_response = None
        final_response = None
        if transcription is not None:
            transcript = transcription.metadata.get("transcript") or transcription.value
            initial_response = transcription.metadata.get("initial_response")
            final_response = transcription.metadata.get("final_response") or transcript
            transcript_confidence = transcription.metadata.get("transcript_confidence")
            raw_status = str(transcription.metadata.get("transcription_status", "UNAVAILABLE")).upper()
            if raw_status in TranscriptionStatus.__members__:
                transcription_status = TranscriptionStatus[raw_status]

        recording_status = RecordingStatus.SUCCESS
        response_duration_ms = None
        response_started_at = recording_started.timestamp if recording_started else None
        response_completed_at = recording_stopped.timestamp if recording_stopped else None
        response_latency_ms = None
        hesitation_duration_ms = None
        if recording_stopped is not None:
            response_duration_ms = recording_stopped.metadata.get("response_duration_ms")
            raw_status = str(recording_stopped.metadata.get("recording_status", "SUCCESS")).upper()
            if raw_status in RecordingStatus.__members__:
                recording_status = RecordingStatus[raw_status]
            response_latency_ms = recording_stopped.metadata.get("response_latency_ms")
            hesitation_duration_ms = recording_stopped.metadata.get("hesitation_duration_ms")
        if response_latency_ms is None and recording_started is not None:
            response_latency_ms = max(0.0, (recording_started.timestamp - presented.timestamp).total_seconds() * 1000.0)
        if hesitation_duration_ms is None:
            hesitation_duration_ms = response_latency_ms

        semantic_cue_used = any(event.metadata.get("cue_type") == CueType.SEMANTIC.value for event in cue_events)
        phonemic_cue_used = any(event.metadata.get("cue_type") == CueType.PHONEMIC.value for event in cue_events)
        cue_used = semantic_cue_used or phonemic_cue_used
        first_cue_time = cue_events[0].timestamp if cue_events else None
        time_to_cue_ms = ((first_cue_time - presented.timestamp).total_seconds() * 1000.0) if first_cue_time else None

        timeout = timeout_event is not None
        correctness, error_type, normalized = classify_response(
            stimulus_id=stimulus_id,
            transcript=final_response or transcript,
            timeout=timeout,
            recording_status=recording_status.value,
        )

        response_after_cue_ms = None
        if first_cue_time is not None and response_started_at is not None and response_started_at >= first_cue_time:
            response_after_cue_ms = (response_started_at - first_cue_time).total_seconds() * 1000.0
        if transcript_confidence is not None:
            transcript_confidence = float(transcript_confidence)

        self_corrected_flag = None
        self_correction_latency_ms = None
        if self_corrected is not None:
            self_corrected_flag = True
            self_correction_latency_ms = self_corrected.metadata.get("self_correction_latency_ms")
            initial_response = self_corrected.metadata.get("initial_response") or initial_response
            final_response = self_corrected.metadata.get("final_response") or final_response

        trials.append(
            ReconstructedNamingTrial(
                trial_id=trial_id,
                trial_index=int(presented.metadata.get("trial_index")),
                stimulus_id=stimulus_id,
                difficulty=stimulus.difficulty,
                is_practice=is_practice,
                stimulus_presented_at=presented.timestamp,
                response_started_at=response_started_at,
                response_completed_at=response_completed_at,
                audio_start_timestamp=recording_started.timestamp if recording_started else None,
                audio_end_timestamp=recording_stopped.timestamp if recording_stopped else None,
                response_duration_ms=float(response_duration_ms) if response_duration_ms is not None else None,
                response_latency_ms=response_latency_ms,
                transcript=transcript,
                transcript_confidence=transcript_confidence,
                transcription_status=transcription_status,
                normalized_response=normalized,
                initial_response=initial_response,
                final_response=final_response or transcript,
                correctness=correctness,
                error_type=error_type,
                cue_used=cue_used,
                semantic_cue_used=semantic_cue_used,
                phonemic_cue_used=phonemic_cue_used,
                time_to_cue_ms=time_to_cue_ms,
                response_after_cue_ms=response_after_cue_ms,
                correct_after_cue=cue_used and correctness == CorrectnessLabel.CORRECT,
                self_corrected=self_corrected_flag,
                self_correction_latency_ms=float(self_correction_latency_ms) if self_correction_latency_ms is not None else None,
                hesitation_duration_ms=hesitation_duration_ms,
                number_of_hesitation_markers=detect_hesitation_markers(final_response or transcript),
                timeout=timeout,
                recording_status=recording_status,
            )
        )

    trials.sort(key=lambda trial: trial.trial_index)
    return trials


def select_scored_trials(trials: list[ReconstructedNamingTrial]) -> list[ReconstructedNamingTrial]:
    return [trial for trial in trials if not trial.is_practice]


def process_boston_naming_completion(
    assessment_id: str,
    request: BostonNamingCompleteRequest,
) -> BostonNamingFeatures:
    validate_telemetry(request, assessment_id)
    trials = reconstruct_trials(request.events)
    scored_trials = select_scored_trials(trials)
    if len(scored_trials) != DEFAULT_CONFIG.TOTAL_SCORED_TRIALS:
        raise FeatureComputationError(
            f"expected {DEFAULT_CONFIG.TOTAL_SCORED_TRIALS} scored trials, received {len(scored_trials)}"
        )
    assessment_started_at, assessment_completed_at = _assessment_window(request.events)
    features = BostonNamingFeatures(
        **compute_all_features(scored_trials, assessment_started_at, assessment_completed_at)
    )
    validate_features(features)
    return features


class BostonNamingService:
    def __init__(self, repository: BostonNamingRepository):
        self._repository = repository

    def complete_game(
        self,
        assessment_id: str,
        request: BostonNamingCompleteRequest,
    ) -> BostonNamingCompleteResponse:
        try:
            uuid.UUID(assessment_id)
        except ValueError as exc:
            raise InvalidAssessmentIdError("assessment_id must be a valid UUID.") from exc

        if not self._repository.assessment_exists(assessment_id):
            raise AssessmentNotFoundError(f"assessment_id '{assessment_id}' does not exist.")

        if self._repository.result_exists(assessment_id):
            raise DuplicateCompletionError(
                f"Boston Naming has already been completed for assessment_id '{assessment_id}'."
            )

        features = process_boston_naming_completion(assessment_id, request)
        self._repository.insert_result(assessment_id, features)
        return BostonNamingCompleteResponse(
            assessment_id=assessment_id,
            game="boston_naming",
            status="completed",
            features=features,
        )
