from __future__ import annotations

import pytest

from app.games.trail_making.exceptions import FeatureValidationError, TelemetryValidationError
from app.games.trail_making.schemas import TrailMakingCompleteRequest, TrailMakingFeatures
from app.games.trail_making.validators import validate_features, validate_telemetry
from tests.games.trail_making.fixtures import GAME_SESSION_ID, ASSESSMENT_ID, perfect_request


def test_validate_telemetry_passes():
    layout, events = perfect_request()
    request = TrailMakingCompleteRequest(
        game_session_id=GAME_SESSION_ID,
        node_layout=layout,
        events=events,
    )
    validate_telemetry(request, ASSESSMENT_ID)


def test_missing_layout_rejected():
    _, events = perfect_request()
    request = TrailMakingCompleteRequest(game_session_id=GAME_SESSION_ID, node_layout=[], events=events)
    with pytest.raises(TelemetryValidationError):
        validate_telemetry(request, ASSESSMENT_ID)


def test_invalid_feature_rejected():
    with pytest.raises(FeatureValidationError):
        validate_features(
            TrailMakingFeatures(
                path_efficiency=1.2,
                sequence_accuracy=1.0,
                switching_delay=10.0,
                backtracking_frequency=0.0,
                rule_violation_count=0,
                cursor_movement_entropy=0.0,
                trajectory_deviation=0.0,
                tremor_jitter_frequency=0.0,
                total_completion_time=100.0,
                total_error_count=0,
                correct_target_count=25,
                mean_reaction_time=10.0,
                median_reaction_time=10.0,
                reaction_time_variance=0.0,
                hesitation_duration=0.0,
                error_recovery_time=0.0,
                first_half_time=10.0,
                second_half_time=10.0,
                time_degradation_ratio=1.0,
                switch_count=24,
                correct_switch_count=24,
                incorrect_switch_count=0,
                backtracking_distance=0.0,
                trajectory_length=100.0,
                ideal_path_length=90.0,
                correction_count=0,
                idle_time=0.0,
                layout=[],
            )
        )
