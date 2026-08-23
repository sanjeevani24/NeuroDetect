import math
from datetime import datetime, timedelta

import pytest

from app.games.nback import features as F
from app.games.nback.schemas import NBackResponse
from tests.games.nback.fixtures import (
    fatigue_decline_set,
    fatigue_improvement_set,
    make_trial,
    mixed_trial_set,
    perfect_false_alarm_set,
    perfect_trial_set,
    single_valid_response_set,
    zero_false_alarm_set,
    zero_hit_rate_set,
)


# ---------------------------------------------------------------------------
# 1. nback_accuracy
# ---------------------------------------------------------------------------

def test_nback_accuracy():
    trials = mixed_trial_set()  # 6 hits + 9 correct rejections = 15 correct / 20 total
    acc = F.compute_nback_accuracy(trials)
    assert acc == pytest.approx(15 / 20)


def test_nback_accuracy_no_trials_raises():
    with pytest.raises(F.FeatureComputationError):
        F.compute_nback_accuracy([])


# ---------------------------------------------------------------------------
# 2. hit_rate
# ---------------------------------------------------------------------------

def test_hit_rate():
    trials = mixed_trial_set()  # 6 hits / 8 targets
    rate, invalid = F.compute_hit_rate(trials)
    assert rate == pytest.approx(6 / 8)
    assert invalid is False


def test_zero_hit_rate():
    trials = zero_hit_rate_set()
    rate, invalid = F.compute_hit_rate(trials)
    assert rate == 0.0
    assert invalid is False


def test_perfect_hit_rate():
    trials = perfect_trial_set()
    rate, invalid = F.compute_hit_rate(trials)
    assert rate == 1.0


def test_hit_rate_no_targets_flags_invalid():
    non_target_only = [make_trial(0, False, NBackResponse.NO_MATCH, 600)]
    rate, invalid = F.compute_hit_rate(non_target_only)
    assert rate == 0.0
    assert invalid is True


# ---------------------------------------------------------------------------
# 3. false_alarm_rate
# ---------------------------------------------------------------------------

def test_false_alarm_rate():
    trials = mixed_trial_set()  # 3 false alarms / 12 non-targets
    rate, invalid = F.compute_false_alarm_rate(trials)
    assert rate == pytest.approx(3 / 12)


def test_zero_false_alarm_rate():
    trials = zero_false_alarm_set()
    rate, _ = F.compute_false_alarm_rate(trials)
    assert rate == 0.0


def test_perfect_false_alarm_rate():
    trials = perfect_false_alarm_set()
    rate, _ = F.compute_false_alarm_rate(trials)
    assert rate == 1.0


# ---------------------------------------------------------------------------
# 4. sensitivity
# ---------------------------------------------------------------------------

def test_sensitivity():
    assert F.compute_sensitivity(0.8, 0.2) == pytest.approx(0.6)
    assert F.compute_sensitivity(0.0, 1.0) == pytest.approx(-1.0)
    assert F.compute_sensitivity(1.0, 0.0) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# 5 & 6. response_latency / latency_variability
# ---------------------------------------------------------------------------

def test_response_latency():
    trials = mixed_trial_set()
    latency = F.compute_response_latency(trials)
    valid = F._valid_latencies(trials)
    assert latency == pytest.approx(sum(valid) / len(valid))


def test_latency_variability():
    trials = mixed_trial_set()
    var = F.compute_latency_variability(trials)
    assert var >= 0


def test_latency_variability_single_point_is_zero():
    trials = [make_trial(0, True, NBackResponse.MATCH, 600)]
    assert F.compute_latency_variability(trials) == 0.0


# ---------------------------------------------------------------------------
# 7 & 8. omission / commission errors
# ---------------------------------------------------------------------------

def test_omission_errors():
    trials = mixed_trial_set()
    assert F.compute_omission_errors(trials) == 2


def test_commission_errors():
    trials = mixed_trial_set()
    assert F.compute_commission_errors(trials) == 3


def test_timeout_counts_as_omission_on_target():
    trials = [make_trial(0, True, NBackResponse.NONE, None, timed_out=True)]
    assert F.compute_omission_errors(trials) == 1


