from __future__ import annotations

from datetime import timedelta

import pytest

from app.games.boston_naming.config import DifficultyLevel
from app.games.boston_naming.features import classify_response, compute_all_features, normalize_answer
from app.games.boston_naming.schemas import CorrectnessLabel, ErrorType
from tests.games.boston_naming.fixtures import T0, make_trial


def scored_trials():
    return [
        make_trial(1, "stim_01", DifficultyLevel.EASY, correctness=CorrectnessLabel.CORRECT),
        make_trial(2, "stim_02", DifficultyLevel.EASY, correctness=CorrectnessLabel.CORRECT, cue_used=True, semantic_cue_used=True),
        make_trial(3, "stim_07", DifficultyLevel.MEDIUM, correctness=CorrectnessLabel.INCORRECT, error_type=ErrorType.SEMANTIC),
        make_trial(4, "stim_08", DifficultyLevel.MEDIUM, correctness=CorrectnessLabel.INCORRECT, error_type=ErrorType.PHONEMIC),
        make_trial(5, "stim_15", DifficultyLevel.HARD, correctness=CorrectnessLabel.AMBIGUOUS, error_type=ErrorType.NO_RESPONSE, timeout=True, response_latency_ms=None, response_duration_ms=None, hesitation_duration_ms=None),
        make_trial(6, "stim_16", DifficultyLevel.HARD, correctness=CorrectnessLabel.CORRECT, cue_used=True, phonemic_cue_used=True, self_corrected=True),
    ]


def test_normalize_answer():
    assert normalize_answer(" Apple. ") == "apple"


def test_classify_response_variants():
    correctness, error_type, normalized = classify_response("stim_01", "apple", False, "SUCCESS")
    assert correctness == CorrectnessLabel.CORRECT
    assert error_type == ErrorType.NONE
    assert normalized == "apple"

    correctness, error_type, _ = classify_response("stim_01", "fruit", False, "SUCCESS")
    assert correctness == CorrectnessLabel.INCORRECT
    assert error_type == ErrorType.SEMANTIC


def test_compute_all_features():
    start = T0
    end = T0 + timedelta(seconds=40)
    features = compute_all_features(scored_trials(), start, end)
    assert features["naming_accuracy"] == pytest.approx(3 / 6)
    assert features["semantic_errors"] == 1
    assert features["phonemic_errors"] == 1
    assert features["omission_errors"] == 1
    assert features["completion_time_ms"] == pytest.approx(40000.0)
    assert len(features["raw_trials"]) == 6


def test_fatigue_trend_deterministic():
    trials = [
        make_trial(1, "stim_01", DifficultyLevel.EASY, correctness=CorrectnessLabel.CORRECT),
        make_trial(2, "stim_02", DifficultyLevel.EASY, correctness=CorrectnessLabel.CORRECT),
        make_trial(3, "stim_07", DifficultyLevel.MEDIUM, correctness=CorrectnessLabel.CORRECT),
        make_trial(4, "stim_08", DifficultyLevel.MEDIUM, correctness=CorrectnessLabel.INCORRECT, error_type=ErrorType.UNRELATED),
    ]
    features = compute_all_features(trials, T0, T0 + timedelta(seconds=20))
    assert features["fatigue_trend"] == pytest.approx(-0.5)
