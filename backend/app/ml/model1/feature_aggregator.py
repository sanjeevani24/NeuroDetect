from __future__ import annotations

import logging
import math
from typing import Any

from app.games.nback.config import DEFAULT_CONFIG as NBACK_CONFIG
from app.ml.model1.config import (
    BOSTON_TOTAL_TRIALS,
    MMSE_ATTENTION_POINTS,
    MMSE_COMMAND_POINTS,
    MMSE_LANGUAGE_POINTS,
    MMSE_ORIENTATION_POINTS,
    MMSE_RECALL_POINTS,
    MMSE_REGISTRATION_POINTS,
    MMSE_TOTAL_POINTS,
    MMSE_TOTAL_QUESTION_COUNT,
    MMSE_TOTAL_RESPONSE_OPPORTUNITIES,
    MODEL_FEATURE_NAMES,
    FeatureMappingSpec,
)
from app.ml.model1.exceptions import Model1FeatureValidationError, Model1IncompleteAssessmentError

logger = logging.getLogger("neurodetect.model1")

FEATURE_MAPPING_SPECS: list[FeatureMappingSpec] = [
    FeatureMappingSpec("overall_mmse_score", "mmse_results", "weighted MMSE domain reconstruction to 30-point scale", "points", "0..30"),
    FeatureMappingSpec("orientation_score", "mmse_results.orientation_accuracy", "direct", "ratio", "0..1"),
    FeatureMappingSpec("attention_score", "mmse_results.attention_accuracy", "direct", "ratio", "0..1"),
    FeatureMappingSpec("recall_score", "mmse_results.delayed_recall_accuracy", "direct", "ratio", "0..1"),
    FeatureMappingSpec("language_score", "mmse_results.language_accuracy", "direct", "ratio", "0..1"),
    FeatureMappingSpec("question_accuracy", "mmse_results", "weighted score / 26 MMSE scored prompts", "ratio", "0..1"),
    FeatureMappingSpec("mean_reaction_time", "mmse_results.response_latency", "direct", "seconds", ">=0"),
    FeatureMappingSpec("reaction_time_variance", "mmse_results.latency_variability", "direct backend variability metric", "seconds", ">=0"),
    FeatureMappingSpec("hesitation_duration", "mmse_results", "response_latency * (1 - performance_consistency)", "seconds", ">=0"),
    FeatureMappingSpec("correction_frequency", "mmse_results.correction_frequency", "direct", "ratio", "0..1"),
    FeatureMappingSpec("skip_frequency", "mmse_results.omission_errors", "omission_errors / 30 response opportunities", "ratio", "0..1"),
    FeatureMappingSpec("confidence_variability", "mmse_results.performance_consistency", "1 - performance_consistency proxy", "ratio", "0..1"),
    FeatureMappingSpec("completion_time", "mmse_results.completion_time", "direct", "seconds", ">0"),
    FeatureMappingSpec("error_recovery_time", "mmse_results", "response_latency * correction_frequency", "seconds", ">=0"),
    FeatureMappingSpec("immediate_recall_accuracy", "memory_results.immediate_recall_accuracy", "direct", "ratio", "0..1"),
    FeatureMappingSpec("delayed_recall_accuracy", "memory_results.delayed_recall_accuracy", "direct", "ratio", "0..1"),
    FeatureMappingSpec("recognition_accuracy", "memory_results.recognition_accuracy", "direct", "ratio", "0..1"),
    FeatureMappingSpec("recall_decay_rate", "memory_results.recall_decay_rate", "direct", "ratio", "0..1"),
    FeatureMappingSpec("recall_latency", "memory_results.recall_latency", "direct", "seconds", ">=0"),
    FeatureMappingSpec("omission_errors", "memory_results.omission_errors", "direct", "count", ">=0"),
    FeatureMappingSpec("intrusion_errors", "memory_results.intrusion_errors", "direct", "count", ">=0"),
    FeatureMappingSpec("sequence_recall_accuracy", "memory_results.sequence_recall_accuracy", "direct", "ratio", "0..1"),
    FeatureMappingSpec("retry_frequency", "memory_results.retry_frequency", "direct", "count", ">=0"),
    FeatureMappingSpec("memory_consistency_trend", "memory_results.memory_consistency_trend", "direct", "ratio", "0..1"),
    FeatureMappingSpec("naming_accuracy", "boston_naming_results.naming_accuracy", "direct", "ratio", "0..1"),
    FeatureMappingSpec("response_latency", "boston_naming_results.mean_response_latency_ms", "milliseconds to seconds", "seconds", ">=0"),
    FeatureMappingSpec("semantic_error_frequency", "boston_naming_results.semantic_errors", "semantic_errors / 20 scored trials", "ratio", "0..1"),
    FeatureMappingSpec("phonemic_error_frequency", "boston_naming_results.phonemic_errors", "phonemic_errors / 20 scored trials", "ratio", "0..1"),
    FeatureMappingSpec("cue_dependency_rate", "boston_naming_results.total_cue_rate", "direct", "ratio", "0..1"),
    FeatureMappingSpec("no_response_frequency", "boston_naming_results.omission_errors", "omission_errors / 20 scored trials", "ratio", "0..1"),
    FeatureMappingSpec("typing_speaking_speed", "boston_naming_results.raw_trials", "mean words per second from final transcript and response duration", "words/sec", ">=0"),
    FeatureMappingSpec("time_per_image", "boston_naming_results.completion_time_ms", "completion_time_ms / 20 then milliseconds to seconds", "seconds", ">0"),
    FeatureMappingSpec("nback_accuracy", "nback_results.nback_accuracy", "direct", "ratio", "0..1"),
    FeatureMappingSpec("false_positive_rate", "nback_results.false_alarm_rate", "direct semantic alias", "ratio", "0..1"),
    FeatureMappingSpec("missed_target_rate", "nback_results", "omission_errors / estimated target trials from false-alarm design prior", "ratio", "0..1"),
    FeatureMappingSpec("sustained_attention_score", "nback_results.response_consistency", "direct proxy from backend response consistency", "ratio", "0..1"),
    FeatureMappingSpec("attention_drift", "nback_results.fatigue_trend", "absolute fatigue_trend magnitude", "ratio", ">=0"),
    FeatureMappingSpec("idle_time", "nback_results", "completion_time - estimated active response time", "seconds", ">=0"),
    FeatureMappingSpec("fatigue_progression", "nback_results.fatigue_trend", "direct semantic alias", "delta accuracy", "-1..1"),
    FeatureMappingSpec("path_efficiency", "trail_making_results.path_efficiency", "direct", "ratio", "0..1"),
    FeatureMappingSpec("sequence_accuracy", "trail_making_results.sequence_accuracy", "direct", "ratio", "0..1"),
    FeatureMappingSpec("switching_delay", "trail_making_results.switching_delay", "direct", "milliseconds", ">=0"),
    FeatureMappingSpec("backtracking_frequency", "trail_making_results.backtracking_frequency", "direct", "ratio", ">=0"),
    FeatureMappingSpec("rule_violation_count", "trail_making_results.rule_violation_count", "direct", "count", ">=0"),
    FeatureMappingSpec("cursor_movement_entropy", "trail_making_results.cursor_movement_entropy", "direct", "entropy", ">=0"),
    FeatureMappingSpec("trajectory_deviation", "trail_making_results.trajectory_deviation", "direct", "ratio", ">=0"),
    FeatureMappingSpec("tremor_jitter_frequency", "trail_making_results.tremor_jitter_frequency", "direct", "events/sec", ">=0"),
]


