import math

import pytest

from app.ml.model1.config import MODEL_FEATURE_NAMES
from app.ml.model1.exceptions import Model1FeatureValidationError, Model1IncompleteAssessmentError
from app.ml.model1.feature_aggregator import Model1FeatureAggregator, validate_model1_features


ASSESSMENT_ID = "77777777-7777-4777-8777-777777777777"


class FakeRepository:
    def __init__(self, row):
        self._row = row

    def get_by_assessment(self, assessment_id: str):
        return self._row


def build_boston_trials():
    return [
        {
            "trial_id": f"trial-{index}",
            "transcript": "clock face",
            "final_response": "clock face",
            "response_duration_ms": 1500 + index * 10,
            "response_latency_ms": 1200 + index * 5,
        }
        for index in range(20)
    ]


def build_aggregator(
    *,
    mmse=None,
    memory=None,
    nback=None,
    boston=None,
    trail=None,
):
    return Model1FeatureAggregator(
        mmse_repository=FakeRepository(
            mmse
            or {
                "orientation_accuracy": 0.8,
                "registration_accuracy": 1.0,
                "attention_accuracy": 0.6,
                "delayed_recall_accuracy": 2 / 3,
                "language_accuracy": 5 / 6,
                "command_following_accuracy": 1.0,
                "response_latency": 1.4,
                "latency_variability": 0.25,
                "omission_errors": 2,
                "correction_frequency": 0.1,
                "performance_consistency": 0.82,
                "completion_time": 80.0,
            }
        ),
        memory_repository=FakeRepository(
            memory
            or {
                "immediate_recall_accuracy": 0.8,
                "delayed_recall_accuracy": 0.6,
                "recognition_accuracy": 0.9,
                "recall_decay_rate": 0.25,
                "recall_latency": 1.7,
                "omission_errors": 1,
                "intrusion_errors": 0,
                "sequence_recall_accuracy": 0.75,
                "retry_frequency": 2,
                "memory_consistency_trend": 0.7,
            }
        ),
        nback_repository=FakeRepository(
            nback
            or {
                "nback_accuracy": 0.78,
                "hit_rate": 0.75,
                "false_alarm_rate": 0.1,
                "omission_errors": 4,
                "response_consistency": 0.84,
                "fatigue_trend": -0.08,
                "response_latency": 1.1,
                "completion_time": 95.0,
            }
        ),
        boston_repository=FakeRepository(
            boston
            or {
                "naming_accuracy": 0.8,
                "mean_response_latency_ms": 1300.0,
                "semantic_errors": 1,
                "phonemic_errors": 1,
                "total_cue_rate": 0.2,
                "omission_errors": 1,
                "completion_time_ms": 100000.0,
                "raw_trials": build_boston_trials(),
            }
        ),
        trail_repository=FakeRepository(
            trail
            or {
                "path_efficiency": 0.85,
                "sequence_accuracy": 0.92,
                "switching_delay": 980.0,
                "backtracking_frequency": 0.08,
                "rule_violation_count": 2,
                "cursor_movement_entropy": 1.8,
                "trajectory_deviation": 0.15,
                "tremor_jitter_frequency": 0.12,
            }
        ),
    )


def test_feature_vector_has_exact_names_and_order():
    aggregator = build_aggregator()
    feature_vector = aggregator.build_feature_vector(ASSESSMENT_ID)
    assert list(feature_vector.keys()) == MODEL_FEATURE_NAMES
    assert len(feature_vector) == 47


def test_missing_game_detection():
    aggregator = build_aggregator(memory=None)
    aggregator = Model1FeatureAggregator(
        mmse_repository=aggregator._mmse_repository,
        memory_repository=FakeRepository(None),
        nback_repository=aggregator._nback_repository,
        boston_repository=aggregator._boston_repository,
        trail_repository=aggregator._trail_repository,
    )
    with pytest.raises(Model1IncompleteAssessmentError) as exc:
        aggregator.build_feature_vector(ASSESSMENT_ID)
    assert "Memory Recall" in exc.value.missing_games


def test_nan_feature_is_rejected():
    with pytest.raises(Model1FeatureValidationError):
        validate_model1_features({name: (float("nan") if name == MODEL_FEATURE_NAMES[0] else 1.0) for name in MODEL_FEATURE_NAMES})


def test_infinite_feature_is_rejected():
    with pytest.raises(Model1FeatureValidationError):
        validate_model1_features({name: (float("inf") if name == MODEL_FEATURE_NAMES[1] else 1.0) for name in MODEL_FEATURE_NAMES})


def test_feature_values_are_finite():
    aggregator = build_aggregator()
    feature_vector = aggregator.build_feature_vector(ASSESSMENT_ID)
    assert all(math.isfinite(value) for value in feature_vector.values())
