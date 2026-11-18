from __future__ import annotations

import re
import statistics
from collections import Counter
from datetime import datetime

from app.games.boston_naming.config import DifficultyLevel, STIMULUS_LOOKUP
from app.games.boston_naming.exceptions import FeatureComputationError
from app.games.boston_naming.schemas import CorrectnessLabel, ErrorType, ReconstructedNamingTrial

_PUNCTUATION = re.compile(r"[^\w\s]")
_WHITESPACE = re.compile(r"\s+")
_HESITATION_PATTERN = re.compile(r"\b(uh|um|er|ah)\b", re.IGNORECASE)


def normalize_answer(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = _PUNCTUATION.sub(" ", value.lower().strip())
    normalized = _WHITESPACE.sub(" ", normalized).strip()
    return normalized or None


def classify_response(
    stimulus_id: str,
    transcript: str | None,
    timeout: bool,
    recording_status: str,
) -> tuple[CorrectnessLabel, ErrorType, str | None]:
    normalized = normalize_answer(transcript)
    stimulus = STIMULUS_LOOKUP[stimulus_id]
    accepted = {normalize_answer(answer) for answer in stimulus.accepted_answers}

    if timeout or recording_status == "FAILED":
        return CorrectnessLabel.AMBIGUOUS, ErrorType.NO_RESPONSE, normalized
    if not normalized:
        return CorrectnessLabel.AMBIGUOUS, ErrorType.UNKNOWN, None
    if normalized in accepted:
        return CorrectnessLabel.CORRECT, ErrorType.NONE, normalized
    if any(token in normalized for token in ("looks like", "red", "round", "big", "small")):
        return CorrectnessLabel.INCORRECT, ErrorType.VISUAL, normalized
    if stimulus.category in normalized or normalized in {
        "animal",
        "food",
        "tool",
        "instrument",
        "plant",
        "fruit",
        "object",
        "thing",
    }:
        return CorrectnessLabel.INCORRECT, ErrorType.SEMANTIC, normalized
    if normalized[0] == stimulus.canonical_name[0]:
        return CorrectnessLabel.INCORRECT, ErrorType.PHONEMIC, normalized
    if normalized in {"noise", "unclear", "inaudible"}:
        return CorrectnessLabel.AMBIGUOUS, ErrorType.UNINTELLIGIBLE, normalized
    return CorrectnessLabel.INCORRECT, ErrorType.UNRELATED, normalized


def detect_hesitation_markers(transcript: str | None) -> int:
    if not transcript:
        return 0
    return len(_HESITATION_PATTERN.findall(transcript))


def _mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _std(values: list[float]) -> float:
    return statistics.stdev(values) if len(values) >= 2 else 0.0


def _accuracy(trials: list[ReconstructedNamingTrial]) -> float | None:
    if not trials:
        return None
    return sum(1 for trial in trials if trial.correctness == CorrectnessLabel.CORRECT) / len(trials)


def _response_trials(trials: list[ReconstructedNamingTrial]) -> list[ReconstructedNamingTrial]:
    return [trial for trial in trials if not trial.timeout and trial.normalized_response]


def serialize_trial(trial: ReconstructedNamingTrial) -> dict[str, object]:
    return {
        "trial_id": trial.trial_id,
        "trial_index": trial.trial_index,
        "stimulus_id": trial.stimulus_id,
        "difficulty": trial.difficulty.value,
        "transcript": trial.transcript,
        "normalized_response": trial.normalized_response,
        "correctness": trial.correctness.value,
        "error_type": trial.error_type.value,
        "cue_used": trial.cue_used,
        "semantic_cue_used": trial.semantic_cue_used,
        "phonemic_cue_used": trial.phonemic_cue_used,
        "self_corrected": trial.self_corrected,
        "response_latency_ms": trial.response_latency_ms,
        "response_duration_ms": trial.response_duration_ms,
        "hesitation_duration_ms": trial.hesitation_duration_ms,
        "timeout": trial.timeout,
        "recording_status": trial.recording_status.value,
        "transcription_status": trial.transcription_status.value,
        "transcript_confidence": trial.transcript_confidence,
        "correct_after_cue": trial.correct_after_cue,
        "response_after_cue_ms": trial.response_after_cue_ms,
        "time_to_cue_ms": trial.time_to_cue_ms,
    }


def compute_all_features(
    scored_trials: list[ReconstructedNamingTrial],
    assessment_started_at: datetime,
    assessment_completed_at: datetime,
) -> dict[str, object]:
    if len(scored_trials) == 0:
        raise FeatureComputationError("no scored trials provided")

    latencies = [trial.response_latency_ms for trial in scored_trials if trial.response_latency_ms is not None]
    durations = [trial.response_duration_ms for trial in scored_trials if trial.response_duration_ms is not None]
    hesitations = [trial.hesitation_duration_ms for trial in scored_trials if trial.hesitation_duration_ms is not None]
    uncued_trials = [trial for trial in scored_trials if not trial.cue_used]
    cued_trials = [trial for trial in scored_trials if trial.cue_used]
    response_trials = _response_trials(scored_trials)
    correct_uncued = [trial for trial in uncued_trials if trial.correctness == CorrectnessLabel.CORRECT]
    incorrect_trials = [trial for trial in scored_trials if trial.correctness == CorrectnessLabel.INCORRECT]
    correct_after_cue = [trial for trial in cued_trials if trial.correct_after_cue]
    self_corrected = [trial for trial in response_trials if trial.self_corrected is True]
    successful_self_corrections = [trial for trial in self_corrected if trial.correctness == CorrectnessLabel.CORRECT]

    difficulties: dict[DifficultyLevel, list[ReconstructedNamingTrial]] = {
        DifficultyLevel.EASY: [trial for trial in scored_trials if trial.difficulty == DifficultyLevel.EASY],
        DifficultyLevel.MEDIUM: [trial for trial in scored_trials if trial.difficulty == DifficultyLevel.MEDIUM],
        DifficultyLevel.HARD: [trial for trial in scored_trials if trial.difficulty == DifficultyLevel.HARD],
    }
    difficulty_scores = {
        level: _accuracy(items)
        for level, items in difficulties.items()
    }

    error_counts = Counter(trial.error_type for trial in scored_trials)
    completion_time_ms = (assessment_completed_at - assessment_started_at).total_seconds() * 1000.0
    if completion_time_ms <= 0:
        raise FeatureComputationError("completion_time_ms must be > 0")

    ordered = sorted(scored_trials, key=lambda trial: trial.trial_index)
    midpoint = len(ordered) // 2
    first_half = ordered[:midpoint]
    second_half = ordered[midpoint:]
    fatigue_trend = ((_accuracy(second_half) or 0.0) - (_accuracy(first_half) or 0.0)) if first_half and second_half else 0.0

    consistency_components: list[float] = []
    if latencies:
        mean_latency = statistics.mean(latencies)
        consistency_components.append(1.0 / (1.0 + (_std(latencies) / mean_latency if mean_latency > 0 else 0.0)))
    else:
        consistency_components.append(0.0)
    response_signature = [f"{trial.stimulus_id}:{trial.correctness.value}" for trial in ordered]
    consistency_components.append(len(set(response_signature)) / len(response_signature))
    naming_consistency = min(1.0, max(0.0, statistics.mean(consistency_components)))

    weighted_scores = []
    difficulty_weights = {DifficultyLevel.EASY: 1.0, DifficultyLevel.MEDIUM: 1.25, DifficultyLevel.HARD: 1.5}
    for level, accuracy in difficulty_scores.items():
        if accuracy is None:
            continue
        weighted_scores.append(accuracy * difficulty_weights[level])
    difficulty_adjusted_accuracy = (sum(weighted_scores) / sum(difficulty_weights[level] for level, accuracy in difficulty_scores.items() if accuracy is not None)) if weighted_scores else 0.0
    difficulty_adjusted_accuracy = min(1.0, max(0.0, difficulty_adjusted_accuracy))

    return {
        "naming_accuracy": _accuracy(scored_trials) or 0.0,
        "uncued_accuracy": _accuracy(uncued_trials) or 0.0,
        "cued_accuracy": _accuracy(cued_trials),
        "semantic_cue_rate": sum(1 for trial in scored_trials if trial.semantic_cue_used) / len(scored_trials),
        "phonemic_cue_rate": sum(1 for trial in scored_trials if trial.phonemic_cue_used) / len(scored_trials),
        "total_cue_rate": sum(1 for trial in scored_trials if trial.cue_used) / len(scored_trials),
        "mean_response_latency_ms": _mean(latencies),
        "median_response_latency_ms": _median(latencies),
        "response_latency_std_ms": _std(latencies),
        "hesitation_duration_ms": _mean(hesitations) or 0.0,
        "hesitation_variability_ms": _std(hesitations),
        "omission_errors": error_counts[ErrorType.NO_RESPONSE],
        "semantic_errors": error_counts[ErrorType.SEMANTIC],
        "phonemic_errors": error_counts[ErrorType.PHONEMIC],
        "visual_errors": error_counts[ErrorType.VISUAL],
        "unrelated_errors": error_counts[ErrorType.UNRELATED],
        "ambiguous_errors": sum(
            error_counts[item]
            for item in (ErrorType.UNKNOWN, ErrorType.UNINTELLIGIBLE)
        ),
        "self_correction_rate": len(self_corrected) / len(response_trials) if response_trials else 0.0,
        "successful_self_correction_rate": len(successful_self_corrections) / len(self_corrected) if self_corrected else None,
        "mean_response_duration_ms": _mean(durations),
        "response_duration_std_ms": _std(durations),
        "correct_response_latency_ms": _mean([trial.response_latency_ms for trial in correct_uncued if trial.response_latency_ms is not None]),
        "incorrect_response_latency_ms": _mean([trial.response_latency_ms for trial in incorrect_trials if trial.response_latency_ms is not None]),
        "difficulty_adjusted_accuracy": difficulty_adjusted_accuracy,
        "easy_accuracy": difficulty_scores[DifficultyLevel.EASY],
        "medium_accuracy": difficulty_scores[DifficultyLevel.MEDIUM],
        "hard_accuracy": difficulty_scores[DifficultyLevel.HARD],
        "naming_consistency": naming_consistency,
        "fatigue_trend": fatigue_trend,
        "completion_time_ms": completion_time_ms,
        "raw_trials": [serialize_trial(trial) for trial in ordered],
    }
