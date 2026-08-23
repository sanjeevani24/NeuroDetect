"""
Deterministic fixtures for N-Back tests.

No randomness anywhere here — every trial set is hand-constructed so test
failures point at a specific, reproducible cause.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from app.games.nback.schemas import NBackResponse, ReconstructedTrial

BASE_TIME = datetime(2026, 1, 1, 12, 0, 0)


def make_trial(
    index: int,
    is_target: bool,
    response: NBackResponse,
    latency_ms: float | None,
    timed_out: bool = False,
    is_practice: bool = False,
    is_warmup: bool = False,
) -> ReconstructedTrial:
    presented_at = BASE_TIME + timedelta(seconds=index * 3)
    response_at = None
    if response != NBackResponse.NONE and not timed_out and latency_ms is not None:
        response_at = presented_at + timedelta(milliseconds=latency_ms)

    return ReconstructedTrial(
        trial_id=f"trial-{index}",
        trial_index=index,
        stimulus="A",
        is_warmup=is_warmup,
        is_practice=is_practice,
        is_target=None if is_warmup else is_target,
        presented_at=presented_at,
        response_started_at=presented_at,
        response_at=response_at,
        response=response,
        correct_answer=None
        if is_warmup
        else (NBackResponse.MATCH if is_target else NBackResponse.NO_MATCH),
        response_latency_ms=latency_ms if (not timed_out and response != NBackResponse.NONE) else None,
        timed_out=timed_out,
    )


def perfect_trial_set(n_targets: int = 10, n_non_targets: int = 20) -> list[ReconstructedTrial]:
    """All hits, all correct rejections. Used for ceiling-value tests."""
    trials = []
    idx = 0
    for _ in range(n_targets):
        trials.append(make_trial(idx, True, NBackResponse.MATCH, latency_ms=600))
        idx += 1
    for _ in range(n_non_targets):
        trials.append(make_trial(idx, False, NBackResponse.NO_MATCH, latency_ms=550))
        idx += 1
    return trials


def zero_hit_rate_set(n_targets: int = 8, n_non_targets: int = 12) -> list[ReconstructedTrial]:
    """All targets missed (omissions); non-targets correctly rejected."""
    trials = []
    idx = 0
    for _ in range(n_targets):
        trials.append(make_trial(idx, True, NBackResponse.NO_MATCH, latency_ms=700))
        idx += 1
    for _ in range(n_non_targets):
        trials.append(make_trial(idx, False, NBackResponse.NO_MATCH, latency_ms=600))
        idx += 1
    return trials


def zero_false_alarm_set(n_targets: int = 8, n_non_targets: int = 12) -> list[ReconstructedTrial]:
    """All non-targets correctly rejected -> false_alarm_rate == 0."""
    trials = []
    idx = 0
    for _ in range(n_targets):
        trials.append(make_trial(idx, True, NBackResponse.MATCH, latency_ms=600))
        idx += 1
    for _ in range(n_non_targets):
        trials.append(make_trial(idx, False, NBackResponse.NO_MATCH, latency_ms=600))
        idx += 1
    return trials


def perfect_false_alarm_set(n_targets: int = 8, n_non_targets: int = 12) -> list[ReconstructedTrial]:
    """All non-targets incorrectly MATCHed -> false_alarm_rate == 1."""
    trials = []
    idx = 0
    for _ in range(n_targets):
        trials.append(make_trial(idx, True, NBackResponse.MATCH, latency_ms=600))
        idx += 1
    for _ in range(n_non_targets):
        trials.append(make_trial(idx, False, NBackResponse.MATCH, latency_ms=600))
        idx += 1
    return trials


def mixed_trial_set() -> list[ReconstructedTrial]:
    """
    8 target trials: 6 hits, 2 omissions.
    12 non-target trials: 9 correct rejections, 3 commissions (false alarms).
    Latencies vary so stdev/consistency are non-trivial.
    """
    trials = []
    idx = 0
    latencies = [500, 600, 700, 550, 650, 620]
    for i in range(6):  # hits
        trials.append(make_trial(idx, True, NBackResponse.MATCH, latency_ms=latencies[i]))
        idx += 1
    for _ in range(2):  # omissions (explicit NO_MATCH on a target)
        trials.append(make_trial(idx, True, NBackResponse.NO_MATCH, latency_ms=800))
        idx += 1
    for _ in range(9):  # correct rejections
        trials.append(make_trial(idx, False, NBackResponse.NO_MATCH, latency_ms=600))
        idx += 1
    for _ in range(3):  # commissions / false alarms
        trials.append(make_trial(idx, False, NBackResponse.MATCH, latency_ms=900))
        idx += 1
    return trials


def fatigue_decline_set() -> list[ReconstructedTrial]:
    """First half all correct, second half all incorrect -> negative trend."""
    trials = []
    idx = 0
    for _ in range(5):
        trials.append(make_trial(idx, True, NBackResponse.MATCH, latency_ms=600))
        idx += 1
    for _ in range(5):
        trials.append(make_trial(idx, True, NBackResponse.NO_MATCH, latency_ms=600))
        idx += 1
    return trials


def fatigue_improvement_set() -> list[ReconstructedTrial]:
    """First half all incorrect, second half all correct -> positive trend."""
    trials = []
    idx = 0
    for _ in range(5):
        trials.append(make_trial(idx, True, NBackResponse.NO_MATCH, latency_ms=600))
        idx += 1
    for _ in range(5):
        trials.append(make_trial(idx, True, NBackResponse.MATCH, latency_ms=600))
        idx += 1
    return trials


def timeout_trial() -> ReconstructedTrial:
    return make_trial(0, True, NBackResponse.NONE, latency_ms=None, timed_out=True)


def single_valid_response_set() -> list[ReconstructedTrial]:
    return [
        make_trial(0, True, NBackResponse.MATCH, latency_ms=600),
        make_trial(1, False, NBackResponse.NONE, latency_ms=None, timed_out=True),
    ]
