import pytest

from app.games.memory.exceptions import FeatureValidationError
from app.games.memory.features import ExtractedFeatures
from app.games.memory.validators import validate_features


def _valid_features(**overrides) -> ExtractedFeatures:
    base = dict(
        immediate_recall_accuracy=0.75,
        delayed_recall_accuracy=0.5,
        recognition_accuracy=0.9,
        recall_decay_rate=0.2,
        recall_latency=3.0,
        omission_errors=5,
        intrusion_errors=1,
        sequence_recall_accuracy=1.0,
        hesitation_duration=0.0,
        retry_frequency=0,
        confidence_variability=1.0,
        completion_time=151.0,
        memory_consistency_trend=0.7,
    )
    base.update(overrides)
    return ExtractedFeatures(**base)


def test_valid_features_pass():
    validate_features(_valid_features())  # should not raise


def test_negative_omission_errors_rejected():
    with pytest.raises(FeatureValidationError):
        validate_features(_valid_features(omission_errors=-1))


def test_completion_time_must_be_positive():
    with pytest.raises(FeatureValidationError):
        validate_features(_valid_features(completion_time=0))


def test_accuracy_out_of_range_rejected():
    with pytest.raises(FeatureValidationError):
        validate_features(_valid_features(immediate_recall_accuracy=1.2))


def test_negative_hesitation_rejected():
    with pytest.raises(FeatureValidationError):
        validate_features(_valid_features(hesitation_duration=-0.1))


def test_multiple_errors_all_reported():
    with pytest.raises(FeatureValidationError) as exc_info:
        validate_features(
            _valid_features(immediate_recall_accuracy=2.0, omission_errors=-3, completion_time=-1)
        )
    assert len(exc_info.value.errors) == 3
