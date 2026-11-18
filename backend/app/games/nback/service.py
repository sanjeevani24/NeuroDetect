"""
N-Back service layer.

Orchestrates:
    telemetry events -> reconstructed trials -> 12 features -> validation -> persistence

Trial reconstruction is intentionally done server-side from raw events
(rather than trusting a frontend-computed summary) so that every scored
trial is reconstructable and auditable from telemetry alone (spec section 14).
"""
from __future__ import annotations

from datetime import datetime
import uuid

from app.games.nback.config import NBackConfig, DEFAULT_CONFIG
from app.games.nback.features import FeatureComputationError, compute_all_features
from app.games.nback.schemas import (
    NBackCompleteRequest,
    NBackCompleteResponse,
    NBackEventType,
    NBackFeatures,
    NBackPhase,
    NBackResponse,
    ReconstructedTrial,
)
from app.games.nback.validators import (
    FeatureValidationError,
    TelemetryValidationError,
    validate_features,
    validate_telemetry,
)
from app.repositories.nback_repository import NBackRepository


class NBackServiceError(Exception):
    """Base class for service-level failures the router translates to HTTP errors."""


class AssessmentNotFoundError(NBackServiceError):
    pass


class DuplicateCompletionError(NBackServiceError):
    pass


class TelemetryInvalidError(NBackServiceError):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class FeaturesInvalidError(NBackServiceError):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InsufficientTrialsError(NBackServiceError):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidAssessmentIdError(NBackServiceError):
    pass


# ---------------------------------------------------------------------------
# Trial reconstruction
# ---------------------------------------------------------------------------

def _correct_answer_for(is_target: bool | None) -> NBackResponse | None:
    if is_target is None:
        return None
    return NBackResponse.MATCH if is_target else NBackResponse.NO_MATCH


def reconstruct_trials(
    events: list,
    config: NBackConfig = DEFAULT_CONFIG,
) -> list[ReconstructedTrial]:
    """
    Groups events by trial_id and reconstructs one ReconstructedTrial per
    trial that reached trial_completed. Practice trials (phase == practice,
    or event_type starts with practice_) are reconstructed too, so the
    caller can explicitly exclude them — never silently dropped without a
    reason.
    """
    by_trial: dict[str, dict] = {}

    for e in events:
        if e.trial_id is None:
            continue
        bucket = by_trial.setdefault(e.trial_id, {"events": []})
        bucket["events"].append(e)

    trials: list[ReconstructedTrial] = []

    for trial_id, bucket in by_trial.items():
        ev_list = sorted(bucket["events"], key=lambda e: e.timestamp)

        started = next(
            (e for e in ev_list if e.event_type in (NBackEventType.TRIAL_STARTED,)), None
        )
        presented = next(
            (e for e in ev_list if e.event_type == NBackEventType.STIMULUS_PRESENTED), None
        )
        completed = next(
            (e for e in ev_list if e.event_type == NBackEventType.TRIAL_COMPLETED), None
        )
        response_evt = next(
            (e for e in ev_list if e.event_type == NBackEventType.RESPONSE_SUBMITTED), None
        )
        timeout_evt = next(
            (e for e in ev_list if e.event_type == NBackEventType.RESPONSE_TIMEOUT), None
        )
        is_practice = any(
            e.event_type
            in (
                NBackEventType.PRACTICE_TRIAL_STARTED,
                NBackEventType.PRACTICE_RESPONSE,
            )
            or e.phase == NBackPhase.PRACTICE
            for e in ev_list
        )

        if presented is None or completed is None:
            # Cannot reconstruct without at minimum a presentation and a completion.
            continue

        meta = presented.metadata or {}
        trial_index = meta.get("trial_index")
        stimulus = meta.get("stimulus")
        is_target = meta.get("is_target")  # bool or None (warmup trials carry None)
        is_warmup = bool(meta.get("is_warmup", False))

        if trial_index is None or stimulus is None:
            # Malformed telemetry: presentation event missing required metadata.
            continue

        response = NBackResponse.NONE
        response_at = None
        response_latency_ms = None
        timed_out = timeout_evt is not None

        if response_evt is not None and not timed_out:
            raw_response = response_evt.value
            if raw_response in (NBackResponse.MATCH.value, NBackResponse.NO_MATCH.value):
                response = NBackResponse(raw_response)
                response_at = response_evt.timestamp
                response_latency_ms = (
                    response_at - presented.timestamp
                ).total_seconds() * 1000.0
                # A response arriving after the configured window is a timeout,
                # not a valid response — classify it explicitly (spec section 10).
                if response_latency_ms > config.RESPONSE_WINDOW_MS:
                    timed_out = True
                    response = NBackResponse.NONE
                    response_at = None
                    response_latency_ms = None

        trials.append(
            ReconstructedTrial(
                trial_id=trial_id,
                trial_index=int(trial_index),
                stimulus=str(stimulus),
                is_warmup=is_warmup,
                is_practice=is_practice,
                is_target=is_target,
                presented_at=presented.timestamp,
                response_started_at=started.timestamp if started else presented.timestamp,
                response_at=response_at,
                response=response,
                correct_answer=_correct_answer_for(is_target),
                response_latency_ms=response_latency_ms,
                timed_out=timed_out,
            )
        )

    trials.sort(key=lambda t: t.trial_index)
    return trials


