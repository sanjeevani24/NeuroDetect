import pytest
from datetime import datetime, timezone

from app.games.mmse.features import (
    calculate_attention_accuracy,
    calculate_omission_errors,
    calculate_serial7_accuracy,
    extract_features,
)
from app.games.mmse.schemas import MMSEEvent, MMSEEventType, MMSEPhase


def _make_event(phase: MMSEPhase, event_type: MMSEEventType, offset: float, **kwargs) -> MMSEEvent:
    base_time = datetime(2026, 8, 23, 10, 0, 0, tzinfo=timezone.utc).timestamp()
    ts = datetime.fromtimestamp(base_time + offset, tz=timezone.utc)
    return MMSEEvent(
        event_id=f"evt_{offset}",
        assessment_id="test-assessment",
        game="mmse",
        phase=phase,
        event_type=event_type,
        timestamp=ts,
        **kwargs,
    )


def test_scenario_a_all_correct_dynamic_serial7():
    """Scenario A: 93 -> 86 -> 79 -> 72 -> 65 all correct -> accuracy 1.0."""
    events: list[MMSEEvent] = []
    current = 100
    answers = [93, 86, 79, 72, 65]

    for idx, ans in enumerate(answers):
        qid = f"serial7_{idx + 1}"
        expected = current - 7
        offset = float(idx * 2)

        # question_presented
        events.append(
            _make_event(
                MMSEPhase.ATTENTION,
                MMSEEventType.QUESTION_PRESENTED,
                offset,
                question_id=qid,
                metadata={
                    "prompt": f"{current} minus 7",
                    "expected_answer": str(expected),
                    "domain": "serial7",
                    "starting_number": current,
                    "subtraction_value": 7,
                    "attempt": idx + 1,
                },
            )
        )
        # response_started
        events.append(
            _make_event(
                MMSEPhase.ATTENTION,
                MMSEEventType.RESPONSE_STARTED,
                offset + 0.2,
                question_id=qid,
            )
        )
        # response_submitted
        events.append(
            _make_event(
                MMSEPhase.ATTENTION,
                MMSEEventType.RESPONSE_SUBMITTED,
                offset + 1.0,
                question_id=qid,
                value=str(ans),
                metadata={
                    "prompt": f"{current} minus 7",
                    "expected_answer": str(expected),
                    "domain": "serial7",
                    "starting_number": current,
                    "subtraction_value": 7,
                    "user_answer": str(ans),
                    "is_correct": ans == expected,
                    "attempt": idx + 1,
                },
            )
        )
        current = ans

    accuracy = calculate_serial7_accuracy(events)
    assert accuracy == pytest.approx(1.0)


def test_scenario_b_incorrect_then_correct_dynamic_serial7():
    """Scenario B: 92 (incorrect for 100-7=93), then next question dynamically starts at 92!

    92 - 7 = 85 (user gives 85 -> correct)
    85 - 7 = 78 (user gives 78 -> correct)
    78 - 7 = 71 (user gives 71 -> correct)
    71 - 7 = 64 (user gives 64 -> correct)
    Result: 4 out of 5 correct = 0.8 accuracy.
    """
    events: list[MMSEEvent] = []
    current = 100
    answers = [92, 85, 78, 71, 64]

    for idx, ans in enumerate(answers):
        qid = f"serial7_{idx + 1}"
        expected = current - 7
        offset = float(idx * 2)

        events.append(
            _make_event(
                MMSEPhase.ATTENTION,
                MMSEEventType.QUESTION_PRESENTED,
                offset,
                question_id=qid,
                metadata={
                    "prompt": f"{current} minus 7",
                    "expected_answer": str(expected),
                    "domain": "serial7",
                    "starting_number": current,
                    "subtraction_value": 7,
                    "attempt": idx + 1,
                },
            )
        )
        events.append(
            _make_event(
                MMSEPhase.ATTENTION,
                MMSEEventType.RESPONSE_STARTED,
                offset + 0.2,
                question_id=qid,
            )
        )
        events.append(
            _make_event(
                MMSEPhase.ATTENTION,
                MMSEEventType.RESPONSE_SUBMITTED,
                offset + 1.0,
                question_id=qid,
                value=str(ans),
                metadata={
                    "prompt": f"{current} minus 7",
                    "expected_answer": str(expected),
                    "domain": "serial7",
                    "starting_number": current,
                    "subtraction_value": 7,
                    "user_answer": str(ans),
                    "is_correct": ans == expected,
                    "attempt": idx + 1,
                },
            )
        )
        # Dynamic progression: next starts with patient's actual answer!
        current = ans

    accuracy = calculate_serial7_accuracy(events)
    assert accuracy == pytest.approx(0.8)


def test_scenario_c_skipped_question_records_omission():
    """Scenario C: When user skips question 1, value is empty, counts as attention omission."""
    events: list[MMSEEvent] = []
    qid = "serial7_1"
    events.append(
        _make_event(
            MMSEPhase.ATTENTION,
            MMSEEventType.QUESTION_PRESENTED,
            1.0,
            question_id=qid,
            metadata={"domain": "serial7", "expected_answer": "93"},
        )
    )
    events.append(
        _make_event(
            MMSEPhase.ATTENTION,
            MMSEEventType.RESPONSE_STARTED,
            1.2,
            question_id=qid,
        )
    )
    events.append(
        _make_event(
            MMSEPhase.ATTENTION,
            MMSEEventType.RESPONSE_SUBMITTED,
            2.0,
            question_id=qid,
            value="",  # skipped / omitted
            metadata={"domain": "serial7", "expected_answer": "93", "skipped": True},
        )
    )

    attention_omissions = sum(
        1 for e in events if e.phase == MMSEPhase.ATTENTION and e.event_type == MMSEEventType.RESPONSE_SUBMITTED and not (e.value or "").strip()
    )
    assert attention_omissions == 1

    accuracy = calculate_serial7_accuracy(events)
    assert accuracy == 0.0
