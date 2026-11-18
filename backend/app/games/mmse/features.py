from __future__ import annotations

import statistics
from dataclasses import dataclass

from app.games.mmse.config import COMMAND_EXPECTED_SEQUENCE, REGISTRATION_TARGETS
from app.games.mmse.exceptions import IncompleteGameDataError
from app.games.mmse.schemas import MMSEEvent, MMSEEventType, MMSEPhase


def _normalize_text(value: str) -> str:
    import re

    text = value.strip().lower()
    text = re.sub(r"[!.,;:'\"?]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _timestamp(event: MMSEEvent) -> float:
    return event.timestamp.timestamp()


def _submitted(events: list[MMSEEvent], phase: MMSEPhase) -> list[MMSEEvent]:
    return [event for event in events if event.phase == phase and event.event_type == MMSEEventType.RESPONSE_SUBMITTED]


def _presented(events: list[MMSEEvent], phase: MMSEPhase) -> list[MMSEEvent]:
    return [event for event in events if event.phase == phase and event.event_type == MMSEEventType.QUESTION_PRESENTED]


def calculate_orientation_accuracy(events: list[MMSEEvent]) -> float:
    presented = _presented(events, MMSEPhase.ORIENTATION)
    if not presented:
        raise IncompleteGameDataError("No orientation questions recorded.")
    submitted = {event.question_id: event for event in _submitted(events, MMSEPhase.ORIENTATION)}
    correct = 0
    for question in presented:
        response = submitted.get(question.question_id)
        if response and _normalize_text(response.value or "") == _normalize_text(str(question.metadata.get("expected_answer", ""))):
            correct += 1
    return correct / len(presented)


def _memory_responses(events: list[MMSEEvent], phase: MMSEPhase) -> list[str]:
    return [_normalize_text(event.value or "") for event in _submitted(events, phase) if (event.value or "").strip()]


def calculate_registration_accuracy(events: list[MMSEEvent]) -> float:
    responses = _memory_responses(events, MMSEPhase.REGISTRATION)
    matched = {response for response in responses if response in REGISTRATION_TARGETS}
    return len(matched) / len(REGISTRATION_TARGETS)


def calculate_attention_accuracy(events: list[MMSEEvent]) -> float:
    presented = _presented(events, MMSEPhase.ATTENTION)
    if not presented:
      raise IncompleteGameDataError("No attention prompts recorded.")
    submitted = {event.question_id: event for event in _submitted(events, MMSEPhase.ATTENTION)}
    correct = 0
    for question in presented:
        response = submitted.get(question.question_id)
        if response and _normalize_text(response.value or "") == _normalize_text(str(question.metadata.get("expected_answer", ""))):
            correct += 1
    return correct / len(presented)


def calculate_serial7_accuracy(events: list[MMSEEvent]) -> float:
    serial_questions = [
        event
        for event in _presented(events, MMSEPhase.ATTENTION)
        if event.metadata.get("domain") == "serial7"
    ]
    if not serial_questions:
        raise IncompleteGameDataError("No serial7 prompts recorded.")
    submitted = {event.question_id: event for event in _submitted(events, MMSEPhase.ATTENTION)}
    correct = 0
    for question in serial_questions:
        response = submitted.get(question.question_id)
        if response and _normalize_text(response.value or "") == _normalize_text(str(question.metadata.get("expected_answer", ""))):
            correct += 1
    return correct / len(serial_questions)


def calculate_delayed_recall_accuracy(events: list[MMSEEvent]) -> float:
    responses = _memory_responses(events, MMSEPhase.DELAYED_RECALL)
    matched = {response for response in responses if response in REGISTRATION_TARGETS}
    return len(matched) / len(REGISTRATION_TARGETS)


def calculate_language_accuracy(events: list[MMSEEvent]) -> float:
    presented = _presented(events, MMSEPhase.LANGUAGE)
    if not presented:
        raise IncompleteGameDataError("No language prompts recorded.")
    submitted = {event.question_id: event for event in _submitted(events, MMSEPhase.LANGUAGE)}
    correct = 0
    for question in presented:
        response = submitted.get(question.question_id)
        if response is None:
            continue
        expected = _normalize_text(str(question.metadata.get("expected_answer", "")))
        value = _normalize_text(response.value or "")
        if question.question_id == "sentence":
            if expected and expected in value:
                correct += 1
        elif value == expected:
            correct += 1
    return correct / len(presented)


def calculate_command_following_accuracy(events: list[MMSEEvent]) -> float:
    completed = next(
        (event for event in events if event.phase == MMSEPhase.COMMAND and event.event_type == MMSEEventType.ITEM_COMPLETED),
        None,
    )
    if completed is None:
        raise IncompleteGameDataError("No command completion event recorded.")
    actual = list(completed.metadata.get("actual_sequence", []))
    correct_steps = sum(
        1 for expected, observed in zip(COMMAND_EXPECTED_SEQUENCE, actual) if expected == observed
    )
    return correct_steps / len(COMMAND_EXPECTED_SEQUENCE)


def calculate_response_latency(events: list[MMSEEvent]) -> float:
    starts: dict[tuple[str, str], float] = {}
    latencies: list[float] = []
    for event in sorted(events, key=_timestamp):
        key = (event.phase.value, event.question_id or event.item_id or "")
        if event.event_type == MMSEEventType.RESPONSE_STARTED:
            starts[key] = _timestamp(event)
        elif event.event_type == MMSEEventType.RESPONSE_SUBMITTED:
            start = starts.get(key)
            if start is not None:
                latencies.append(max(0.0, _timestamp(event) - start))
                starts.pop(key, None)
    if not latencies:
        raise IncompleteGameDataError("No valid response latencies recorded.")
    return statistics.mean(latencies)


def calculate_latency_variability(events: list[MMSEEvent]) -> float:
    starts: dict[tuple[str, str], float] = {}
    latencies: list[float] = []
    for event in sorted(events, key=_timestamp):
        key = (event.phase.value, event.question_id or event.item_id or "")
        if event.event_type == MMSEEventType.RESPONSE_STARTED:
            starts[key] = _timestamp(event)
        elif event.event_type == MMSEEventType.RESPONSE_SUBMITTED:
            start = starts.get(key)
            if start is not None:
                latencies.append(max(0.0, _timestamp(event) - start))
                starts.pop(key, None)
    if not latencies:
        raise IncompleteGameDataError("No valid response latencies recorded.")
    return 0.0 if len(latencies) == 1 else statistics.stdev(latencies)


def calculate_omission_errors(events: list[MMSEEvent]) -> int:
    orientation_omissions = sum(1 for event in _submitted(events, MMSEPhase.ORIENTATION) if not (event.value or "").strip())
    attention_omissions = sum(1 for event in _submitted(events, MMSEPhase.ATTENTION) if not (event.value or "").strip())
    language_omissions = sum(1 for event in _submitted(events, MMSEPhase.LANGUAGE) if not (event.value or "").strip())
    registration_missing = max(0, len(REGISTRATION_TARGETS) - len(_memory_responses(events, MMSEPhase.REGISTRATION)))
    delayed_missing = max(0, len(REGISTRATION_TARGETS) - len(_memory_responses(events, MMSEPhase.DELAYED_RECALL)))
    command_completed = next(
        (event for event in events if event.phase == MMSEPhase.COMMAND and event.event_type == MMSEEventType.ITEM_COMPLETED),
        None,
    )
    command_sequence = list(command_completed.metadata.get("actual_sequence", [])) if command_completed else []
    command_missing = max(0, len(COMMAND_EXPECTED_SEQUENCE) - len(command_sequence))
    return orientation_omissions + attention_omissions + language_omissions + registration_missing + delayed_missing + command_missing


def calculate_intrusion_errors(events: list[MMSEEvent]) -> int:
    registration_intrusions = sum(
        1 for response in _memory_responses(events, MMSEPhase.REGISTRATION) if response not in REGISTRATION_TARGETS
    )
    delayed_intrusions = sum(
        1 for response in _memory_responses(events, MMSEPhase.DELAYED_RECALL) if response not in REGISTRATION_TARGETS
    )
    return registration_intrusions + delayed_intrusions


def calculate_correction_frequency(events: list[MMSEEvent]) -> float:
    corrections = sum(1 for event in events if event.event_type == MMSEEventType.RESPONSE_EDITED)
    opportunities = len([event for event in events if event.event_type == MMSEEventType.RESPONSE_SUBMITTED])
    if opportunities == 0:
        raise IncompleteGameDataError("No response opportunities recorded.")
    return corrections / opportunities


def calculate_completion_time(events: list[MMSEEvent]) -> float:
    starts = [_timestamp(event) for event in events if event.event_type == MMSEEventType.GAME_STARTED]
    completions = [_timestamp(event) for event in events if event.event_type == MMSEEventType.GAME_COMPLETED]
    if not starts or not completions:
        raise IncompleteGameDataError("Missing game_started or game_completed event.")
    duration = max(completions) - min(starts)
    if duration <= 0:
        raise IncompleteGameDataError("completion_time must be greater than zero.")
    return duration


def calculate_performance_consistency(
    orientation_accuracy: float,
    registration_accuracy: float,
    attention_accuracy: float,
    language_accuracy: float,
    delayed_recall_accuracy: float,
    command_following_accuracy: float,
) -> float:
    phase_accuracies = [
        orientation_accuracy,
        registration_accuracy,
        attention_accuracy,
        language_accuracy,
        delayed_recall_accuracy,
        command_following_accuracy,
    ]
    spread = statistics.pstdev(phase_accuracies)
    return max(0.0, min(1.0, 1 - spread))


@dataclass
class ExtractedMMSEFeatures:
    orientation_accuracy: float
    registration_accuracy: float
    attention_accuracy: float
    serial7_accuracy: float
    delayed_recall_accuracy: float
    language_accuracy: float
    command_following_accuracy: float
    response_latency: float
    latency_variability: float
    omission_errors: int
    intrusion_errors: int
    correction_frequency: float
    completion_time: float
    performance_consistency: float


def extract_features(events: list[MMSEEvent]) -> ExtractedMMSEFeatures:
    orientation_accuracy = calculate_orientation_accuracy(events)
    registration_accuracy = calculate_registration_accuracy(events)
    attention_accuracy = calculate_attention_accuracy(events)
    serial7_accuracy = calculate_serial7_accuracy(events)
    delayed_recall_accuracy = calculate_delayed_recall_accuracy(events)
    language_accuracy = calculate_language_accuracy(events)
    command_following_accuracy = calculate_command_following_accuracy(events)
    response_latency = calculate_response_latency(events)
    latency_variability = calculate_latency_variability(events)
    omission_errors = calculate_omission_errors(events)
    intrusion_errors = calculate_intrusion_errors(events)
    correction_frequency = calculate_correction_frequency(events)
    completion_time = calculate_completion_time(events)
    performance_consistency = calculate_performance_consistency(
        orientation_accuracy,
        registration_accuracy,
        attention_accuracy,
        language_accuracy,
        delayed_recall_accuracy,
        command_following_accuracy,
    )

    return ExtractedMMSEFeatures(
        orientation_accuracy=orientation_accuracy,
        registration_accuracy=registration_accuracy,
        attention_accuracy=attention_accuracy,
        serial7_accuracy=serial7_accuracy,
        delayed_recall_accuracy=delayed_recall_accuracy,
        language_accuracy=language_accuracy,
        command_following_accuracy=command_following_accuracy,
        response_latency=response_latency,
        latency_variability=latency_variability,
        omission_errors=omission_errors,
        intrusion_errors=intrusion_errors,
        correction_frequency=correction_frequency,
        completion_time=completion_time,
        performance_consistency=performance_consistency,
    )