def select_scored_trials(trials: list[ReconstructedTrial]) -> list[ReconstructedTrial]:
    """
    Scored trials = not practice, not warmup, and is_target is not None
    (warmup trials have no valid 2-back comparison and are excluded from
    scoring by design — spec section 5/9).
    """
    return [t for t in trials if not t.is_practice and not t.is_warmup and t.is_target is not None]


def _assessment_window(events: list) -> tuple[datetime, datetime]:
    started = next((e for e in events if e.event_type == NBackEventType.ASSESSMENT_STARTED), None)
    completed = next((e for e in events if e.event_type == NBackEventType.GAME_COMPLETED), None)
    if started is None or completed is None:
        raise TelemetryValidationError(
            "cannot determine assessment window: missing assessment_started or game_completed event"
        )
    return started.timestamp, completed.timestamp


# ---------------------------------------------------------------------------
# Orchestration entrypoint
# ---------------------------------------------------------------------------

def process_nback_completion(
    assessment_id: str,
    request: NBackCompleteRequest,
    config: NBackConfig = DEFAULT_CONFIG,
) -> NBackFeatures:
    """
    Full pipeline: validate telemetry -> reconstruct trials -> exclude
    practice/warmup -> compute 12 features -> validate features.

    Does NOT touch the database — repository/router layer is responsible for
    assessment-existence checks and persistence (including the
    duplicate-completion / unique assessment_id guarantee).
    """
    try:
        validate_telemetry(request, assessment_id, config)
    except TelemetryValidationError as exc:
        raise TelemetryInvalidError(str(exc)) from exc

    all_trials = reconstruct_trials(request.events, config)
    scored_trials = select_scored_trials(all_trials)

    if len(scored_trials) < 1:
        raise InsufficientTrialsError(
            "no scored trials could be reconstructed from telemetry"
        )

    try:
        started_at, completed_at = _assessment_window(request.events)
    except TelemetryValidationError as exc:
        raise TelemetryInvalidError(str(exc)) from exc

    try:
        raw_features = compute_all_features(scored_trials, started_at, completed_at)
    except FeatureComputationError as exc:
        raise InsufficientTrialsError(str(exc)) from exc

    raw_features.pop("_flags", None)
    features = NBackFeatures(**raw_features)

    try:
        validate_features(features)
    except FeatureValidationError as exc:
        raise FeaturesInvalidError(str(exc)) from exc

    return features


class NBackGameService:
    def __init__(self, repository: NBackRepository, config: NBackConfig = DEFAULT_CONFIG):
        self._repository = repository
        self._config = config

    def complete_game(self, assessment_id: str, request: NBackCompleteRequest) -> NBackCompleteResponse:
        try:
            uuid.UUID(assessment_id)
        except ValueError as exc:
            raise InvalidAssessmentIdError("assessment_id must be a valid UUID.") from exc

        if not self._repository.assessment_exists(assessment_id):
            raise AssessmentNotFoundError(f"assessment_id '{assessment_id}' does not exist.")

        if self._repository.result_exists(assessment_id):
            raise DuplicateCompletionError(
                f"N-Back has already been completed for assessment_id '{assessment_id}'."
            )

        features = process_nback_completion(assessment_id, request, self._config)
        self._repository.insert_result(assessment_id, features)

        return NBackCompleteResponse(
            assessment_id=assessment_id,
            game="nback",
            status="completed",
            features=features,
        )
