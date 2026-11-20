import { useEffect, useRef, useState } from "react";
import { DISTRACTOR_CONFIG } from "../config/memoryConfig";
import { createMemoryEvent } from "../telemetry/memoryEvents";
import type { MemoryEvent } from "../telemetry/eventTypes";

interface DistractorPhaseProps {
  assessmentId: string;
  onEvent: (event: MemoryEvent) => void;
  onComplete: () => void;
}

/**
 * Controlled distractor: count backwards from 100 by 3s.
 * Displays current number dynamically based on the participant's actual responses.
 * Never exposes the expected answer in the UI or placeholder.
 */
export function DistractorPhase({ assessmentId, onEvent, onComplete }: DistractorPhaseProps) {
  const [currentNumber, setCurrentNumber] = useState(DISTRACTOR_CONFIG.startValue);
  const [input, setInput] = useState("");
  const [attemptCount, setAttemptCount] = useState(0);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const startedRef = useRef(false);
  const finishedRef = useRef(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const maxAttempts = DISTRACTOR_CONFIG.maxAttempts ?? 5;
  const subtractionValue = DISTRACTOR_CONFIG.step;
  const expectedAnswer = currentNumber - subtractionValue;

  useEffect(() => {
    if (!startedRef.current) {
      startedRef.current = true;
      onEvent(
        createMemoryEvent({
          assessmentId,
          phase: "DISTRACTOR",
          eventType: "response_started",
          metadata: { note: "distractor_started", start_value: DISTRACTOR_CONFIG.startValue },
        })
      );
    }
  }, [assessmentId, onEvent]);

  function finish() {
    if (finishedRef.current) return;
    finishedRef.current = true;
    onEvent(
      createMemoryEvent({
        assessmentId,
        phase: "DISTRACTOR",
        eventType: "response_submitted",
        metadata: {
          note: "distractor_completed",
          total_attempts: attemptCount,
        },
      })
    );
    onComplete();
  }

  function handleSubmit() {
    if (isSubmitting || finishedRef.current) return;

    const trimmed = input.trim();
    if (!trimmed) {
      setValidationError("Please enter a number, or click 'Skip ahead'.");
      inputRef.current?.focus();
      return;
    }

    if (!/^-?\d+$/.test(trimmed)) {
      setValidationError("Please enter a valid whole number.");
      inputRef.current?.focus();
      return;
    }

    setIsSubmitting(true);
    setValidationError(null);

    const userAnswer = trimmed;
    const parsedUserAnswer = parseInt(trimmed, 10);
    const isCorrect = parsedUserAnswer === expectedAnswer;
    const nextAttempt = attemptCount + 1;

    onEvent(
      createMemoryEvent({
        assessmentId,
        phase: "DISTRACTOR",
        eventType: "response_submitted",
        value: userAnswer,
        metadata: {
          starting_number: currentNumber,
          subtraction_value: subtractionValue,
          user_answer: userAnswer,
          expected_answer: String(expectedAnswer),
          is_correct: isCorrect,
          attempt: nextAttempt,
          total_attempts: maxAttempts,
        },
      })
    );

    setAttemptCount(nextAttempt);
    setCurrentNumber(parsedUserAnswer);
    setInput("");
    setIsSubmitting(false);

    if (nextAttempt >= maxAttempts || parsedUserAnswer <= 0) {
      finish();
    } else {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }

  return (
    <div className="memory-phase distractor-phase">
      <p className="memory-instruction">{DISTRACTOR_CONFIG.prompt}</p>
      <p className="memory-progress-count">
        Attempt {Math.min(attemptCount + 1, maxAttempts)} of {maxAttempts}
      </p>
      <p>
        Current: <strong className="memory-distractor-value">{currentNumber}</strong>
      </p>
      <div className="memory-response-row" style={{ maxWidth: "360px", margin: "0 auto" }}>
        <input
          ref={inputRef}
          type="text"
          inputMode="numeric"
          value={input}
          placeholder="Enter your answer"
          autoFocus
          disabled={isSubmitting}
          onChange={(e) => {
            setInput(e.target.value);
            if (validationError) setValidationError(null);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              handleSubmit();
            }
          }}
        />
      </div>
      {validationError && (
        <div
          role="alert"
          style={{ color: "var(--error, #dc2626)", fontSize: "0.9rem", marginTop: "-8px" }}
        >
          {validationError}
        </div>
      )}
      <div className="memory-button-row">
        <button type="button" onClick={handleSubmit} disabled={isSubmitting}>
          Submit
        </button>
        <button type="button" onClick={finish} disabled={isSubmitting} className="memory-skip-button">
          Skip ahead
        </button>
      </div>
    </div>
  );
}
