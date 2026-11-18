import pytest

from app.games.memory.exceptions import IncompleteGameDataError
from app.games.memory.features import extract_features
from tests.games.memory.fixtures import (
    TARGET_IDS,
    TARGET_LABELS,
    build_full_happy_path_events,
    default_confidence,
    delayed_recall_events,
    game_completed,
    game_started,
    immediate_recall_events,
    learning_events,
    make_event,
    phase_boundary,
    recognition_events,
    reset_event_counter,
    t,
)
from app.games.memory.schemas import MemoryConfidence, MemoryEventType, MemoryPhase


# ---------------------------------------------------------------------
# Full worked example (spec section 33)
# ---------------------------------------------------------------------


def test_worked_example_immediate_recall_accuracy():
    features = extract_features(build_full_happy_path_events(), default_confidence())
    assert features.immediate_recall_accuracy == pytest.approx(9 / 12)


def test_worked_example_delayed_recall_accuracy():
    features = extract_features(build_full_happy_path_events(), default_confidence())
    assert features.delayed_recall_accuracy == pytest.approx(7 / 12)


def test_worked_example_omission_errors():
    features = extract_features(build_full_happy_path_events(), default_confidence())
    assert features.omission_errors == 5


def test_worked_example_intrusion_errors():
    features = extract_features(build_full_happy_path_events(), default_confidence())
    assert features.intrusion_errors == 1


def test_worked_example_recognition_accuracy():
    features = extract_features(build_full_happy_path_events(), default_confidence())
    assert features.recognition_accuracy == pytest.approx(1.0)


def test_worked_example_recall_decay_rate():
    features = extract_features(build_full_happy_path_events(), default_confidence())
    expected = (9 / 12 - 7 / 12) / (9 / 12)
    assert features.recall_decay_rate == pytest.approx(expected)


def test_worked_example_sequence_recall_accuracy():
    features = extract_features(build_full_happy_path_events(), default_confidence())
    assert features.sequence_recall_accuracy == pytest.approx(1.0)


def test_worked_example_hesitation_duration_no_hesitation():
    features = extract_features(build_full_happy_path_events(), default_confidence())
    assert features.hesitation_duration == pytest.approx(0.0)


def test_worked_example_retry_frequency():
    features = extract_features(build_full_happy_path_events(), default_confidence())
    assert features.retry_frequency == 0


def test_worked_example_confidence_variability():
    features = extract_features(build_full_happy_path_events(), default_confidence())
    assert features.confidence_variability == pytest.approx(1.0)


def test_worked_example_completion_time():
    features = extract_features(build_full_happy_path_events(), default_confidence())
    assert features.completion_time == pytest.approx(151.0)


def test_worked_example_memory_consistency_trend():
    features = extract_features(build_full_happy_path_events(), default_confidence())
    assert features.memory_consistency_trend == pytest.approx(7 / 9)


def test_worked_example_recall_latency():
    features = extract_features(build_full_happy_path_events(), default_confidence())
    assert features.recall_latency == pytest.approx(3.0)


# ---------------------------------------------------------------------
# Helper to build a minimal but complete event stream for edge cases
# ---------------------------------------------------------------------


