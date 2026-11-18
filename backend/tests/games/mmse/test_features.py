import pytest

from app.games.mmse.exceptions import IncompleteGameDataError
from app.games.mmse.features import (
    calculate_attention_accuracy,
    calculate_command_following_accuracy,
    calculate_completion_time,
    calculate_correction_frequency,
    calculate_delayed_recall_accuracy,
    calculate_intrusion_errors,
    calculate_language_accuracy,
    calculate_latency_variability,
    calculate_omission_errors,
    calculate_orientation_accuracy,
    calculate_performance_consistency,
    calculate_registration_accuracy,
    calculate_response_latency,
    calculate_serial7_accuracy,
    extract_features,
)
from app.games.mmse.schemas import MMSEEventType, MMSEPhase
from tests.games.mmse.fixtures import build_happy_path_events, make_event, reset_event_counter


def test_orientation_accuracy():
    features = extract_features(build_happy_path_events())
    assert features.orientation_accuracy == pytest.approx(0.8)


def test_registration_accuracy():
    features = extract_features(build_happy_path_events())
    assert features.registration_accuracy == pytest.approx(2 / 3)


def test_attention_accuracy():
    features = extract_features(build_happy_path_events())
    assert features.attention_accuracy == pytest.approx(0.8)


def test_serial7_accuracy():
    features = extract_features(build_happy_path_events())
    assert features.serial7_accuracy == pytest.approx(0.8)


def test_delayed_recall_accuracy():
    features = extract_features(build_happy_path_events())
    assert features.delayed_recall_accuracy == pytest.approx(2 / 3)


def test_language_accuracy():
    features = extract_features(build_happy_path_events())
    assert features.language_accuracy == pytest.approx(1.0)


def test_command_following_accuracy():
    features = extract_features(build_happy_path_events())
    assert features.command_following_accuracy == pytest.approx(1.0)


def test_response_latency():
    features = extract_features(build_happy_path_events())
    assert features.response_latency == pytest.approx(0.8125)


def test_latency_variability():
    features = extract_features(build_happy_path_events())
    assert features.latency_variability == pytest.approx(0.05)


def test_omission_errors():
    features = extract_features(build_happy_path_events())
    assert features.omission_errors == 0


def test_intrusion_errors():
    features = extract_features(build_happy_path_events())
    assert features.intrusion_errors == 2


def test_correction_frequency():
    features = extract_features(build_happy_path_events())
    assert features.correction_frequency == pytest.approx(1 / 20)


def test_completion_time():
    features = extract_features(build_happy_path_events())
    assert features.completion_time == pytest.approx(60.0)


def test_performance_consistency():
    features = extract_features(build_happy_path_events())
    expected = calculate_performance_consistency(0.8, 2 / 3, 0.8, 1.0, 2 / 3, 1.0)
    assert features.performance_consistency == pytest.approx(expected)


def test_perfect_performance():
    events = build_happy_path_events()
    for event in events:
        if event.event_type == MMSEEventType.RESPONSE_SUBMITTED and event.phase in {
            MMSEPhase.ORIENTATION,
            MMSEPhase.ATTENTION,
        }:
            event.value = str(event.metadata.get("expected_answer", event.value))
        if event.phase == MMSEPhase.REGISTRATION and event.event_type == MMSEEventType.RESPONSE_SUBMITTED:
            event.value = ["APPLE", "TABLE", "COIN"][int(event.metadata["response_order"]) - 1]
        if event.phase == MMSEPhase.DELAYED_RECALL and event.event_type == MMSEEventType.RESPONSE_SUBMITTED:
            event.value = ["APPLE", "TABLE", "COIN"][int(event.metadata["response_order"]) - 1]
    features = extract_features(events)
    assert features.orientation_accuracy == 1.0
    assert features.serial7_accuracy == 1.0
    assert features.delayed_recall_accuracy == 1.0


def test_zero_recall():
    events = build_happy_path_events()
    for event in events:
        if event.phase in {MMSEPhase.REGISTRATION, MMSEPhase.DELAYED_RECALL} and event.event_type == MMSEEventType.RESPONSE_SUBMITTED:
            event.value = ""
    features = extract_features(events)
    assert features.registration_accuracy == 0.0
    assert features.delayed_recall_accuracy == 0.0


def test_missing_response():
    events = build_happy_path_events()
    for event in events:
        if event.phase == MMSEPhase.ORIENTATION and event.question_id == "location" and event.event_type == MMSEEventType.RESPONSE_SUBMITTED:
            event.value = ""
    features = extract_features(events)
    assert features.omission_errors == 1


def test_intrusion_response():
    events = build_happy_path_events()
    features = extract_features(events)
    assert features.intrusion_errors == 2


def test_correction():
    events = build_happy_path_events()
    assert extract_features(events).correction_frequency > 0


def test_no_latency_raises_incomplete():
    reset_event_counter()
    events = [
        make_event(MMSEPhase.INTRO, MMSEEventType.GAME_STARTED, 0),
        make_event(MMSEPhase.ORIENTATION, MMSEEventType.QUESTION_PRESENTED, 1, question_id="year", metadata={"expected_answer": "2026"}),
    ]
    with pytest.raises(IncompleteGameDataError):
        calculate_response_latency(events)
