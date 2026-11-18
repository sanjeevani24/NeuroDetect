"""
Explicit range validation for derived Memory Recall features.

This runs BEFORE database insertion. It is deliberately independent of the
Pydantic schema constraints in schemas.py (defense in depth) and produces a
human-readable list of every violation rather than stopping at the first
one, so failures are easy to diagnose. Nothing here silently coerces an
invalid value to zero or to an in-range value — invalid data is rejected.
"""
from __future__ import annotations

import math

from app.games.memory.exceptions import FeatureValidationError
from app.games.memory.features import ExtractedFeatures

_RANGE_01 = (0.0, 1.0)


def _check_finite(name: str, value: float, errors: list[str]) -> None:
    if math.isnan(value) or math.isinf(value):
        errors.append(f"{name} is NaN or infinite: {value}")


def _check_range(name: str, value: float, low: float, high: float, errors: list[str]) -> None:
    if not (low <= value <= high):
        errors.append(f"{name}={value} is outside allowed range [{low}, {high}]")


def _check_min(name: str, value: float, minimum: float, inclusive: bool, errors: list[str]) -> None:
    ok = value >= minimum if inclusive else value > minimum
    if not ok:
        bound = ">=" if inclusive else ">"
        errors.append(f"{name}={value} must be {bound} {minimum}")


def validate_features(features: ExtractedFeatures) -> None:
    errors: list[str] = []

    for name in (
        "immediate_recall_accuracy",
        "delayed_recall_accuracy",
        "recognition_accuracy",
        "recall_decay_rate",
        "sequence_recall_accuracy",
        "memory_consistency_trend",
    ):
        value = getattr(features, name)
        _check_finite(name, value, errors)
        _check_range(name, value, *_RANGE_01, errors)

    for name in ("hesitation_duration", "recall_latency", "confidence_variability"):
        value = getattr(features, name)
        _check_finite(name, value, errors)
        _check_min(name, value, 0.0, inclusive=True, errors=errors)

    for name in ("omission_errors", "intrusion_errors", "retry_frequency"):
        value = getattr(features, name)
        _check_min(name, value, 0, inclusive=True, errors=errors)

    _check_finite("completion_time", features.completion_time, errors)
    _check_min("completion_time", features.completion_time, 0.0, inclusive=False, errors=errors)

    if errors:
        raise FeatureValidationError(errors)
