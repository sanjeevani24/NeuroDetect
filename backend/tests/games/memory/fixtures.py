"""
Deterministic fixtures for Memory Recall tests.

No randomness anywhere. Every helper takes explicit inputs and produces a
fixed, reconstructable event stream so tests are exact and repeatable.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from app.games.memory.schemas import MemoryConfidence, MemoryEvent, MemoryEventType, MemoryPhase

ASSESSMENT_ID = "11111111-1111-1111-1111-111111111111"

TARGET_LABELS = [
    "apple",
    "chair",
    "train",
    "river",
    "clock",
    "bottle",
    "garden",
    "book",
    "camera",
    "shoe",
    "flower",
    "key",
]

TARGET_IDS = [f"item_{i:03d}" for i in range(1, len(TARGET_LABELS) + 1)]

BASE_TIME = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

_counter = {"n": 0}


def _next_event_id() -> str:
    _counter["n"] += 1
    return f"evt_{_counter['n']:05d}"


def reset_event_counter() -> None:
    _counter["n"] = 0


def t(seconds: float) -> datetime:
    return BASE_TIME + timedelta(seconds=seconds)


def make_event(
    phase: MemoryPhase,
    event_type: MemoryEventType,
    timestamp: datetime,
    item_id: Optional[str] = None,
    trial_id: Optional[str] = None,
    value: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> MemoryEvent:
    return MemoryEvent(
        event_id=_next_event_id(),
        assessment_id=ASSESSMENT_ID,
        game="memory",
        phase=phase,
        event_type=event_type,
        timestamp=timestamp,
        item_id=item_id,
        trial_id=trial_id,
        value=value,
        metadata=metadata or {},
    )


def learning_events(start_seconds: float = 1.0, item_duration: float = 3.0) -> list[MemoryEvent]:
    events = []
    for i, (item_id, label) in enumerate(zip(TARGET_IDS, TARGET_LABELS)):
        shown_at = t(start_seconds + i * item_duration)
        hidden_at = t(start_seconds + i * item_duration + item_duration * 0.8)
        events.append(
            make_event(
                MemoryPhase.LEARNING,
                MemoryEventType.ITEM_PRESENTED,
                shown_at,
                item_id=item_id,
                metadata={"label": label, "position": i},
            )
        )
        events.append(
            make_event(
                MemoryPhase.LEARNING,
                MemoryEventType.ITEM_HIDDEN,
                hidden_at,
                item_id=item_id,
            )
        )
    return events


def immediate_recall_events(
    selected_target_ids: list[str], start_seconds: float = 60.0
) -> list[MemoryEvent]:
    events = []
    for i, item_id in enumerate(selected_target_ids):
        events.append(
            make_event(
                MemoryPhase.IMMEDIATE_RECALL,
                MemoryEventType.ITEM_SELECTED,
                t(start_seconds + i),
                item_id=item_id,
                metadata={"is_target": item_id in TARGET_IDS},
            )
        )
    return events


def delayed_recall_events(
    responses: list[str], start_seconds: float, gap_seconds: float = 1.0
) -> list[MemoryEvent]:
    events = []
    for i, text in enumerate(responses):
        events.append(
            make_event(
                MemoryPhase.DELAYED_RECALL,
                MemoryEventType.RESPONSE_SUBMITTED,
                t(start_seconds + i * gap_seconds),
                value=text,
                metadata={"response_order": i},
            )
        )
    return events


def recognition_events(
    trials: list[tuple[str, bool, str]], start_seconds: float
) -> list[MemoryEvent]:
    """trials: list of (item_id, is_target, response 'YES'/'NO')"""
    events = []
    for i, (item_id, is_target, response) in enumerate(trials):
        correct = (response == "YES") == is_target
        events.append(
            make_event(
                MemoryPhase.RECOGNITION,
                MemoryEventType.RECOGNITION_RESPONSE,
                t(start_seconds + i * 2),
                item_id=item_id,
                trial_id=f"trial_{i:03d}",
                value=response,
                metadata={"is_target": is_target, "correct": correct},
            )
        )
    return events


def phase_boundary(phase: MemoryPhase, event_type: MemoryEventType, seconds: float) -> MemoryEvent:
    return make_event(phase, event_type, t(seconds))


def game_started(seconds: float = 0.0) -> MemoryEvent:
    return make_event(MemoryPhase.INTRO, MemoryEventType.GAME_STARTED, t(seconds))


def game_completed(seconds: float) -> MemoryEvent:
    return make_event(MemoryPhase.COMPLETE, MemoryEventType.GAME_COMPLETED, t(seconds))


def default_confidence() -> MemoryConfidence:
    return MemoryConfidence(immediate_recall=4, delayed_recall=3, recognition=5)


def build_full_happy_path_events() -> list[MemoryEvent]:
    """
    Matches the worked example in the spec:
      immediate recall: 9/12 correct (first 9 targets selected)
      delayed recall: 7/12 correct (first 7 targets recalled) + 1 intrusion ("dog")
      omission_errors: 5
    """
    reset_event_counter()
    events: list[MemoryEvent] = [game_started(0.0)]

    events.append(phase_boundary(MemoryPhase.LEARNING, MemoryEventType.PHASE_STARTED, 1.0))
    events += learning_events(start_seconds=1.0)
    events.append(phase_boundary(MemoryPhase.LEARNING, MemoryEventType.PHASE_COMPLETED, 40.0))

    events.append(
        phase_boundary(MemoryPhase.IMMEDIATE_RECALL, MemoryEventType.PHASE_STARTED, 41.0)
    )
    events += immediate_recall_events(TARGET_IDS[:9], start_seconds=42.0)
    events.append(
        phase_boundary(MemoryPhase.IMMEDIATE_RECALL, MemoryEventType.PHASE_COMPLETED, 55.0)
    )

    events.append(phase_boundary(MemoryPhase.DISTRACTOR, MemoryEventType.PHASE_STARTED, 56.0))
    events.append(
        make_event(MemoryPhase.DISTRACTOR, MemoryEventType.PHASE_COMPLETED, t(86.0))
    )

    events.append(
        phase_boundary(MemoryPhase.DELAYED_RECALL, MemoryEventType.PHASE_STARTED, 87.0)
    )
    delayed_responses = TARGET_LABELS[:7] + ["dog"]
    events += delayed_recall_events(delayed_responses, start_seconds=90.0, gap_seconds=1.5)
    events.append(
        phase_boundary(MemoryPhase.DELAYED_RECALL, MemoryEventType.PHASE_COMPLETED, 110.0)
    )

    events.append(phase_boundary(MemoryPhase.RECOGNITION, MemoryEventType.PHASE_STARTED, 111.0))
    recog_trials = [(item_id, True, "YES") for item_id in TARGET_IDS] + [
        ("distractor_1", False, "NO"),
        ("distractor_2", False, "NO"),
    ]
    events += recognition_events(recog_trials, start_seconds=112.0)
    events.append(
        phase_boundary(MemoryPhase.RECOGNITION, MemoryEventType.PHASE_COMPLETED, 145.0)
    )

    events.append(phase_boundary(MemoryPhase.CONFIDENCE, MemoryEventType.PHASE_STARTED, 146.0))
    events.append(phase_boundary(MemoryPhase.CONFIDENCE, MemoryEventType.PHASE_COMPLETED, 150.0))

    events.append(game_completed(151.0))
    return events
