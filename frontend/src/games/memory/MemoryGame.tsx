import { useEffect, useReducer, useRef, useState } from "react";
import "./MemoryGame.css";

import { CompletionState, ErrorState, LoadingState } from "../../components/ui/States";
import { PrimaryButton } from "../../components/ui/buttons";
import { completeMemoryGame, ApiError, type MemoryGameResult } from "../../services/api";
import { ConfidenceInput } from "./components/ConfidenceInput";
import { DelayedRecall } from "./components/DelayedRecall";
import { DistractorPhase } from "./components/DistractorPhase";
import { ImmediateRecall } from "./components/ImmediateRecall";
import { LearningPhase } from "./components/LearningPhase";
import { MemoryIntro } from "./components/MemoryIntro";
import { MemoryProgress } from "./components/MemoryProgress";
import { RecognitionPhase } from "./components/RecognitionPhase";
import { memoryReducer, initialMemoryState } from "./state/memoryState";
import { createMemoryEvent } from "./telemetry/memoryEvents";
import type { MemoryEvent } from "./telemetry/eventTypes";
import type { MemoryPhase } from "./types/memoryTypes";

interface MemoryGameProps {
  assessmentId: string;
  onComplete?: () => void;
}

type SubmissionStatus = "idle" | "submitting" | "success" | "error";

const CONFIDENCE_STEPS: Array<{
  key: "immediate_recall" | "delayed_recall" | "recognition";
  label: string;
}> = [
  { key: "immediate_recall", label: "How confident were you in your immediate recall?" },
  { key: "delayed_recall", label: "How confident were you in your delayed recall?" },
  { key: "recognition", label: "How confident were you in your recognition answers?" },
];

const NEXT_PHASE: Record<Exclude<MemoryPhase, "COMPLETE">, MemoryPhase> = {
  INTRO: "LEARNING",
  LEARNING: "IMMEDIATE_RECALL",
  IMMEDIATE_RECALL: "DISTRACTOR",
  DISTRACTOR: "DELAYED_RECALL",
  DELAYED_RECALL: "RECOGNITION",
  RECOGNITION: "CONFIDENCE",
  CONFIDENCE: "COMPLETE",
};

