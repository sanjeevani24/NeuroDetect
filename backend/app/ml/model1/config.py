from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


MODEL_NAME = "NeuroDetect Model 1 - Cognitive Performance Regressor"
MODEL_VERSION = "1.0.0"
MODEL_ROOT = Path(__file__).resolve().parents[3] / "models" / "model1" / "model1_cognitive_package"
MODEL_PATH = MODEL_ROOT / "model1_cognitive_xgboost.json"
MODEL_METADATA_PATH = MODEL_ROOT / "model_metadata.json"
FEATURE_SCHEMA_PATH = MODEL_ROOT / "feature_schema.json"
TRAINING_SUMMARY_PATH = MODEL_ROOT / "training_summary.json"

MODEL_FEATURE_NAMES = [
    "overall_mmse_score",
    "orientation_score",
    "attention_score",
    "recall_score",
    "language_score",
    "question_accuracy",
    "mean_reaction_time",
    "reaction_time_variance",
    "hesitation_duration",
    "correction_frequency",
    "skip_frequency",
    "confidence_variability",
    "completion_time",
    "error_recovery_time",
    "immediate_recall_accuracy",
    "delayed_recall_accuracy",
    "recognition_accuracy",
    "recall_decay_rate",
    "recall_latency",
    "omission_errors",
    "intrusion_errors",
    "sequence_recall_accuracy",
    "retry_frequency",
    "memory_consistency_trend",
    "naming_accuracy",
    "response_latency",
    "semantic_error_frequency",
    "phonemic_error_frequency",
    "cue_dependency_rate",
    "no_response_frequency",
    "typing_speaking_speed",
    "time_per_image",
    "nback_accuracy",
    "false_positive_rate",
    "missed_target_rate",
    "sustained_attention_score",
    "attention_drift",
    "idle_time",
    "fatigue_progression",
    "path_efficiency",
    "sequence_accuracy",
    "switching_delay",
    "backtracking_frequency",
    "rule_violation_count",
    "cursor_movement_entropy",
    "trajectory_deviation",
    "tremor_jitter_frequency",
]

MMSE_TOTAL_POINTS = 30.0
MMSE_ORIENTATION_POINTS = 10.0
MMSE_REGISTRATION_POINTS = 3.0
MMSE_ATTENTION_POINTS = 5.0
MMSE_RECALL_POINTS = 3.0
MMSE_LANGUAGE_POINTS = 6.0
MMSE_COMMAND_POINTS = 3.0
MMSE_TOTAL_QUESTION_COUNT = 26.0
MMSE_TOTAL_RESPONSE_OPPORTUNITIES = 30.0

BOSTON_TOTAL_TRIALS = 20.0


@dataclass(frozen=True)
class FeatureMappingSpec:
    feature_name: str
    source: str
    transformation: str
    unit: str
    valid_range: str
