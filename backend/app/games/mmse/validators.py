from __future__ import annotations

import math

from app.games.mmse.exceptions import FeatureValidationError
from app.games.mmse.features import ExtractedMMSEFeatures


def _check_range(name: str, value: float, low: float, high: float, errors: list[str]) -> None:
    if not (low <= value <= high):
        errors.append(f"{name}={value} is outside allowed range [{low}, {high}]")


def _check_min(name: str, value: float, minimum: float, inclusive: bool, errors: list[str]) -> None:
    ok = value >= minimum if inclusive else value > minimum
    if not ok:
        bound = ">=" if inclusive else ">"
        errors.append(f"{name}={value} must be {bound} {minimum}")


def _check_finite(name: str, value: float, errors: list[str]) -> None:
    if math.isnan(value) or math.isinf(value):
        errors.append(f"{name} is NaN or infinite: {value}")


def validate_features(features: ExtractedMMSEFeatures) -> None:
    errors: list[str] = []
    range_fields = (
        "orientation_accuracy",
        "registration_accuracy",
        "attention_accuracy",
        "serial7_accuracy",
        "delayed_recall_accuracy",
        "language_accuracy",
        "command_following_accuracy",
        "correction_frequency",
        "performance_consistency",
    )
    for name in range_fields:
        value = getattr(features, name)
        _check_finite(name, value, errors)
        _check_range(name, value, 0.0, 1.0, errors)

    min_zero_fields = ("response_latency", "latency_variability")
    for name in min_zero_fields:
        value = getattr(features, name)
        _check_finite(name, value, errors)
        _check_min(name, value, 0.0, inclusive=True, errors=errors)

    for name in ("omission_errors", "intrusion_errors"):
        _check_min(name, getattr(features, name), 0, inclusive=True, errors=errors)

    _check_finite("completion_time", features.completion_time, errors)
    _check_min("completion_time", features.completion_time, 0.0, inclusive=False, errors=errors)

    if errors:
        raise FeatureValidationError(errors)
