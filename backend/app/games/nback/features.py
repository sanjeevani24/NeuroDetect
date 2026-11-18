"""
N-Back feature extraction.

Implements the 12 LOCKED feature definitions from the N-Back spec (section 15).
All functions are pure: given a list of ReconstructedTrial (scored trials only,
practice and warmup already excluded by the caller) plus assessment start/end
timestamps, they return a single float/int. No I/O, no randomness.

d_prime uses statistics.NormalDist().inv_cdf, the standard-library exact
implementation of the standard normal inverse CDF (probit function) - this is
NOT an approximation, per spec section 15.9.
"""
from __future__ import annotations

import statistics
from datetime import datetime

from app.games.nback.schemas import NBackResponse, ReconstructedTrial

_normal = statistics.NormalDist(mu=0.0, sigma=1.0)


class FeatureComputationError(Exception):
    """Raised when features cannot be computed from the given trial set."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_hit(t: ReconstructedTrial) -> bool:
    return t.is_target is True and t.response == NBackResponse.MATCH


def _is_omission(t: ReconstructedTrial) -> bool:
    # target trial where participant said NO_MATCH, OR failed to respond in time
    return t.is_target is True and (
        t.response == NBackResponse.NO_MATCH or t.timed_out or t.response == NBackResponse.NONE
    )


def _is_commission(t: ReconstructedTrial) -> bool:
    return t.is_target is False and t.response == NBackResponse.MATCH


def _is_correct_rejection(t: ReconstructedTrial) -> bool:
    return t.is_target is False and t.response == NBackResponse.NO_MATCH


def _is_correct(t: ReconstructedTrial) -> bool:
    if t.response == NBackResponse.NONE or t.timed_out:
        return False
    return t.response == t.correct_answer


def _valid_latencies(trials: list[ReconstructedTrial]) -> list[float]:
    """
    Latencies (in seconds) for scored trials with an actual, in-window response.
    Excludes no-response and timed-out trials per spec section 15.5/15.6.
    """
    out = []
    for t in trials:
        if t.timed_out or t.response == NBackResponse.NONE:
            continue
        if t.response_latency_ms is None:
            continue
        out.append(t.response_latency_ms / 1000.0)
    return out


# ---------------------------------------------------------------------------
# 1. nback_accuracy
# ---------------------------------------------------------------------------

def compute_nback_accuracy(trials: list[ReconstructedTrial]) -> float:
    if not trials:
        raise FeatureComputationError("no scored trials available for accuracy")
    correct = sum(1 for t in trials if _is_correct(t))
    return correct / len(trials)


# ---------------------------------------------------------------------------
# 2. hit_rate
# ---------------------------------------------------------------------------

def compute_hit_rate(trials: list[ReconstructedTrial]) -> tuple[float, bool]:
    """Returns (hit_rate, invalid_configuration_flag)."""
    targets = [t for t in trials if t.is_target is True]
    if not targets:
        return 0.0, True
    hits = sum(1 for t in targets if _is_hit(t))
    return hits / len(targets), False


# ---------------------------------------------------------------------------
# 3. false_alarm_rate
# ---------------------------------------------------------------------------

def compute_false_alarm_rate(trials: list[ReconstructedTrial]) -> tuple[float, bool]:
    non_targets = [t for t in trials if t.is_target is False]
    if not non_targets:
        return 0.0, True
    fas = sum(1 for t in non_targets if _is_commission(t))
    return fas / len(non_targets), False


# ---------------------------------------------------------------------------
# 4. sensitivity  (simple index, NOT d-prime — spec section 15.4)
# ---------------------------------------------------------------------------

def compute_sensitivity(hit_rate: float, false_alarm_rate: float) -> float:
    """Simple sensitivity index = hit_rate - false_alarm_rate. Range -1..1."""
    return hit_rate - false_alarm_rate


# ---------------------------------------------------------------------------
# 5. response_latency
# ---------------------------------------------------------------------------

def compute_response_latency(trials: list[ReconstructedTrial]) -> float:
    latencies = _valid_latencies(trials)
    if not latencies:
        return 0.0
    return statistics.mean(latencies)


# ---------------------------------------------------------------------------
# 6. latency_variability
# ---------------------------------------------------------------------------

def compute_latency_variability(trials: list[ReconstructedTrial]) -> float:
    latencies = _valid_latencies(trials)
    if len(latencies) < 2:
        return 0.0
    return statistics.stdev(latencies)


# ---------------------------------------------------------------------------
# 7. omission_errors
# ---------------------------------------------------------------------------

def compute_omission_errors(trials: list[ReconstructedTrial]) -> int:
    return sum(1 for t in trials if _is_omission(t))


# ---------------------------------------------------------------------------
# 8. commission_errors
# ---------------------------------------------------------------------------

def compute_commission_errors(trials: list[ReconstructedTrial]) -> int:
    return sum(1 for t in trials if _is_commission(t))


# ---------------------------------------------------------------------------
# 9. d_prime  (exact signal-detection d', with finite-sample correction)
# ---------------------------------------------------------------------------

def compute_d_prime(trials: list[ReconstructedTrial]) -> float:
    """
    d_prime = z(adjusted_hit_rate) - z(adjusted_false_alarm_rate)

    Finite-sample correction (spec section 15.9) is applied unconditionally
    (not just when H/FA hit 0 or 1) so the estimator is consistent:

        adjusted_hit_rate = (H + 0.5) / (N_target + 1)
        adjusted_false_alarm_rate = (FA + 0.5) / (N_non_target + 1)

    z() is statistics.NormalDist().inv_cdf — the exact standard normal
    inverse CDF, not an approximation.
    """
    targets = [t for t in trials if t.is_target is True]
    non_targets = [t for t in trials if t.is_target is False]

    n_target = len(targets)
    n_non_target = len(non_targets)

    if n_target == 0 or n_non_target == 0:
        raise FeatureComputationError(
            "d_prime requires at least one target and one non-target trial"
        )

    hits = sum(1 for t in targets if _is_hit(t))
    false_alarms = sum(1 for t in non_targets if _is_commission(t))

    adjusted_hit_rate = (hits + 0.5) / (n_target + 1)
    adjusted_false_alarm_rate = (false_alarms + 0.5) / (n_non_target + 1)

    z_hit = _normal.inv_cdf(adjusted_hit_rate)
    z_fa = _normal.inv_cdf(adjusted_false_alarm_rate)

    d_prime = z_hit - z_fa

    if not _is_finite(d_prime):
        raise FeatureComputationError("d_prime computation produced a non-finite value")

    return d_prime


def _is_finite(x: float) -> bool:
    return x == x and x not in (float("inf"), float("-inf"))


# ---------------------------------------------------------------------------
# 10. response_consistency
# ---------------------------------------------------------------------------

def compute_response_consistency(trials: list[ReconstructedTrial]) -> float:
    """
    1 / (1 + coefficient_of_variation)
    coefficient_of_variation = stdev(latency) / mean(latency)

    If mean latency <= 0 (including "no valid latencies"), return 0
    per spec section 15.10.
    """
    latencies = _valid_latencies(trials)
    if not latencies:
        return 0.0
    mean_latency = statistics.mean(latencies)
    if mean_latency <= 0:
        return 0.0
    if len(latencies) < 2:
        # a single data point has zero variance -> perfectly consistent
        return 1.0
    stdev_latency = statistics.stdev(latencies)
    cv = stdev_latency / mean_latency
    return 1.0 / (1.0 + cv)


# ---------------------------------------------------------------------------
# 11. fatigue_trend
# ---------------------------------------------------------------------------

def compute_fatigue_trend(trials: list[ReconstructedTrial]) -> float:
    """
    Split scored trials (in trial_index order) into first/second half by
    count, compute accuracy in each half, return second - first.
    Odd counts: the middle trial goes into the first half (floor split),
    consistent and deterministic.
    """
    if len(trials) < 2:
        return 0.0
    ordered = sorted(trials, key=lambda t: t.trial_index)
    midpoint = len(ordered) // 2
    first_half = ordered[:midpoint]
    second_half = ordered[midpoint:]
    if not first_half or not second_half:
        return 0.0
    acc_first = sum(1 for t in first_half if _is_correct(t)) / len(first_half)
    acc_second = sum(1 for t in second_half if _is_correct(t)) / len(second_half)
    return acc_second - acc_first


# ---------------------------------------------------------------------------
# 12. completion_time
# ---------------------------------------------------------------------------

def compute_completion_time(started_at: datetime, completed_at: datetime) -> float:
    delta = (completed_at - started_at).total_seconds()
    if delta <= 0:
        raise FeatureComputationError("completion_time must be > 0")
    return delta


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def compute_all_features(
    scored_trials: list[ReconstructedTrial],
    assessment_started_at: datetime,
    assessment_completed_at: datetime,
) -> dict:
    """
    Computes all 12 features from scored trials (warmup + practice already
    excluded by the caller). Raises FeatureComputationError if the trial set
    is insufficient to compute a required feature.
    """
    if not scored_trials:
        raise FeatureComputationError("no scored trials provided")

    accuracy = compute_nback_accuracy(scored_trials)
    hit_rate, hit_invalid = compute_hit_rate(scored_trials)
    fa_rate, fa_invalid = compute_false_alarm_rate(scored_trials)
    sensitivity = compute_sensitivity(hit_rate, fa_rate)
    response_latency = compute_response_latency(scored_trials)
    latency_variability = compute_latency_variability(scored_trials)
    omission_errors = compute_omission_errors(scored_trials)
    commission_errors = compute_commission_errors(scored_trials)
    d_prime = compute_d_prime(scored_trials)
    response_consistency = compute_response_consistency(scored_trials)
    fatigue_trend = compute_fatigue_trend(scored_trials)
    completion_time = compute_completion_time(assessment_started_at, assessment_completed_at)

    return {
        "nback_accuracy": accuracy,
        "hit_rate": hit_rate,
        "false_alarm_rate": fa_rate,
        "sensitivity": sensitivity,
        "response_latency": response_latency,
        "latency_variability": latency_variability,
        "omission_errors": omission_errors,
        "commission_errors": commission_errors,
        "d_prime": d_prime,
        "response_consistency": response_consistency,
        "fatigue_trend": fatigue_trend,
        "completion_time": completion_time,
        "_flags": {
            "hit_rate_invalid_configuration": hit_invalid,
            "false_alarm_rate_invalid_configuration": fa_invalid,
        },
    }
