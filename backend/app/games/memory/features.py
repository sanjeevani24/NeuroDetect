"""
Feature extraction for the Memory Recall game.

This module is PURE business logic: given a validated list of telemetry
events plus the confidence ratings, it derives exactly the 13 locked
features. It performs no I/O, no database access, and no HTTP concerns.
That separation is deliberate — it is what makes this module trivially
unit-testable and what the other four cognitive games should replicate.

------------------------------------------------------------------------
EVENT CONVENTIONS THIS MODULE RELIES ON
------------------------------------------------------------------------
LEARNING phase:
    item_presented  -> item_id set, metadata={"label": str, "position": int}
    item_hidden      -> item_id set

IMMEDIATE_RECALL phase:
    item_selected / item_deselected
        -> item_id set, metadata={"is_target": bool}
        -> final state per item is whichever of these events for that
           item_id has the LATEST timestamp (select/deselect/select is
           fully preserved in the raw event log; only the final state
           feeds accuracy).

DELAYED_RECALL phase:
    response_submitted
        -> value = raw free-text response (one item per event),
           metadata={"response_order": int} optional
    response_edited / retry (any phase)
        -> counted toward retry_frequency, not toward recall accuracy

RECOGNITION phase:
    recognition_response
        -> item_id, trial_id set, value="YES"|"NO",
           metadata={"is_target": bool, "correct": bool (optional,
           recomputed if absent), "response_time_ms": float (optional)}

Phase boundaries / whole-game timing:
    phase_started / phase_completed -> phase set, timestamp marks boundary
    game_started / game_completed   -> timestamp marks whole-game boundary

Confidence ratings arrive out-of-band via MemoryConfidence (not events),
per the API contract, and always contain exactly 3 observations
(immediate_recall, delayed_recall, recognition).
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from app.games.memory.config import HESITATION_THRESHOLD_SECONDS, TARGET_ITEM_COUNT
from app.games.memory.exceptions import IncompleteGameDataError
from app.games.memory.schemas import MemoryConfidence, MemoryEvent, MemoryEventType, MemoryPhase


@dataclass
class TargetItem:
    item_id: str
    label: str
    position: int


@dataclass
class DelayedResponse:
    raw_text: str
    normalized: str
    timestamp: float  # epoch seconds
    order: int


def _normalize_text(raw: str) -> str:
    """
    Deterministic text normalization — no LLM, no fuzzy matching.
    lowercase -> trim -> collapse internal whitespace -> strip harmless
    punctuation.
    """
    import re

    text = raw.strip().lower()
    text = re.sub(r"[!.,;:'\"?]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _ts(event: MemoryEvent) -> float:
    return event.timestamp.timestamp()


def _extract_targets(events: list[MemoryEvent]) -> list[TargetItem]:
    targets: dict[str, TargetItem] = {}
    for e in events:
        if e.phase == MemoryPhase.LEARNING and e.event_type == MemoryEventType.ITEM_PRESENTED:
            if e.item_id is None:
                continue
            label = str(e.metadata.get("label", e.item_id))
            position = int(e.metadata.get("position", len(targets)))
            targets[e.item_id] = TargetItem(item_id=e.item_id, label=label, position=position)
    ordered = sorted(targets.values(), key=lambda t: t.position)
    return ordered


def _final_immediate_selection(events: list[MemoryEvent]) -> dict[str, bool]:
    """Reconstruct final selected/deselected state per item from the raw log."""
    latest: dict[str, tuple[float, bool]] = {}
    for e in events:
        if e.phase != MemoryPhase.IMMEDIATE_RECALL:
            continue
        if e.event_type not in (MemoryEventType.ITEM_SELECTED, MemoryEventType.ITEM_DESELECTED):
            continue
        if e.item_id is None:
            continue
        is_selected = e.event_type == MemoryEventType.ITEM_SELECTED
        ts = _ts(e)
        prev = latest.get(e.item_id)
        if prev is None or ts >= prev[0]:
            latest[e.item_id] = (ts, is_selected)
    return {item_id: selected for item_id, (ts, selected) in latest.items()}


def _immediate_recall_target_ids_selected(events: list[MemoryEvent], target_ids: set[str]) -> set[str]:
    final_state = _final_immediate_selection(events)
    return {item_id for item_id, selected in final_state.items() if selected and item_id in target_ids}


def _delayed_responses(events: list[MemoryEvent]) -> list[DelayedResponse]:
    responses: list[DelayedResponse] = []
    order = 0
    for e in events:
        if e.phase != MemoryPhase.DELAYED_RECALL:
            continue
        if e.event_type != MemoryEventType.RESPONSE_SUBMITTED:
            continue
        if not e.value:
            continue
        normalized = _normalize_text(e.value)
        if not normalized:
            continue
        order += 1
        responses.append(
            DelayedResponse(raw_text=e.value, normalized=normalized, timestamp=_ts(e), order=order)
        )
    responses.sort(key=lambda r: r.timestamp)
    return responses


def _recognition_trials(events: list[MemoryEvent]) -> list[MemoryEvent]:
    return [
        e
        for e in events
        if e.phase == MemoryPhase.RECOGNITION and e.event_type == MemoryEventType.RECOGNITION_RESPONSE
    ]


def _phase_boundary(events: list[MemoryEvent], phase: MemoryPhase, event_type: MemoryEventType) -> float | None:
    matches = [_ts(e) for e in events if e.phase == phase and e.event_type == event_type]
    return min(matches) if matches else None


def _game_boundaries(events: list[MemoryEvent]) -> tuple[float | None, float | None]:
    started = [_ts(e) for e in events if e.event_type == MemoryEventType.GAME_STARTED]
    completed = [_ts(e) for e in events if e.event_type == MemoryEventType.GAME_COMPLETED]
    start = min(started) if started else None
    end = max(completed) if completed else None
    return start, end


# ---------------------------------------------------------------------
# Individual feature calculators (kept separate for direct unit testing)
# ---------------------------------------------------------------------


def calculate_immediate_recall_accuracy(events: list[MemoryEvent], targets: list[TargetItem]) -> float:
    if not targets:
        return 0.0
    target_ids = {t.item_id for t in targets}
    selected_targets = _immediate_recall_target_ids_selected(events, target_ids)
    return len(selected_targets) / TARGET_ITEM_COUNT


def _matched_target_labels_in_order(
    responses: list[DelayedResponse], targets: list[TargetItem]
) -> list[tuple[DelayedResponse, TargetItem]]:
    """
    Match delayed-recall responses to targets by normalized label.
    Duplicate valid target entries are not counted as additional correct
    recalls — each target can match at most once (first occurrence wins).
    """
    label_to_target = {_normalize_text(t.label): t for t in targets}
    matched: list[tuple[DelayedResponse, TargetItem]] = []
    used_target_ids: set[str] = set()
    for r in responses:
        target = label_to_target.get(r.normalized)
        if target is None:
            continue
        if target.item_id in used_target_ids:
            continue
        used_target_ids.add(target.item_id)
        matched.append((r, target))
    return matched


def calculate_delayed_recall_accuracy(
    responses: list[DelayedResponse], targets: list[TargetItem]
) -> float:
    matched = _matched_target_labels_in_order(responses, targets)
    return len(matched) / TARGET_ITEM_COUNT


def calculate_recognition_accuracy(trials: list[MemoryEvent]) -> float:
    if not trials:
        raise IncompleteGameDataError("No recognition trials recorded.")
    correct_count = 0
    for e in trials:
        is_target = bool(e.metadata.get("is_target", False))
        response_yes = (e.value or "").strip().upper() == "YES"
        correct = e.metadata.get("correct")
        if correct is None:
            correct = response_yes == is_target
        if correct:
            correct_count += 1
    return correct_count / len(trials)


def calculate_recall_decay_rate(immediate_acc: float, delayed_acc: float) -> float:
    if immediate_acc <= 0:
        return 0.0
    decay = (immediate_acc - delayed_acc) / immediate_acc
    # Clamp: the metric is only meaningful in [0, 1]; a "negative decay"
    # (delayed > immediate) is treated as no decay, not a boosted score.
    return max(0.0, min(1.0, decay))


def calculate_recall_latency(events: list[MemoryEvent], responses: list[DelayedResponse]) -> float:
    phase_start = _phase_boundary(events, MemoryPhase.DELAYED_RECALL, MemoryEventType.PHASE_STARTED)
    if phase_start is None:
        raise IncompleteGameDataError("DELAYED_RECALL phase_started event missing.")
    if not responses:
        raise IncompleteGameDataError("No valid delayed recall response was submitted.")
    first_response_ts = min(r.timestamp for r in responses)
    latency = first_response_ts - phase_start
    return max(0.0, latency)


def calculate_omission_errors(matched_count: int) -> int:
    return max(0, TARGET_ITEM_COUNT - matched_count)


def calculate_intrusion_errors(responses: list[DelayedResponse], targets: list[TargetItem]) -> int:
    target_labels = {_normalize_text(t.label) for t in targets}
    return sum(1 for r in responses if r.normalized not in target_labels)


def calculate_sequence_recall_accuracy(
    matched: list[tuple[DelayedResponse, TargetItem]]
) -> float:
    if len(matched) < 2:
        return 0.0
    # matched is already ordered by response submission order (see caller)
    positions = [target.position for _response, target in matched]
    preserved = 0
    pairs = 0
    for a, b in zip(positions, positions[1:]):
        pairs += 1
        if a < b:
            preserved += 1
    return preserved / pairs if pairs else 0.0


def calculate_hesitation_duration(responses: list[DelayedResponse]) -> float:
    if len(responses) < 2:
        return 0.0
    total = 0.0
    for prev, curr in zip(responses, responses[1:]):
        gap = curr.timestamp - prev.timestamp
        if gap > HESITATION_THRESHOLD_SECONDS:
            total += gap - HESITATION_THRESHOLD_SECONDS
    return total


def calculate_retry_frequency(events: list[MemoryEvent]) -> int:
    return sum(
        1
        for e in events
        if e.event_type in (MemoryEventType.RESPONSE_EDITED, MemoryEventType.RETRY)
    )


def calculate_confidence_variability(confidence: MemoryConfidence) -> float:
    values = [confidence.immediate_recall, confidence.delayed_recall, confidence.recognition]
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values)


def calculate_completion_time(events: list[MemoryEvent]) -> float:
    start, end = _game_boundaries(events)
    if start is None or end is None:
        raise IncompleteGameDataError("game_started/game_completed events missing.")
    duration = end - start
    if duration <= 0:
        raise IncompleteGameDataError("completion_time must be greater than zero.")
    return duration


def calculate_memory_consistency_trend(
    immediate_target_ids: set[str], matched: list[tuple[DelayedResponse, TargetItem]]
) -> float:
    if not immediate_target_ids:
        return 0.0
    delayed_target_ids = {target.item_id for _response, target in matched}
    both = immediate_target_ids & delayed_target_ids
    return len(both) / len(immediate_target_ids)


@dataclass
class ExtractedFeatures:
    immediate_recall_accuracy: float
    delayed_recall_accuracy: float
    recognition_accuracy: float
    recall_decay_rate: float
    recall_latency: float
    omission_errors: int
    intrusion_errors: int
    sequence_recall_accuracy: float
    hesitation_duration: float
    retry_frequency: int
    confidence_variability: float
    completion_time: float
    memory_consistency_trend: float


def extract_features(events: list[MemoryEvent], confidence: MemoryConfidence) -> ExtractedFeatures:
    """
    Derive the 13 locked Memory Recall features from a raw telemetry event
    log and confidence ratings. Raises IncompleteGameDataError if the log
    does not contain enough data to compute a required feature — callers
    must not silently default such cases to zero.
    """
    targets = _extract_targets(events)
    if not targets:
        raise IncompleteGameDataError("No LEARNING item_presented events found; cannot score recall.")

    target_ids = {t.item_id for t in targets}
    immediate_target_ids = _immediate_recall_target_ids_selected(events, target_ids)
    immediate_acc = calculate_immediate_recall_accuracy(events, targets)

    responses = _delayed_responses(events)
    matched = _matched_target_labels_in_order(responses, targets)
    delayed_acc = calculate_delayed_recall_accuracy(responses, targets)

    trials = _recognition_trials(events)
    recognition_acc = calculate_recognition_accuracy(trials)

    return ExtractedFeatures(
        immediate_recall_accuracy=immediate_acc,
        delayed_recall_accuracy=delayed_acc,
        recognition_accuracy=recognition_acc,
        recall_decay_rate=calculate_recall_decay_rate(immediate_acc, delayed_acc),
        recall_latency=calculate_recall_latency(events, responses),
        omission_errors=calculate_omission_errors(len(matched)),
        intrusion_errors=calculate_intrusion_errors(responses, targets),
        sequence_recall_accuracy=calculate_sequence_recall_accuracy(matched),
        hesitation_duration=calculate_hesitation_duration(responses),
        retry_frequency=calculate_retry_frequency(events),
        confidence_variability=calculate_confidence_variability(confidence),
        completion_time=calculate_completion_time(events),
        memory_consistency_trend=calculate_memory_consistency_trend(immediate_target_ids, matched),
    )
