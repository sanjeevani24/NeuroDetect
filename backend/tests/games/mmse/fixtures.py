from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.games.mmse.schemas import MMSECompletionRequest, MMSEEvent, MMSEEventType, MMSEPhase

ASSESSMENT_ID = "22222222-2222-2222-2222-222222222222"
BASE_TIME = datetime(2026, 8, 23, 10, 0, 0, tzinfo=timezone.utc)

_counter = {"n": 0}


def reset_event_counter() -> None:
    _counter["n"] = 0


def _next_event_id() -> str:
    _counter["n"] += 1
    return f"mmse_evt_{_counter['n']:05d}"


def t(seconds: float) -> datetime:
    return BASE_TIME + timedelta(seconds=seconds)


def make_event(
    phase: MMSEPhase,
    event_type: MMSEEventType,
    seconds: float,
    *,
    question_id: str | None = None,
    item_id: str | None = None,
    value: str | None = None,
    metadata: dict | None = None,
    assessment_id: str = ASSESSMENT_ID,
) -> MMSEEvent:
    return MMSEEvent(
        event_id=_next_event_id(),
        assessment_id=assessment_id,
        game="mmse",
        phase=phase,
        event_type=event_type,
        timestamp=t(seconds),
        question_id=question_id,
        item_id=item_id,
        value=value,
        metadata=metadata or {},
    )


