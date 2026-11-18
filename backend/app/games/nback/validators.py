"""
Validation layer for N-Back.

Two responsibilities, kept separate on purpose:

1. Telemetry validation — is the incoming event stream well-formed enough to
   reconstruct trials from? (structural / referential checks)
2. Feature validation — are the 12 computed features within their locked
   valid ranges (spec section 16)? Invalid feature sets are REJECTED, never
   silently coerced to a default.
"""
from __future__ import annotations

import math
from datetime import datetime

from app.games.nback.config import NBackConfig
from app.games.nback.schemas import (
    NBackCompleteRequest,
    NBackEventType,
    NBackFeatures,
)


class TelemetryValidationError(Exception):
    """Malformed or insufficient telemetry — request should be rejected (422)."""


class FeatureValidationError(Exception):
    """A computed feature fell outside its locked valid range."""


# ---------------------------------------------------------------------------
# Telemetry validation
# ---------------------------------------------------------------------------

def validate_telemetry(
    request: NBackCompleteRequest,
    assessment_id: str,
    config: NBackConfig,
) -> None:
    """
    Structural checks before any trial reconstruction is attempted.
    Raises TelemetryValidationError with a descriptive message on failure.
    """
    events = request.events

    if not events:
        raise TelemetryValidationError("event list is empty")

    for e in events:
        if e.assessment_id != assessment_id:
            raise TelemetryValidationError(
                f"event.assessment_id '{e.assessment_id}' does not match "
                f"path assessment_id '{assessment_id}'"
            )

    event_types = {e.event_type for e in events}

    required = {
        NBackEventType.GAME_STARTED,
        NBackEventType.ASSESSMENT_STARTED,
        NBackEventType.GAME_COMPLETED,
    }
    missing = required - event_types
    if missing:
        raise TelemetryValidationError(
            f"missing required event types: {sorted(m.value for m in missing)}"
        )

    # Every non-warmup, non-practice trial_completed event needs a matching
    # trial_started + stimulus_presented with the same trial_id.
    trial_ids_started = {e.trial_id for e in events if e.event_type == NBackEventType.TRIAL_STARTED}
    trial_ids_presented = {
        e.trial_id for e in events if e.event_type == NBackEventType.STIMULUS_PRESENTED
    }
    trial_ids_completed = {
        e.trial_id for e in events if e.event_type == NBackEventType.TRIAL_COMPLETED
    }

    orphaned_completions = trial_ids_completed - trial_ids_started
    if orphaned_completions:
        raise TelemetryValidationError(
            f"trial_completed events with no matching trial_started: {orphaned_completions}"
        )

    unpresented = trial_ids_completed - trial_ids_presented
    if unpresented:
        raise TelemetryValidationError(
            f"trial_completed events with no stimulus_presented event: {unpresented}"
        )

    # Duplicate completion detection (spec: prevent duplicate trial completion)
    completed_list = [e.trial_id for e in events if e.event_type == NBackEventType.TRIAL_COMPLETED]
    if len(completed_list) != len(set(completed_list)):
        raise TelemetryValidationError("duplicate trial_completed events detected for the same trial_id")

    # Duplicate game completion detection
    game_completed_count = sum(1 for e in events if e.event_type == NBackEventType.GAME_COMPLETED)
    if game_completed_count > 1:
        raise TelemetryValidationError("duplicate game_completed events detected")

    scored_trial_count = len(
        trial_ids_completed
        - {
            e.trial_id
            for e in events
            if e.event_type in (NBackEventType.PRACTICE_TRIAL_STARTED, NBackEventType.PRACTICE_RESPONSE)
        }
    )
    if scored_trial_count < config.WARMUP_TRIALS + 1:
        raise TelemetryValidationError(
            "insufficient completed trials to reconstruct any scored trial"
        )


# ---------------------------------------------------------------------------
# Feature validation (spec section 16 — LOCKED ranges)
# ---------------------------------------------------------------------------

def _check_range(name: str, value: float, lo: float, hi: float, inclusive_hi: bool = True) -> None:
    if not (lo <= value and (value <= hi if inclusive_hi else value < hi)):
        raise FeatureValidationError(f"{name}={value} is outside valid range [{lo}, {hi}]")


def validate_features(features: NBackFeatures) -> None:
    """
    Rejects (raises) on any out-of-range feature. Never coerces or replaces
    invalid values with a default — per spec section 16.
    """
    _check_range("nback_accuracy", features.nback_accuracy, 0.0, 1.0)
    _check_range("hit_rate", features.hit_rate, 0.0, 1.0)
    _check_range("false_alarm_rate", features.false_alarm_rate, 0.0, 1.0)
    _check_range("sensitivity", features.sensitivity, -1.0, 1.0)

    if features.response_latency < 0:
        raise FeatureValidationError(f"response_latency={features.response_latency} must be >= 0")

    if features.latency_variability < 0:
        raise FeatureValidationError(
            f"latency_variability={features.latency_variability} must be >= 0"
        )

    if features.omission_errors < 0:
        raise FeatureValidationError(f"omission_errors={features.omission_errors} must be >= 0")

    if features.commission_errors < 0:
        raise FeatureValidationError(f"commission_errors={features.commission_errors} must be >= 0")

    if not math.isfinite(features.d_prime):
        raise FeatureValidationError("d_prime must be a finite number")

    if features.response_consistency < 0:
        raise FeatureValidationError(
            f"response_consistency={features.response_consistency} must be >= 0"
        )

    _check_range("fatigue_trend", features.fatigue_trend, -1.0, 1.0)

    if features.completion_time <= 0:
        raise FeatureValidationError(f"completion_time={features.completion_time} must be > 0")
