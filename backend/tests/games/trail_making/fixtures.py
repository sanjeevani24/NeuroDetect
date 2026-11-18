from __future__ import annotations

from datetime import datetime, timedelta

from app.games.trail_making.config import DEFAULT_CONFIG, TrailNodeType
from app.games.trail_making.schemas import (
    TrailMakingErrorType,
    TrailMakingEventType,
    TrailMakingNodeLayout,
    TrailMakingPhase,
    TrailMakingTelemetryEvent,
)

ASSESSMENT_ID = "33333333-3333-3333-3333-333333333333"
GAME_SESSION_ID = "44444444-4444-4444-4444-444444444444"
T0 = datetime(2026, 1, 1, 12, 0, 0)


def build_layout() -> list[TrailMakingNodeLayout]:
    layout: list[TrailMakingNodeLayout] = []
    for index, label in enumerate(DEFAULT_CONFIG.sequence_labels):
        layout.append(
            TrailMakingNodeLayout(
                node_id=f"node-{index}",
                label=label,
                node_type=TrailNodeType.NUMBER if label.isdigit() else TrailNodeType.LETTER,
                sequence_index=index,
                x=60 + (index % 5) * 150,
                y=70 + (index // 5) * 95,
            )
        )
    return layout


def make_event(
    event_type: TrailMakingEventType,
    offset_ms: float,
    *,
    node: TrailMakingNodeLayout | None = None,
    pointer_x: float | None = None,
    pointer_y: float | None = None,
    was_correct: bool | None = None,
    error_type: TrailMakingErrorType | None = None,
    expected_sequence_index: int | None = None,
    event_payload: dict | None = None,
):
    return TrailMakingTelemetryEvent(
        event_id=f"evt-{event_type.value}-{offset_ms}-{node.node_id if node else 'global'}",
        assessment_id=ASSESSMENT_ID,
        game_session_id=GAME_SESSION_ID,
        phase=TrailMakingPhase.RUNNING if event_type != TrailMakingEventType.GAME_STARTED else TrailMakingPhase.INTRO,
        event_type=event_type,
        timestamp=T0 + timedelta(milliseconds=offset_ms),
        relative_time_ms=offset_ms,
        node_id=node.node_id if node else None,
        node_label=node.label if node else None,
        node_type=node.node_type if node else None,
        sequence_index=node.sequence_index if node else None,
        expected_sequence_index=expected_sequence_index,
        x=node.x if node else None,
        y=node.y if node else None,
        pointer_x=pointer_x,
        pointer_y=pointer_y,
        was_correct=was_correct,
        error_type=error_type,
        event_payload=event_payload or {},
    )


def perfect_request():
    layout = build_layout()
    events: list[TrailMakingTelemetryEvent] = [make_event(TrailMakingEventType.GAME_STARTED, 0)]
    current_time = 0.0
    for index, node in enumerate(layout):
        current_time += 150
        prev_node = layout[index - 1] if index > 0 else node
        for step in range(1, 4):
            x = prev_node.x + ((node.x - prev_node.x) * step / 3)
            y = prev_node.y + ((node.y - prev_node.y) * step / 3)
            events.append(make_event(TrailMakingEventType.POINTER_SAMPLE, current_time + (step * 30), pointer_x=x, pointer_y=y))
        click_time = current_time + 150
        events.append(
            make_event(
                TrailMakingEventType.NODE_CLICKED,
                click_time,
                node=node,
                pointer_x=node.x,
                pointer_y=node.y,
                was_correct=True,
                error_type=TrailMakingErrorType.CORRECT,
                expected_sequence_index=index,
            )
        )
        events.append(
            make_event(
                TrailMakingEventType.TARGET_COMPLETED,
                click_time,
                node=node,
                pointer_x=node.x,
                pointer_y=node.y,
                was_correct=True,
                error_type=TrailMakingErrorType.CORRECT,
                expected_sequence_index=index,
            )
        )
        current_time = click_time
    events.append(make_event(TrailMakingEventType.GAME_COMPLETED, current_time + 50))
    return layout, events


def error_heavy_request():
    layout, events = perfect_request()
    wrong = layout[3]
    events.insert(
        6,
        make_event(
            TrailMakingEventType.NODE_CLICKED,
            220,
            node=wrong,
            pointer_x=wrong.x + 20,
            pointer_y=wrong.y + 20,
            was_correct=False,
            error_type=TrailMakingErrorType.OUT_OF_ORDER,
            expected_sequence_index=0,
        ),
    )
    events.insert(
        7,
        make_event(TrailMakingEventType.POINTER_SAMPLE, 260, pointer_x=wrong.x - 25, pointer_y=wrong.y - 15),
    )
    return layout, events