# ---------------------------------------------------------------------------
# 9. d_prime
# ---------------------------------------------------------------------------

def test_d_prime_finite_and_reasonable():
    trials = mixed_trial_set()
    d = F.compute_d_prime(trials)
    assert math.isfinite(d)
    assert d > 0  # hit rate 0.75 clearly above false alarm rate 0.25


def test_dprime_correction_extreme_rates_stay_finite():
    # perfect hit rate + zero false alarm rate would be +/- infinity without
    # the finite-sample correction; with it, d_prime must stay finite.
    trials = perfect_trial_set(n_targets=10, n_non_targets=10)
    d = F.compute_d_prime(trials)
    assert math.isfinite(d)
    assert d > 0


def test_dprime_zero_hit_and_perfect_fa_stays_finite():
    trials = []
    idx = 0
    for _ in range(10):
        trials.append(make_trial(idx, True, NBackResponse.NO_MATCH, 600))
        idx += 1
    for _ in range(10):
        trials.append(make_trial(idx, False, NBackResponse.MATCH, 600))
        idx += 1
    d = F.compute_d_prime(trials)
    assert math.isfinite(d)
    assert d < 0


def test_d_prime_no_targets_raises():
    non_target_only = [make_trial(0, False, NBackResponse.NO_MATCH, 600)]
    with pytest.raises(F.FeatureComputationError):
        F.compute_d_prime(non_target_only)


# ---------------------------------------------------------------------------
# 10. response_consistency
# ---------------------------------------------------------------------------

def test_response_consistency():
    trials = mixed_trial_set()
    c = F.compute_response_consistency(trials)
    assert c > 0
    assert c <= 1.0  # 1/(1+cv) with cv >= 0 is always <= 1


def test_response_consistency_no_latencies_returns_zero():
    trials = [make_trial(0, True, NBackResponse.NONE, None, timed_out=True)]
    assert F.compute_response_consistency(trials) == 0.0


def test_response_consistency_single_valid_response():
    # single_valid_response_set has exactly one valid latency -> stdev
    # undefined -> should be treated as perfectly consistent (1.0)
    trials = single_valid_response_set()
    c = F.compute_response_consistency(trials)
    assert c == 1.0


# ---------------------------------------------------------------------------
# 11. fatigue_trend
# ---------------------------------------------------------------------------

def test_fatigue_decline():
    trials = fatigue_decline_set()
    trend = F.compute_fatigue_trend(trials)
    assert trend < 0
    assert trend == pytest.approx(-1.0)  # 1.0 first half -> 0.0 second half


def test_fatigue_improvement():
    trials = fatigue_improvement_set()
    trend = F.compute_fatigue_trend(trials)
    assert trend > 0
    assert trend == pytest.approx(1.0)


def test_fatigue_trend_insufficient_trials():
    assert F.compute_fatigue_trend([make_trial(0, True, NBackResponse.MATCH, 600)]) == 0.0


# ---------------------------------------------------------------------------
# 12. completion_time
# ---------------------------------------------------------------------------

def test_completion_time():
    start = datetime(2026, 1, 1, 12, 0, 0)
    end = start + timedelta(seconds=95)
    assert F.compute_completion_time(start, end) == pytest.approx(95.0)


def test_completion_time_non_positive_raises():
    start = datetime(2026, 1, 1, 12, 0, 0)
    with pytest.raises(F.FeatureComputationError):
        F.compute_completion_time(start, start)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def test_compute_all_features_returns_all_12_keys():
    trials = mixed_trial_set()
    start = datetime(2026, 1, 1, 12, 0, 0)
    end = start + timedelta(seconds=120)
    result = F.compute_all_features(trials, start, end)
    expected_keys = {
        "nback_accuracy",
        "hit_rate",
        "false_alarm_rate",
        "sensitivity",
        "response_latency",
        "latency_variability",
        "omission_errors",
        "commission_errors",
        "d_prime",
        "response_consistency",
        "fatigue_trend",
        "completion_time",
    }
    assert expected_keys.issubset(result.keys())