def _minimal_game(
    immediate_selected: list[str],
    delayed_responses: list[str],
    recognition_results: list[tuple[str, bool, str]],
    delayed_gap: float = 1.0,
    completion_seconds: float = 60.0,
):
    reset_event_counter()
    events = [game_started(0.0)]
    events.append(phase_boundary(MemoryPhase.LEARNING, MemoryEventType.PHASE_STARTED, 1.0))
    events += learning_events(start_seconds=1.0)
    events.append(phase_boundary(MemoryPhase.LEARNING, MemoryEventType.PHASE_COMPLETED, 5.0))

    events.append(
        phase_boundary(MemoryPhase.IMMEDIATE_RECALL, MemoryEventType.PHASE_STARTED, 6.0)
    )
    events += immediate_recall_events(immediate_selected, start_seconds=7.0)
    events.append(
        phase_boundary(MemoryPhase.IMMEDIATE_RECALL, MemoryEventType.PHASE_COMPLETED, 10.0)
    )

    events.append(phase_boundary(MemoryPhase.DISTRACTOR, MemoryEventType.PHASE_STARTED, 11.0))
    events.append(phase_boundary(MemoryPhase.DISTRACTOR, MemoryEventType.PHASE_COMPLETED, 20.0))

    events.append(
        phase_boundary(MemoryPhase.DELAYED_RECALL, MemoryEventType.PHASE_STARTED, 21.0)
    )
    events += delayed_recall_events(delayed_responses, start_seconds=22.0, gap_seconds=delayed_gap)
    events.append(
        phase_boundary(MemoryPhase.DELAYED_RECALL, MemoryEventType.PHASE_COMPLETED, 30.0)
    )

    events.append(phase_boundary(MemoryPhase.RECOGNITION, MemoryEventType.PHASE_STARTED, 31.0))
    events += recognition_events(recognition_results, start_seconds=32.0)
    events.append(phase_boundary(MemoryPhase.RECOGNITION, MemoryEventType.PHASE_COMPLETED, 40.0))

    events.append(phase_boundary(MemoryPhase.CONFIDENCE, MemoryEventType.PHASE_STARTED, 41.0))
    events.append(phase_boundary(MemoryPhase.CONFIDENCE, MemoryEventType.PHASE_COMPLETED, 42.0))

    events.append(game_completed(completion_seconds))
    return events


def test_zero_immediate_recall():
    events = _minimal_game(
        immediate_selected=[],
        delayed_responses=[TARGET_LABELS[0]],
        recognition_results=[(TARGET_IDS[0], True, "YES")],
    )
    features = extract_features(events, default_confidence())
    assert features.immediate_recall_accuracy == 0.0
    assert features.recall_decay_rate == 0.0
    assert features.memory_consistency_trend == 0.0


def test_zero_delayed_recall():
    events = _minimal_game(
        immediate_selected=TARGET_IDS[:5],
        delayed_responses=[],
        recognition_results=[(TARGET_IDS[0], True, "YES")],
    )
    with pytest.raises(IncompleteGameDataError):
        extract_features(events, default_confidence())


def test_perfect_recall():
    events = _minimal_game(
        immediate_selected=TARGET_IDS,
        delayed_responses=TARGET_LABELS,
        recognition_results=[(tid, True, "YES") for tid in TARGET_IDS],
        delayed_gap=1.0,
    )
    features = extract_features(events, default_confidence())
    assert features.immediate_recall_accuracy == pytest.approx(1.0)
    assert features.delayed_recall_accuracy == pytest.approx(1.0)
    assert features.omission_errors == 0
    assert features.recall_decay_rate == pytest.approx(0.0)
    assert features.memory_consistency_trend == pytest.approx(1.0)


def test_no_recall_at_all_raises_incomplete():
    events = _minimal_game(
        immediate_selected=[],
        delayed_responses=[],
        recognition_results=[(TARGET_IDS[0], True, "YES")],
    )
    with pytest.raises(IncompleteGameDataError):
        extract_features(events, default_confidence())


def test_all_recognition_correct():
    events = _minimal_game(
        immediate_selected=TARGET_IDS[:3],
        delayed_responses=[TARGET_LABELS[0]],
        recognition_results=[(tid, True, "YES") for tid in TARGET_IDS]
        + [("d1", False, "NO")],
    )
    features = extract_features(events, default_confidence())
    assert features.recognition_accuracy == pytest.approx(1.0)


def test_all_recognition_incorrect():
    events = _minimal_game(
        immediate_selected=TARGET_IDS[:3],
        delayed_responses=[TARGET_LABELS[0]],
        recognition_results=[(tid, True, "NO") for tid in TARGET_IDS],
    )
    features = extract_features(events, default_confidence())
    assert features.recognition_accuracy == pytest.approx(0.0)


def test_duplicate_target_responses_not_double_counted():
    events = _minimal_game(
        immediate_selected=TARGET_IDS[:3],
        delayed_responses=[TARGET_LABELS[0], TARGET_LABELS[0], TARGET_LABELS[1]],
        recognition_results=[(TARGET_IDS[0], True, "YES")],
    )
    features = extract_features(events, default_confidence())
    # Only 2 distinct targets recalled (apple, chair) despite 3 responses
    assert features.delayed_recall_accuracy == pytest.approx(2 / 12)
    assert features.omission_errors == 10


