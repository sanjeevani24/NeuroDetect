import pytest

from app.games.mmse.exceptions import FeatureValidationError
from app.games.mmse.features import ExtractedMMSEFeatures
from app.games.mmse.validators import validate_features


def _valid_features(**overrides) -> ExtractedMMSEFeatures:
    base = dict(
        orientation_accuracy=0.8,
        registration_accuracy=0.7,
        attention_accuracy=0.8,
        serial7_accuracy=0.8,
        delayed_recall_accuracy=0.7,
        language_accuracy=1.0,
        command_following_accuracy=1.0,
        response_latency=0.8,
        latency_variability=0.0,
        omission_errors=0,
        intrusion_errors=2,
        correction_frequency=0.05,
        completion_time=60.0,
        performance_consistency=0.9,
    )
    base.update(overrides)
    return ExtractedMMSEFeatures(**base)


def test_valid_features_pass():
    validate_features(_valid_features())


def test_accuracy_out_of_range_rejected():
    with pytest.raises(FeatureValidationError):
        validate_features(_valid_features(orientation_accuracy=1.4))


def test_completion_time_must_be_positive():
    with pytest.raises(FeatureValidationError):
        validate_features(_valid_features(completion_time=0))


def test_negative_intrusion_errors_rejected():
    with pytest.raises(FeatureValidationError):
        validate_features(_valid_features(intrusion_errors=-1))
