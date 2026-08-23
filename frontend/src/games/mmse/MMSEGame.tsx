import { useEffect, useReducer, useRef, useState } from "react";

import "./MMSEGame.css";

import { ApiError, completeMMSEGame } from "../../services/api";
import { MMSECompletion } from "./components/MMSECompletion";
import { MMSEIntro } from "./components/MMSEIntro";
import { OrientationPhase } from "./components/OrientationPhase";
import { RegistrationPhase } from "./components/RegistrationPhase";
import { AttentionPhase } from "./components/AttentionPhase";
import { LanguagePhase } from "./components/LanguagePhase";
import { DelayedRecallPhase } from "./components/DelayedRecallPhase";
import { CommandPhase } from "./components/CommandPhase";
import { createMMSEEvent, type MMSEEvent } from "./telemetry/mmseEvents";
import { initialMMSEState, mmseReducer } from "./state/mmseState";
import type { MMSEPhase } from "./types/mmseTypes";

interface MMSEGameProps {
  assessmentId: string;
  onComplete?: () => void;
}

type SubmissionStatus = "idle" | "submitting" | "success" | "error";

const NEXT_PHASE: Record<Exclude<MMSEPhase, "COMPLETION">, MMSEPhase> = {
  INTRO: "ORIENTATION",
  ORIENTATION: "REGISTRATION",
  REGISTRATION: "ATTENTION",
  ATTENTION: "LANGUAGE",
  LANGUAGE: "DELAYED_RECALL",
  DELAYED_RECALL: "COMMAND",
  COMMAND: "COMPLETION",
};

export function MMSEGame({ assessmentId, onComplete }: MMSEGameProps) {
  const [state, dispatch] = useReducer(mmseReducer, undefined, initialMMSEState);
  const [submissionStatus, setSubmissionStatus] = useState<SubmissionStatus>("idle");
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const submittedRef = useRef(false);

  function appendEvent(event: MMSEEvent) {
    dispatch({ type: "APPEND_EVENT", event });
  }

  function startGame() {
    dispatch({
      type: "START",
      event: createMMSEEvent({ assessmentId, phase: "INTRO", eventType: "game_started" }),
    });
    dispatch({
      type: "APPEND_EVENT",
      event: createMMSEEvent({ assessmentId, phase: "ORIENTATION", eventType: "phase_started" }),
    });
  }

  function advance(phase: MMSEEvent["phase"]) {
    if (phase === "COMPLETION") return;
    const nextPhase = NEXT_PHASE[phase];
    dispatch({
      type: "APPEND_EVENT",
      event: createMMSEEvent({ assessmentId, phase, eventType: "phase_completed" }),
    });
    dispatch({
      type: "ADVANCE",
      event: createMMSEEvent({ assessmentId, phase: nextPhase, eventType: "phase_started" }),
    });
  }

  async function submitGame(events: MMSEEvent[]) {
    if (submittedRef.current) return;
    submittedRef.current = true;
    setSubmissionStatus("submitting");
    try {
      await completeMMSEGame(assessmentId, { events });
      setSubmissionStatus("success");
    } catch (error) {
      submittedRef.current = false;
      setSubmissionStatus("error");
      setSubmissionError(error instanceof ApiError ? String(error.detail ?? error.message) : "Something went wrong.");
    }
  }

  useEffect(() => {
    if (submissionStatus === "success") {
      const timer = window.setTimeout(() => onComplete?.(), 1200);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [onComplete, submissionStatus]);

  if (state.phase === "INTRO") {
    return <MMSEIntro onStart={startGame} />;
  }

  if (state.phase === "ORIENTATION") {
    return (
      <OrientationPhase
        assessmentId={assessmentId}
        onEvent={appendEvent}
        onComplete={() => advance("ORIENTATION")}
      />
    );
  }

  if (state.phase === "REGISTRATION") {
    return (
      <RegistrationPhase
        assessmentId={assessmentId}
        onEvent={appendEvent}
        onComplete={() => advance("REGISTRATION")}
      />
    );
  }

  if (state.phase === "ATTENTION") {
    return (
      <AttentionPhase
        assessmentId={assessmentId}
        onEvent={appendEvent}
        onComplete={() => advance("ATTENTION")}
      />
    );
  }

  if (state.phase === "LANGUAGE") {
    return (
      <LanguagePhase
        assessmentId={assessmentId}
        onEvent={appendEvent}
        onComplete={() => advance("LANGUAGE")}
      />
    );
  }

  if (state.phase === "DELAYED_RECALL") {
    return (
      <DelayedRecallPhase
        assessmentId={assessmentId}
        onEvent={appendEvent}
        onComplete={() => advance("DELAYED_RECALL")}
      />
    );
  }

  if (state.phase === "COMMAND") {
    return (
      <CommandPhase
        assessmentId={assessmentId}
        onEvent={appendEvent}
        onComplete={(sequence) => {
          const commandCompletedEvent = createMMSEEvent({
            assessmentId,
            phase: "COMMAND",
            eventType: "item_completed",
            questionId: "command_sequence",
            value: sequence.join(","),
            metadata: {
              expected_sequence: ["step_1", "step_2", "step_3"],
              actual_sequence: sequence,
            },
          });
          const phaseCompletedEvent = createMMSEEvent({
            assessmentId,
            phase: "COMMAND",
            eventType: "phase_completed",
          });
          dispatch({
            type: "APPEND_EVENT",
            event: commandCompletedEvent,
          });
          dispatch({ type: "APPEND_EVENT", event: phaseCompletedEvent });
          const completionEvent = createMMSEEvent({
            assessmentId,
            phase: "COMPLETION",
            eventType: "game_completed",
          });
          dispatch({ type: "COMPLETE", event: completionEvent });
          void submitGame([...state.events, commandCompletedEvent, phaseCompletedEvent, completionEvent]);
        }}
      />
    );
  }

  return (
    <MMSECompletion
      status={submissionStatus}
      error={submissionError}
      onRetry={() => void submitGame(state.events)}
    />
  );
}