def test_intrusion_responses_counted():
    events = _minimal_game(
        immediate_selected=TARGET_IDS[:3],
        delayed_responses=[TARGET_LABELS[0], "dog", "elephant"],
        recognition_results=[(TARGET_IDS[0], True, "YES")],
    )
    features = extract_features(events, default_confidence())
    assert features.intrusion_errors == 2


def test_long_hesitation():
    events = _minimal_game(
        immediate_selected=TARGET_IDS[:3],
        delayed_responses=[TARGET_LABELS[0], TARGET_LABELS[1]],
        recognition_results=[(TARGET_IDS[0], True, "YES")],
        delayed_gap=10.0,  # 10s gap, threshold is 2s -> 8s hesitation
    )
    features = extract_features(events, default_confidence())
    assert features.hesitation_duration == pytest.approx(8.0)


def test_no_hesitation_under_threshold():
    events = _minimal_game(
        immediate_selected=TARGET_IDS[:3],
        delayed_responses=[TARGET_LABELS[0], TARGET_LABELS[1]],
        recognition_results=[(TARGET_IDS[0], True, "YES")],
        delayed_gap=1.5,
    )
    features = extract_features(events, default_confidence())
    assert features.hesitation_duration == pytest.approx(0.0)


def test_one_confidence_observation_not_possible_but_two_minimum_handled():
    # MemoryConfidence always requires 3 fields; verify stdev computation
    # is stable and deterministic for a fixed set of 3 values.
    confidence = MemoryConfidence(immediate_recall=3, delayed_recall=3, recognition=3)
    events = _minimal_game(
        immediate_selected=TARGET_IDS[:3],
        delayed_responses=[TARGET_LABELS[0]],
        recognition_results=[(TARGET_IDS[0], True, "YES")],
    )
    features = extract_features(events, confidence)
    assert features.confidence_variability == pytest.approx(0.0)


def test_three_confidence_observations_variability():
    confidence = MemoryConfidence(immediate_recall=1, delayed_recall=3, recognition=5)
    events = _minimal_game(
        immediate_selected=TARGET_IDS[:3],
        delayed_responses=[TARGET_LABELS[0]],
        recognition_results=[(TARGET_IDS[0], True, "YES")],
    )
    features = extract_features(events, confidence)
    assert features.confidence_variability == pytest.approx(2.0)


def test_missing_delayed_response_raises_incomplete():
    reset_event_counter()
    events = [game_started(0.0)]
    events.append(phase_boundary(MemoryPhase.LEARNING, MemoryEventType.PHASE_STARTED, 1.0))
    events += learning_events(start_seconds=1.0)
    events.append(phase_boundary(MemoryPhase.LEARNING, MemoryEventType.PHASE_COMPLETED, 5.0))
    events.append(
        phase_boundary(MemoryPhase.DELAYED_RECALL, MemoryEventType.PHASE_STARTED, 21.0)
    )
    events.append(game_completed(30.0))
    with pytest.raises(IncompleteGameDataError):
        extract_features(events, default_confidence())


def test_incomplete_game_missing_completion_timestamp_raises():
    reset_event_counter()
    events = [game_started(0.0)]
    events += learning_events(start_seconds=1.0)
    # no game_completed event at all
    with pytest.raises(IncompleteGameDataError):
        extract_features(events, default_confidence())


def test_sequence_recall_out_of_order_penalized():
    events = _minimal_game(
        immediate_selected=TARGET_IDS[:5],
        delayed_responses=[TARGET_LABELS[2], TARGET_LABELS[0], TARGET_LABELS[1]],
        recognition_results=[(TARGET_IDS[0], True, "YES")],
    )
    features = extract_features(events, default_confidence())
    # order recalled: position 2, then 0, then 1 -> pairs (2,0) not preserved, (0,1) preserved
    assert features.sequence_recall_accuracy == pytest.approx(0.5)


def test_sequence_recall_fewer_than_two_matches_is_zero():
    events = _minimal_game(
        immediate_selected=TARGET_IDS[:3],
        delayed_responses=[TARGET_LABELS[0]],
        recognition_results=[(TARGET_IDS[0], True, "YES")],
    )
    features = extract_features(events, default_confidence())
    assert features.sequence_recall_accuracy == 0.0