export function MemoryGame({ assessmentId, onComplete }: MemoryGameProps) {
  const [state, dispatch] = useReducer(memoryReducer, undefined, initialMemoryState);
  const [confidenceStepIndex, setConfidenceStepIndex] = useState(0);
  const [submissionStatus, setSubmissionStatus] = useState<SubmissionStatus>("idle");
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [result, setResult] = useState<MemoryGameResult | null>(null);
  const submittedRef = useRef(false);

  function appendEvent(event: MemoryEvent) {
    dispatch({ type: "APPEND_EVENT", event });
  }

  function handleStart() {
    dispatch({
      type: "START_GAME",
      event: createMemoryEvent({ assessmentId, phase: "INTRO", eventType: "game_started" }),
    });
    dispatch({
      type: "APPEND_EVENT",
      event: createMemoryEvent({ assessmentId, phase: "LEARNING", eventType: "phase_started" }),
    });
  }

  function advancePhase(completedPhase: MemoryEvent["phase"]) {
    if (completedPhase === "COMPLETE") return;
    dispatch({
      type: "APPEND_EVENT",
      event: createMemoryEvent({ assessmentId, phase: completedPhase, eventType: "phase_completed" }),
    });
    dispatch({
      type: "ADVANCE_PHASE",
      event: createMemoryEvent({
        assessmentId,
        phase: NEXT_PHASE[completedPhase],
        eventType: "phase_started",
      }),
    });
  }

  async function handleConfidenceSubmit(value: number, event: MemoryEvent) {
    const step = CONFIDENCE_STEPS[confidenceStepIndex];
    dispatch({ type: "SET_CONFIDENCE", phase: step.key, value, event });

    if (confidenceStepIndex + 1 < CONFIDENCE_STEPS.length) {
      setConfidenceStepIndex((prev) => prev + 1);
      return;
    }

    const phaseCompletedEvent = createMemoryEvent({
      assessmentId,
      phase: "CONFIDENCE",
      eventType: "phase_completed",
    });
    dispatch({ type: "APPEND_EVENT", event: phaseCompletedEvent });

    const gameCompletedEvent = createMemoryEvent({
      assessmentId,
      phase: "COMPLETE",
      eventType: "game_completed",
    });
    dispatch({ type: "COMPLETE_GAME", event: gameCompletedEvent });

    await submitGame([...state.events, event, phaseCompletedEvent, gameCompletedEvent], {
      immediate_recall: step.key === "immediate_recall" ? value : state.confidence.immediate_recall!,
      delayed_recall: step.key === "delayed_recall" ? value : state.confidence.delayed_recall!,
      recognition: step.key === "recognition" ? value : state.confidence.recognition!,
    });
  }

  async function submitGame(
    events: MemoryEvent[],
    confidence: { immediate_recall: number; delayed_recall: number; recognition: number }
  ) {
    if (submittedRef.current) return;
    submittedRef.current = true;
    setSubmissionStatus("submitting");
    try {
      const response = await completeMemoryGame(assessmentId, { events, confidence });
      setResult(response);
      setSubmissionStatus("success");
    } catch (err) {
      submittedRef.current = false;
      setSubmissionStatus("error");
      setSubmissionError(err instanceof ApiError ? String(err.detail ?? err.message) : "Something went wrong.");
    }
  }

  useEffect(() => {
    if (submissionStatus !== "success") return;
    const timer = window.setTimeout(() => onComplete?.(), 1200);
    return () => window.clearTimeout(timer);
  }, [onComplete, submissionStatus]);

  return (
    <div className="memory-game">
      {state.phase !== "INTRO" && state.phase !== "COMPLETE" ? <MemoryProgress phase={state.phase} /> : null}

      {state.phase === "INTRO" ? <MemoryIntro onStart={handleStart} /> : null}

      {state.phase === "LEARNING" ? (
        <LearningPhase assessmentId={assessmentId} onItemEvent={appendEvent} onComplete={() => advancePhase("LEARNING")} />
      ) : null}

      {state.phase === "IMMEDIATE_RECALL" ? (
        <ImmediateRecall
          assessmentId={assessmentId}
          onEvent={appendEvent}
          onComplete={() => advancePhase("IMMEDIATE_RECALL")}
        />
      ) : null}

      {state.phase === "DISTRACTOR" ? (
        <DistractorPhase assessmentId={assessmentId} onEvent={appendEvent} onComplete={() => advancePhase("DISTRACTOR")} />
      ) : null}

      {state.phase === "DELAYED_RECALL" ? (
        <DelayedRecall assessmentId={assessmentId} onEvent={appendEvent} onComplete={() => advancePhase("DELAYED_RECALL")} />
      ) : null}

      {state.phase === "RECOGNITION" ? (
        <RecognitionPhase assessmentId={assessmentId} onEvent={appendEvent} onComplete={() => advancePhase("RECOGNITION")} />
      ) : null}

      {state.phase === "CONFIDENCE" ? (
        <ConfidenceInput
          key={CONFIDENCE_STEPS[confidenceStepIndex].key}
          assessmentId={assessmentId}
          phase={CONFIDENCE_STEPS[confidenceStepIndex].key}
          label={CONFIDENCE_STEPS[confidenceStepIndex].label}
          onSubmit={handleConfidenceSubmit}
        />
      ) : null}

      {state.phase === "COMPLETE" ? (
        <div className="memory-phase memory-complete">
          {submissionStatus === "submitting" || submissionStatus === "idle" ? (
            <LoadingState
              title="Saving Memory Recall results"
              message="Your responses are being processed."
            />
          ) : null}
          {submissionStatus === "success" && result ? (
            <CompletionState
              title="Memory Recall complete"
              message="Thank you. Your responses have been recorded for this stage."
            />
          ) : null}
          {submissionStatus === "error" ? (
            <ErrorState
              title="We could not save Memory Recall"
              message={`The backend returned: ${submissionError}`}
              action={
                <PrimaryButton
                  type="button"
                  onClick={() =>
                    submitGame(state.events, {
                      immediate_recall: state.confidence.immediate_recall!,
                      delayed_recall: state.confidence.delayed_recall!,
                      recognition: state.confidence.recognition!,
                    })
                  }
                >
                  Retry submission
                </PrimaryButton>
              }
            />
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
