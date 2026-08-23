import math

from app.ml.model1.config import MODEL_FEATURE_NAMES
from app.ml.model1.model import get_model1_booster, load_feature_schema, load_model_metadata, predict_cognitive_performance


def build_feature_vector() -> dict[str, float]:
    return {
        "overall_mmse_score": 24.0,
        "orientation_score": 0.8,
        "attention_score": 0.6,
        "recall_score": 0.67,
        "language_score": 0.83,
        "question_accuracy": 0.74,
        "mean_reaction_time": 1.35,
        "reaction_time_variance": 0.24,
        "hesitation_duration": 0.18,
        "correction_frequency": 0.12,
        "skip_frequency": 0.06,
        "confidence_variability": 0.22,
        "completion_time": 86.0,
        "error_recovery_time": 0.16,
        "immediate_recall_accuracy": 0.78,
        "delayed_recall_accuracy": 0.67,
        "recognition_accuracy": 0.9,
        "recall_decay_rate": 0.14,
        "recall_latency": 1.8,
        "omission_errors": 1.0,
        "intrusion_errors": 0.0,
        "sequence_recall_accuracy": 0.72,
        "retry_frequency": 2.0,
        "memory_consistency_trend": 0.75,
        "naming_accuracy": 0.8,
        "response_latency": 1.4,
        "semantic_error_frequency": 0.05,
        "phonemic_error_frequency": 0.05,
        "cue_dependency_rate": 0.2,
        "no_response_frequency": 0.05,
        "typing_speaking_speed": 2.1,
        "time_per_image": 5.4,
        "nback_accuracy": 0.78,
        "false_positive_rate": 0.08,
        "missed_target_rate": 0.15,
        "sustained_attention_score": 0.81,
        "attention_drift": 0.1,
        "idle_time": 14.0,
        "fatigue_progression": -0.06,
        "path_efficiency": 0.84,
        "sequence_accuracy": 0.92,
        "switching_delay": 920.0,
        "backtracking_frequency": 0.08,
        "rule_violation_count": 2.0,
        "cursor_movement_entropy": 1.9,
        "trajectory_deviation": 0.16,
        "tremor_jitter_frequency": 0.12,
    }


def test_model_metadata_loads():
    metadata = load_model_metadata()
    assert metadata["model_version"] == "1.0.0"
    assert metadata["feature_count"] == 47
    assert metadata["feature_names"] == MODEL_FEATURE_NAMES


def test_feature_schema_loads():
    schema = load_feature_schema()
    assert schema["feature_count"] == 47
    assert schema["features"] == MODEL_FEATURE_NAMES


def test_model_loads():
    booster = get_model1_booster()
    assert booster is not None


def test_prediction_is_finite():
    prediction = predict_cognitive_performance(build_feature_vector())
    assert math.isfinite(prediction)