def validate_model1_features(feature_vector: dict[str, float]) -> None:
    names = list(feature_vector.keys())
    if names != MODEL_FEATURE_NAMES:
        raise Model1FeatureValidationError("Model 1 feature order does not match the required 47-feature schema.")
    if len(feature_vector) != len(MODEL_FEATURE_NAMES):
        raise Model1FeatureValidationError("Model 1 feature count must be exactly 47.")
    for name, value in feature_vector.items():
        if value is None:
            raise Model1FeatureValidationError(f"Feature '{name}' is missing.", feature_name=name)
        if not isinstance(value, (int, float)):
            raise Model1FeatureValidationError(f"Feature '{name}' must be numeric.", feature_name=name)
        if not math.isfinite(float(value)):
            raise Model1FeatureValidationError(f"Feature '{name}' must be finite.", feature_name=name)


def _safe_divide(numerator: float, denominator: float, *, feature_name: str) -> float:
    if denominator <= 0:
        raise Model1FeatureValidationError(
            f"Cannot derive feature '{feature_name}' because the denominator is zero.",
            feature_name=feature_name,
        )
    return numerator / denominator


def _mean_words_per_second(raw_trials: list[dict[str, Any]]) -> float:
    valid_speeds: list[float] = []
    for trial in raw_trials:
        response = str(trial.get("final_response") or trial.get("transcript") or "").strip()
        duration_ms = trial.get("response_duration_ms")
        if not response or duration_ms in (None, 0):
            continue
        words = [token for token in response.split() if token]
        seconds = float(duration_ms) / 1000.0
        if seconds <= 0:
            continue
        valid_speeds.append(len(words) / seconds)
    if not valid_speeds:
        raise Model1FeatureValidationError(
            "Cannot derive feature 'typing_speaking_speed' because Boston Naming response durations are unavailable.",
            feature_name="typing_speaking_speed",
        )
    return sum(valid_speeds) / len(valid_speeds)


