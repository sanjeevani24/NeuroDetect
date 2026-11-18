import { useEffect, useRef, useState } from "react";

import { RESPONSE_WINDOW_MS, STIMULUS_DURATION_MS } from "../config/nbackConfig";
import type { TrialResponse, TrialSpec } from "../types/nbackTypes";
import { latencyMs, monotonicNowMs } from "../utils/timing";

interface Props {
  trial: TrialSpec;
  /** Practice trials show immediate neutral feedback; scored trials do not (spec section 13). */
  showFeedback: boolean;
  onPresented: (timestampMs: number) => void;
  onResponse: (response: TrialResponse, timestampMs: number) => void;
  onTimeout: (timestampMs: number) => void;
  onTrialComplete: () => void;
}

type LocalPhase = "showing" | "awaiting_response" | "feedback" | "done";

export function NBackTrial({
  trial,
  showFeedback,
  onPresented,
  onResponse,
  onTimeout,
  onTrialComplete,
}: Props) {
  const [localPhase, setLocalPhase] = useState<LocalPhase>("showing");
  const [feedbackText, setFeedbackText] = useState<string | null>(null);
  const [stimulusVisible, setStimulusVisible] = useState(true);
  const respondedRef = useRef(false); // guards against duplicate responses within one trial
  const presentedAtRef = useRef<number | null>(null);
  const timeoutHandleRef = useRef<number | null>(null);
  const stimulusHideHandleRef = useRef<number | null>(null);

  useEffect(() => {
    // Reset all per-trial guards when the trial identity changes.
    respondedRef.current = false;
    presentedAtRef.current = null;
    setLocalPhase("showing");
    setFeedbackText(null);
    setStimulusVisible(true);

    const presentedAt = monotonicNowMs();
    presentedAtRef.current = presentedAt;
    onPresented(presentedAt);

    setLocalPhase("awaiting_response");

    stimulusHideHandleRef.current = window.setTimeout(() => {
      setStimulusVisible(false);
    }, STIMULUS_DURATION_MS);

    timeoutHandleRef.current = window.setTimeout(() => {
      if (respondedRef.current) return; // already answered — no timeout
      respondedRef.current = true;
      const now = monotonicNowMs();
      onTimeout(now);
      if (showFeedback) {
        setFeedbackText("Try to respond faster");
        setLocalPhase("feedback");
        window.setTimeout(() => {
          setLocalPhase("done");
          onTrialComplete();
        }, 600);
      } else {
        setLocalPhase("done");
        onTrialComplete();
      }
    }, RESPONSE_WINDOW_MS);

    return () => {
      if (stimulusHideHandleRef.current !== null) {
        window.clearTimeout(stimulusHideHandleRef.current);
      }
      if (timeoutHandleRef.current !== null) {
        window.clearTimeout(timeoutHandleRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trial.trialId]);

  function handleRespond(response: TrialResponse) {
    if (respondedRef.current) return; // duplicate-response guard
    if (localPhase !== "awaiting_response") return;
    if (presentedAtRef.current === null) return;

    respondedRef.current = true;
    if (timeoutHandleRef.current !== null) {
      window.clearTimeout(timeoutHandleRef.current);
    }

    const now = monotonicNowMs();
    const withinWindow = latencyMs(presentedAtRef.current, now) <= RESPONSE_WINDOW_MS;

    if (!withinWindow) {
      // Should be rare (setTimeout already guards this), but treat a
      // late-arriving response as a timeout, never a silent normal response.
      onTimeout(now);
    } else {
      onResponse(response, now);
    }

    if (showFeedback) {
      const isCorrect =
        trial.isTarget !== null &&
        ((trial.isTarget && response === "MATCH") || (!trial.isTarget && response === "NO_MATCH"));
      setFeedbackText(isCorrect ? "Correct" : "Not quite");
      setLocalPhase("feedback");
      window.setTimeout(() => {
        setLocalPhase("done");
        onTrialComplete();
      }, 600);
    } else {
      setLocalPhase("done");
      onTrialComplete();
    }
  }

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.repeat) return;
      const key = event.key.toLowerCase();
      if (key === "m") {
        event.preventDefault();
        handleRespond("MATCH");
      } else if (key === "n") {
        event.preventDefault();
        handleRespond("NO_MATCH");
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  });

  return (
    <div className="nback-trial" data-phase={localPhase}>
      <div className="nback-stimulus-frame" aria-live="polite">
        <div className={`nback-stimulus ${stimulusVisible ? "is-visible" : "is-hidden"}`}>
          {localPhase !== "done" && stimulusVisible ? trial.stimulus : ""}
        </div>
      </div>

      {localPhase === "awaiting_response" && (
        <div className="nback-response-controls">
          <button
            className="nback-response-button nback-response-button--match"
            onClick={() => handleRespond("MATCH")}
            type="button"
          >
            Match
            <span>M</span>
          </button>
          <button
            className="nback-response-button nback-response-button--no-match"
            onClick={() => handleRespond("NO_MATCH")}
            type="button"
          >
            No Match
            <span>N</span>
          </button>
        </div>
      )}

      {localPhase === "feedback" && feedbackText && (
        <div className="nback-feedback">{feedbackText}</div>
      )}
    </div>
  );
}