def build_happy_path_events() -> list[MMSEEvent]:
    reset_event_counter()
    events = [
        make_event(MMSEPhase.INTRO, MMSEEventType.GAME_STARTED, 0),
        make_event(MMSEPhase.ORIENTATION, MMSEEventType.PHASE_STARTED, 1),
    ]

    orientation = [
        ("year", "What year is it?", "2026", "2026"),
        ("month", "What month is it?", "August", "August"),
        ("date", "What is today's date?", "23", "23"),
        ("day", "What day of the week is it?", "Sunday", "Sunday"),
        ("location", "What is the name of this assessment site?", "NeuroDetect Clinic", "Clinic"),
    ]
    for index, (question_id, prompt, expected, response) in enumerate(orientation):
        offset = 2 + index * 2
        events.append(
            make_event(
                MMSEPhase.ORIENTATION,
                MMSEEventType.QUESTION_PRESENTED,
                offset,
                question_id=question_id,
                metadata={"prompt": prompt, "expected_answer": expected},
            )
        )
        events.append(make_event(MMSEPhase.ORIENTATION, MMSEEventType.RESPONSE_STARTED, offset + 0.2, question_id=question_id))
        events.append(
            make_event(
                MMSEPhase.ORIENTATION,
                MMSEEventType.RESPONSE_SUBMITTED,
                offset + 1.0,
                question_id=question_id,
                value=response,
                metadata={"prompt": prompt, "expected_answer": expected},
            )
        )
    events.append(make_event(MMSEPhase.ORIENTATION, MMSEEventType.PHASE_COMPLETED, 13))
    events.append(make_event(MMSEPhase.REGISTRATION, MMSEEventType.PHASE_STARTED, 14))

    for index, word in enumerate(("APPLE", "TABLE", "COIN")):
        events.append(
            make_event(
                MMSEPhase.REGISTRATION,
                MMSEEventType.ITEM_PRESENTED,
                15 + index,
                item_id=word.lower(),
                value=word,
                metadata={"target": True},
            )
        )
    events.append(make_event(MMSEPhase.REGISTRATION, MMSEEventType.RESPONSE_STARTED, 19, question_id="registration_recall"))
    for index, word in enumerate(("APPLE", "TABLE", "DOG")):
        events.append(
            make_event(
                MMSEPhase.REGISTRATION,
                MMSEEventType.RESPONSE_SUBMITTED,
                20 + index,
                question_id="registration_recall",
                value=word,
                metadata={"response_order": index + 1},
            )
        )
    events.append(make_event(MMSEPhase.REGISTRATION, MMSEEventType.PHASE_COMPLETED, 24))
    events.append(make_event(MMSEPhase.ATTENTION, MMSEEventType.PHASE_STARTED, 25))

    serial7 = [("serial7_1", "93"), ("serial7_2", "86"), ("serial7_3", "79"), ("serial7_4", "72"), ("serial7_5", "65")]
    for index, (question_id, expected) in enumerate(serial7):
        offset = 26 + index * 2
        actual = expected if question_id != "serial7_3" else "80"
        events.append(
            make_event(
                MMSEPhase.ATTENTION,
                MMSEEventType.QUESTION_PRESENTED,
                offset,
                question_id=question_id,
                metadata={"prompt": question_id, "expected_answer": expected, "domain": "serial7"},
            )
        )
        events.append(make_event(MMSEPhase.ATTENTION, MMSEEventType.RESPONSE_STARTED, offset + 0.2, question_id=question_id))
        events.append(
            make_event(
                MMSEPhase.ATTENTION,
                MMSEEventType.RESPONSE_SUBMITTED,
                offset + 1.0,
                question_id=question_id,
                value=actual,
                metadata={"expected_answer": expected, "domain": "serial7"},
            )
        )
    events.append(make_event(MMSEPhase.ATTENTION, MMSEEventType.RESPONSE_EDITED, 36.5, question_id="serial7_3"))
    events.append(make_event(MMSEPhase.ATTENTION, MMSEEventType.PHASE_COMPLETED, 37))
    events.append(make_event(MMSEPhase.LANGUAGE, MMSEEventType.PHASE_STARTED, 38))

    language = [
        ("naming", "PEN", "PEN"),
        ("repetition", "No ifs, ands, or buts.", "No ifs, ands, or buts."),
        ("reading", "CLOSE", "CLOSE"),
        ("sentence", "patient", "The patient feels calm."),
    ]
    for index, (question_id, expected, response) in enumerate(language):
        offset = 39 + index * 2
        events.append(
            make_event(
                MMSEPhase.LANGUAGE,
                MMSEEventType.QUESTION_PRESENTED,
                offset,
                question_id=question_id,
                metadata={"expected_answer": expected},
            )
        )
        events.append(make_event(MMSEPhase.LANGUAGE, MMSEEventType.RESPONSE_STARTED, offset + 0.2, question_id=question_id))
        events.append(
            make_event(
                MMSEPhase.LANGUAGE,
                MMSEEventType.RESPONSE_SUBMITTED,
                offset + 1.0,
                question_id=question_id,
                value=response,
                metadata={"expected_answer": expected},
            )
        )
    events.append(make_event(MMSEPhase.LANGUAGE, MMSEEventType.PHASE_COMPLETED, 47))
    events.append(make_event(MMSEPhase.DELAYED_RECALL, MMSEEventType.PHASE_STARTED, 48))
    events.append(make_event(MMSEPhase.DELAYED_RECALL, MMSEEventType.RESPONSE_STARTED, 48.2, question_id="delayed_recall"))
    for index, word in enumerate(("APPLE", "COIN", "TREE")):
        events.append(
            make_event(
                MMSEPhase.DELAYED_RECALL,
                MMSEEventType.RESPONSE_SUBMITTED,
                49 + index,
                question_id="delayed_recall",
                value=word,
                metadata={"response_order": index + 1},
            )
        )
    events.append(make_event(MMSEPhase.DELAYED_RECALL, MMSEEventType.PHASE_COMPLETED, 53))
    events.append(make_event(MMSEPhase.COMMAND, MMSEEventType.PHASE_STARTED, 54))
    events.extend(
        [
            make_event(MMSEPhase.COMMAND, MMSEEventType.ITEM_SELECTED, 55, item_id="step_1"),
            make_event(MMSEPhase.COMMAND, MMSEEventType.ITEM_SELECTED, 56, item_id="step_2"),
            make_event(MMSEPhase.COMMAND, MMSEEventType.ITEM_SELECTED, 57, item_id="step_3"),
            make_event(
                MMSEPhase.COMMAND,
                MMSEEventType.ITEM_COMPLETED,
                58,
                question_id="command_sequence",
                value="step_1,step_2,step_3",
                metadata={
                    "expected_sequence": ["step_1", "step_2", "step_3"],
                    "actual_sequence": ["step_1", "step_2", "step_3"],
                },
            ),
            make_event(MMSEPhase.COMMAND, MMSEEventType.PHASE_COMPLETED, 59),
            make_event(MMSEPhase.COMPLETION, MMSEEventType.GAME_COMPLETED, 60),
        ]
    )
    return events


def build_request() -> MMSECompletionRequest:
    return MMSECompletionRequest(events=build_happy_path_events())
