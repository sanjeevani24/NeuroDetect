from __future__ import annotations

import pytest

from app.games.trail_making.features import compute_all_features
from tests.games.trail_making.fixtures import error_heavy_request, perfect_request


def test_perfect_request_features():
    layout, events = perfect_request()
    features = compute_all_features(events, layout)
    assert features["sequence_accuracy"] == pytest.approx(1.0)
    assert features["path_efficiency"] > 0.7
    assert features["rule_violation_count"] == 0
    assert features["incorrect_switch_count"] == 0


def test_error_heavy_request_features():
    layout, events = error_heavy_request()
    features = compute_all_features(events, layout)
    assert features["rule_violation_count"] >= 1
    assert features["total_error_count"] >= 1
    assert features["backtracking_frequency"] >= 0