def _mean_boston_latency_seconds(raw_trials: list[dict[str, Any]], summary_ms: Any) -> float:
    if summary_ms is not None:
        return float(summary_ms) / 1000.0
    latencies = [
        float(trial["response_latency_ms"]) / 1000.0
        for trial in raw_trials
        if trial.get("response_latency_ms") is not None
    ]
    if not latencies:
        raise Model1FeatureValidationError(
            "Cannot derive feature 'response_latency' because Boston Naming latencies are unavailable.",
            feature_name="response_latency",
        )
    return sum(latencies) / len(latencies)


class Model1FeatureAggregator:
    def __init__(self, *, mmse_repository, memory_repository, nback_repository, boston_repository, trail_repository):
        self._mmse_repository = mmse_repository
        self._memory_repository = memory_repository
        self._nback_repository = nback_repository
        self._boston_repository = boston_repository
        self._trail_repository = trail_repository

    def fetch_required_results(self, assessment_id: str) -> dict[str, dict[str, Any]]:
        mmse = self._mmse_repository.get_by_assessment(assessment_id)
        memory = self._memory_repository.get_by_assessment(assessment_id)
        nback = self._nback_repository.get_by_assessment(assessment_id)
        boston = self._boston_repository.get_by_assessment(assessment_id)
        trail = self._trail_repository.get_by_assessment(assessment_id)

        missing_games: list[str] = []
        if mmse is None:
            missing_games.append("MMSE")
        if memory is None:
            missing_games.append("Memory Recall")
        if nback is None:
            missing_games.append("N-Back")
        if boston is None:
            missing_games.append("Boston Naming")
        if trail is None:
            missing_games.append("Trail Making")
        if missing_games:
            raise Model1IncompleteAssessmentError(missing_games)

        return {
            "mmse": mmse,
            "memory": memory,
            "nback": nback,
            "boston": boston,
            "trail": trail,
        }

    def build_feature_vector(self, assessment_id: str) -> dict[str, float]:
        results = self.fetch_required_results(assessment_id)
        mmse = results["mmse"]
        memory = results["memory"]
        nback = results["nback"]
        boston = results["boston"]
        trail = results["trail"]

        orientation_points = float(mmse["orientation_accuracy"]) * MMSE_ORIENTATION_POINTS
        registration_points = float(mmse["registration_accuracy"]) * MMSE_REGISTRATION_POINTS
        attention_points = float(mmse["attention_accuracy"]) * MMSE_ATTENTION_POINTS
        recall_points = float(mmse["delayed_recall_accuracy"]) * MMSE_RECALL_POINTS
        language_points = float(mmse["language_accuracy"]) * MMSE_LANGUAGE_POINTS
        command_points = float(mmse["command_following_accuracy"]) * MMSE_COMMAND_POINTS
        overall_mmse_score = (
            orientation_points
            + registration_points
            + attention_points
            + recall_points
            + language_points
            + command_points
        )
        mmse_question_accuracy = _safe_divide(overall_mmse_score, MMSE_TOTAL_QUESTION_COUNT, feature_name="question_accuracy")
        mmse_hesitation_duration = float(mmse["response_latency"]) * max(
            0.0, 1.0 - float(mmse["performance_consistency"])
        )
        mmse_skip_frequency = _safe_divide(
            float(mmse["omission_errors"]),
            MMSE_TOTAL_RESPONSE_OPPORTUNITIES,
            feature_name="skip_frequency",
        )
        mmse_confidence_variability = max(0.0, 1.0 - float(mmse["performance_consistency"]))
        mmse_error_recovery_time = float(mmse["response_latency"]) * float(mmse["correction_frequency"])

        boston_raw_trials = list(boston.get("raw_trials") or [])
        total_boston_trials = float(len(boston_raw_trials) or BOSTON_TOTAL_TRIALS)

        estimated_target_trials = max(
            1.0,
            round(NBACK_CONFIG.TOTAL_SCORED_TRIALS * ((NBACK_CONFIG.TARGET_RATIO_MIN + NBACK_CONFIG.TARGET_RATIO_MAX) / 2.0)),
        )
        estimated_non_target_trials = max(1.0, NBACK_CONFIG.TOTAL_SCORED_TRIALS - estimated_target_trials)
        estimated_active_response_time = float(nback["response_latency"]) * (
            float(nback["hit_rate"]) * estimated_target_trials
            + float(nback["false_alarm_rate"]) * estimated_non_target_trials
        )
        nback_idle_time = max(0.0, float(nback["completion_time"]) - estimated_active_response_time)

        feature_vector: dict[str, float] = {
            "overall_mmse_score": overall_mmse_score,
            "orientation_score": float(mmse["orientation_accuracy"]),
            "attention_score": float(mmse["attention_accuracy"]),
            "recall_score": float(mmse["delayed_recall_accuracy"]),
            "language_score": float(mmse["language_accuracy"]),
            "question_accuracy": mmse_question_accuracy,
            "mean_reaction_time": float(mmse["response_latency"]),
            "reaction_time_variance": float(mmse["latency_variability"]),
            "hesitation_duration": mmse_hesitation_duration,
            "correction_frequency": float(mmse["correction_frequency"]),
            "skip_frequency": mmse_skip_frequency,
            "confidence_variability": mmse_confidence_variability,
            "completion_time": float(mmse["completion_time"]),
            "error_recovery_time": mmse_error_recovery_time,
            "immediate_recall_accuracy": float(memory["immediate_recall_accuracy"]),
            "delayed_recall_accuracy": float(memory["delayed_recall_accuracy"]),
            "recognition_accuracy": float(memory["recognition_accuracy"]),
            "recall_decay_rate": float(memory["recall_decay_rate"]),
            "recall_latency": float(memory["recall_latency"]),
            "omission_errors": float(memory["omission_errors"]),
            "intrusion_errors": float(memory["intrusion_errors"]),
            "sequence_recall_accuracy": float(memory["sequence_recall_accuracy"]),
            "retry_frequency": float(memory["retry_frequency"]),
            "memory_consistency_trend": float(memory["memory_consistency_trend"]),
            "naming_accuracy": float(boston["naming_accuracy"]),
            "response_latency": _mean_boston_latency_seconds(boston_raw_trials, boston.get("mean_response_latency_ms")),
            "semantic_error_frequency": _safe_divide(
                float(boston["semantic_errors"]), total_boston_trials, feature_name="semantic_error_frequency"
            ),
            "phonemic_error_frequency": _safe_divide(
                float(boston["phonemic_errors"]), total_boston_trials, feature_name="phonemic_error_frequency"
            ),
            "cue_dependency_rate": float(boston["total_cue_rate"]),
            "no_response_frequency": _safe_divide(
                float(boston["omission_errors"]), total_boston_trials, feature_name="no_response_frequency"
            ),
            "typing_speaking_speed": _mean_words_per_second(boston_raw_trials),
            "time_per_image": (float(boston["completion_time_ms"]) / total_boston_trials) / 1000.0,
            "nback_accuracy": float(nback["nback_accuracy"]),
            "false_positive_rate": float(nback["false_alarm_rate"]),
            "missed_target_rate": min(
                1.0,
                _safe_divide(float(nback["omission_errors"]), estimated_target_trials, feature_name="missed_target_rate"),
            ),
            "sustained_attention_score": float(nback["response_consistency"]),
            "attention_drift": abs(float(nback["fatigue_trend"])),
            "idle_time": nback_idle_time,
            "fatigue_progression": float(nback["fatigue_trend"]),
            "path_efficiency": float(trail["path_efficiency"]),
            "sequence_accuracy": float(trail["sequence_accuracy"]),
            "switching_delay": float(trail["switching_delay"]),
            "backtracking_frequency": float(trail["backtracking_frequency"]),
            "rule_violation_count": float(trail["rule_violation_count"]),
            "cursor_movement_entropy": float(trail["cursor_movement_entropy"]),
            "trajectory_deviation": float(trail["trajectory_deviation"]),
            "tremor_jitter_frequency": float(trail["tremor_jitter_frequency"]),
        }

        validate_model1_features(feature_vector)

        logger.info("MODEL 1 FEATURE VECTOR")
        for index, name in enumerate(MODEL_FEATURE_NAMES, start=1):
            logger.info("%s. %s = %s", index, name, feature_vector[name])
        logger.info("feature count = %s", len(feature_vector))
        return feature_vector
