import { useEffect, useRef, useState } from "react";

import { GameShell } from "../../../components/ui/GameShell";
import { PrimaryButton } from "../../../components/ui/buttons";
import { SERIAL7_CONFIG } from "../config/mmseConfig";
import { createMMSEEvent, type MMSEEvent } from "../telemetry/mmseEvents";

interface AttentionPhaseProps {
  assessmentId: string;
  onEvent: (event: MMSEEvent) => void;
  onComplete: () => void;
}

export function AttentionPhase({ assessmentId, onEvent, onComplete }: AttentionPhaseProps) {
  const [attemptIndex, setAttemptIndex] = useState(0);
  const [currentNumber, setCurrentNumber] = useState(SERIAL7_CONFIG.startValue);
  const [inputValue, setInputValue] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const presentedQuestionsRef = useRef<Set<string>>(new Set());
  const startedQuestionsRef = useRef<Set<string>>(new Set());
  const inputRef = useRef<HTMLInputElement | null>(null);

  const questionId =
    SERIAL7_CONFIG.questionIds[attemptIndex] ?? `serial7_${attemptIndex + 1}`;
  const subtractionValue = SERIAL7_CONFIG.step;
  const expectedAnswer = currentNumber - subtractionValue;
  const promptText = `${currentNumber} minus ${subtractionValue}`;

  // Emit question_presented dynamically for the current question
  useEffect(() => {
    if (!presentedQuestionsRef.current.has(questionId)) {
      presentedQuestionsRef.current.add(questionId);
      onEvent(
        createMMSEEvent({
          assessmentId,
          phase: "ATTENTION",
          eventType: "question_presented",
          questionId,
          metadata: {
            prompt: promptText,
            expected_answer: String(expectedAnswer),
            domain: "serial7",
            starting_number: currentNumber,
            subtraction_value: subtractionValue,
            attempt: attemptIndex + 1,
            total_attempts: SERIAL7_CONFIG.totalAttempts,
          },
        })
      );
    }
  }, [assessmentId, attemptIndex, currentNumber, expectedAnswer, onEvent, promptText, questionId, subtractionValue]);

  function ensureResponseStarted() {
    if (!startedQuestionsRef.current.has(questionId)) {
      startedQuestionsRef.current.add(questionId);
      onEvent(
        createMMSEEvent({
          assessmentId,
          phase: "ATTENTION",
          eventType: "response_started",
          questionId,
          metadata: {
            domain: "serial7",
            attempt: attemptIndex + 1,
          },
        })
      );
    }
  }

  function advanceToNext(nextStartingNumber: number) {
    if (attemptIndex + 1 >= SERIAL7_CONFIG.totalAttempts) {
      onComplete();
    } else {
      setCurrentNumber(nextStartingNumber);
      setAttemptIndex((prev) => prev + 1);
      setInputValue("");
      setIsSubmitting(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }

  function handleSubmit() {
    if (isSubmitting) return;

    const trimmed = inputValue.trim();
    if (!trimmed) {
      setValidationError("Please enter a number, or click 'Skip question' to continue.");
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
    ensureResponseStarted();

    const userAnswer = trimmed;
    const parsedUserAnswer = parseInt(trimmed, 10);
    const isCorrect = parsedUserAnswer === expectedAnswer;

    onEvent(
      createMMSEEvent({
        assessmentId,
        phase: "ATTENTION",
        eventType: "response_submitted",
        questionId,
        value: userAnswer,
        metadata: {
          prompt: promptText,
          expected_answer: String(expectedAnswer),
          domain: "serial7",
          starting_number: currentNumber,
          subtraction_value: subtractionValue,
          user_answer: userAnswer,
          is_correct: isCorrect,
          attempt: attemptIndex + 1,
        },
      })
    );

    advanceToNext(parsedUserAnswer);
  }

  function handleSkip() {
    if (isSubmitting) return;
    setIsSubmitting(true);
    setValidationError(null);
    ensureResponseStarted();

    const userAnswer = "";
    const isCorrect = false;

    onEvent(
      createMMSEEvent({
        assessmentId,
        phase: "ATTENTION",
        eventType: "response_submitted",
        questionId,
        value: userAnswer,
        metadata: {
          prompt: promptText,
          expected_answer: String(expectedAnswer),
          domain: "serial7",
          starting_number: currentNumber,
          subtraction_value: subtractionValue,
          user_answer: userAnswer,
          is_correct: isCorrect,
          skipped: true,
          attempt: attemptIndex + 1,
        },
      })
    );

    // When skipped, participant did not provide a number; retain currentNumber for next question
    advanceToNext(currentNumber);
  }

  return (
    <GameShell title="MMSE" phase="Attention and Serial 7s" progress="04 / 07">
      <div className="mmse-stack">
        <p className="mmse-caption" style={{ margin: 0 }}>
          Question {attemptIndex + 1} of {SERIAL7_CONFIG.totalAttempts}
        </p>
        <label className="mmse-field">
          <span style={{ fontSize: "1.25rem", fontWeight: 600, color: "var(--text)" }}>
            {promptText}
          </span>
          <input
            ref={inputRef}
            type="text"
            inputMode="numeric"
            value={inputValue}
            placeholder="Enter your answer"
            autoFocus
            disabled={isSubmitting}
            onFocus={ensureResponseStarted}
            onChange={(event) => {
              setInputValue(event.target.value);
              if (validationError) setValidationError(null);
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                handleSubmit();
              }
            }}
          />
        </label>
        {validationError && (
          <div
            className="mmse-error-message"
            role="alert"
            style={{ color: "var(--error, #dc2626)", fontSize: "0.9rem" }}
          >
            {validationError}
          </div>
        )}
      </div>
      <div className="mmse-actions">
        <PrimaryButton type="button" onClick={handleSubmit} disabled={isSubmitting}>
          {attemptIndex + 1 < SERIAL7_CONFIG.totalAttempts ? "Submit & Next" : "Submit & Finish"}
        </PrimaryButton>
        <button
          type="button"
          onClick={handleSkip}
          disabled={isSubmitting}
          className="memory-skip-button"
          style={{
            minHeight: "48px",
            padding: "0 18px",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-md)",
            background: "transparent",
            color: "var(--text-muted)",
            cursor: "pointer",
          }}
        >
          Skip question
        </button>
      </div>
    </GameShell>
  );
}
