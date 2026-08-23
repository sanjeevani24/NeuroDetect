import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";

import "./NBackGame.css";

import { CompletionState, ErrorState, LoadingState } from "../../components/ui/States";
import { completeNBackGame, ApiError, type NBackGameResult } from "../../services/api";
import { PRACTICE_TRIALS, TOTAL_SCORED_TRIALS, WARMUP_TRIALS } from "./config/nbackConfig";
import { NBackCompletion } from "./components/NBackCompletion";
import { NBackIntro } from "./components/NBackIntro";
import { NBackPractice } from "./components/NBackPractice";
import { NBackProgress } from "./components/NBackProgress";
import { NBackReady } from "./components/NBackReady";
import { NBackTrial } from "./components/NBackTrial";
import { createInitialState, nbackReducer } from "./state/nbackState";
import { NBackEventType } from "./telemetry/eventTypes";
import { NBackTelemetryCollector } from "./telemetry/nbackEvents";
import type { TrialResponse, TrialSpec } from "./types/nbackTypes";
import { generatePracticeSequence, generateTrialSequence } from "./utils/trialGenerator";
import { monotonicNowMs } from "./utils/timing";

interface NBackGameProps {
  assessmentId: string;
  onComplete?: () => void;
}

type SubmissionStatus = "idle" | "submitting" | "success" | "error";

export function NBackGame({ assessmentId, onComplete }: NBackGameProps) {
  const [state, dispatch] = useReducer(nbackReducer, assessmentId, createInitialState);
  const telemetryRef = useRef(new NBackTelemetryCollector(assessmentId));
  const [scoredIndex, setScoredIndex] = useState(0);
  const [submissionStatus, setSubmissionStatus] = useState<SubmissionStatus>("idle");
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [result, setResult] = useState<NBackGameResult | null>(null);
  const submittedRef = useRef(false);

  const scoredTrials = useMemo<TrialSpec[]>(
    () => generateTrialSequence({ totalScoredTrials: TOTAL_SCORED_TRIALS, warmupTrials: WARMUP_TRIALS }),
    []
  );
  const practiceTrials = useMemo<TrialSpec[]>(
    () => generatePracticeSequence(PRACTICE_TRIALS),
    []
  );

  const telemetry = telemetryRef.current;

  const handleBegin = useCallback(() => {
    const ts = monotonicNowMs();
    dispatch({ type: "START_GAME", timestampMs: ts });
    telemetry.record(NBackEventType.GAME_STARTED, "INTRO", { monotonicTimestampMs: ts });
    telemetry.record(NBackEventType.PRACTICE_STARTED, "PRACTICE", { monotonicTimestampMs: ts });
    dispatch({ type: "START_PRACTICE", trials: practiceTrials });
  }, [practiceTrials, telemetry]);

  const handlePracticeTrialPresented = useCallback(
    (trial: TrialSpec, ts: number) => {
      telemetry.record(NBackEventType.PRACTICE_TRIAL_STARTED, "PRACTICE", {
        trialId: trial.trialId,
        monotonicTimestampMs: ts,
        metadata: {
          trial_index: trial.trialIndex,
          stimulus: trial.stimulus,
          is_target: trial.isTarget,
          is_warmup: trial.isWarmup,
        },
      });
    },
    [telemetry]
  );

  const handlePracticeResponse = useCallback(
    (trial: TrialSpec, response: TrialResponse, ts: number) => {
      telemetry.record(NBackEventType.PRACTICE_RESPONSE, "PRACTICE", {
        trialId: trial.trialId,
        value: response,
        monotonicTimestampMs: ts,
      });
    },
    [telemetry]
  );

  const handlePracticeTimeout = useCallback(
    (trial: TrialSpec, ts: number) => {
      telemetry.record(NBackEventType.RESPONSE_TIMEOUT, "PRACTICE", {
        trialId: trial.trialId,
        monotonicTimestampMs: ts,
      });
    },
    [telemetry]
  );

  const handlePracticeComplete = useCallback(() => {
    const ts = monotonicNowMs();
    telemetry.record(NBackEventType.PRACTICE_COMPLETED, "PRACTICE", { monotonicTimestampMs: ts });
    dispatch({ type: "COMPLETE_PRACTICE" });
    dispatch({ type: "READY_ASSESSMENT", trials: scoredTrials });
  }, [scoredTrials, telemetry]);

  const handleStartAssessment = useCallback(() => {
    const ts = monotonicNowMs();
    telemetry.record(NBackEventType.ASSESSMENT_STARTED, "RUNNING", { monotonicTimestampMs: ts });
    dispatch({ type: "START_ASSESSMENT", timestampMs: ts });
    setScoredIndex(0);
  }, [telemetry]);

  const submitResults = useCallback(async () => {
    if (submittedRef.current) return;
    submittedRef.current = true;
    setSubmissionStatus("submitting");
    setSubmissionError(null);

    try {
      const response = await completeNBackGame(assessmentId, { events: telemetry.getEvents() });
      setResult(response);
      setSubmissionStatus("success");
    } catch (error) {
      submittedRef.current = false;
      setSubmissionStatus("error");
      setSubmissionError(error instanceof ApiError ? String(error.detail ?? error.message) : "Unable to save your N-Back results.");
    }
  }, [assessmentId, telemetry]);

  const handleScoredTrialPresented = useCallback(
    (trial: TrialSpec, ts: number) => {
      telemetry.record(NBackEventType.TRIAL_STARTED, "RUNNING", {
        trialId: trial.trialId,
        monotonicTimestampMs: ts,
      });
      telemetry.record(NBackEventType.STIMULUS_PRESENTED, "RUNNING", {
        trialId: trial.trialId,
        monotonicTimestampMs: ts,
        metadata: {
          trial_index: trial.trialIndex,
          stimulus: trial.stimulus,
          is_target: trial.isTarget,
          is_warmup: trial.isWarmup,
        },
      });
      dispatch({ type: "PRESENT_TRIAL", trialIndex: scoredIndex, timestampMs: ts });
    },
    [scoredIndex, telemetry]
  );

  const handleScoredResponse = useCallback(
    (trial: TrialSpec, response: TrialResponse, ts: number) => {
      telemetry.record(NBackEventType.RESPONSE_SUBMITTED, "RUNNING", {
        trialId: trial.trialId,
        value: response,
        monotonicTimestampMs: ts,
      });
      dispatch({ type: "SUBMIT_RESPONSE", trialId: trial.trialId, response, timestampMs: ts });
    },
    [telemetry]
  );

  const handleScoredTimeout = useCallback(
    (trial: TrialSpec, ts: number) => {
      telemetry.record(NBackEventType.RESPONSE_TIMEOUT, "RUNNING", {
        trialId: trial.trialId,
        monotonicTimestampMs: ts,
      });
      dispatch({ type: "TIMEOUT_TRIAL", trialId: trial.trialId, timestampMs: ts });
    },
    [telemetry]
  );

  const handleScoredTrialComplete = useCallback(
    (trial: TrialSpec) => {
      const ts = monotonicNowMs();
      dispatch({ type: "COMPLETE_TRIAL", trialId: trial.trialId });
      telemetry.record(NBackEventType.TRIAL_COMPLETED, "RUNNING", {
        trialId: trial.trialId,
        monotonicTimestampMs: ts,
      });

      if (scoredIndex + 1 >= scoredTrials.length) {
        telemetry.record(NBackEventType.PHASE_COMPLETED, "RUNNING", {
          monotonicTimestampMs: ts,
          metadata: { phase: "running" },
        });
        telemetry.record(NBackEventType.GAME_COMPLETED, "COMPLETION", { monotonicTimestampMs: ts });
        dispatch({ type: "COMPLETE_GAME", timestampMs: ts });
        void submitResults();
      } else {
        setScoredIndex((currentIndex) => currentIndex + 1);
        dispatch({ type: "ADVANCE_TRIAL" });
      }
    },
    [scoredIndex, scoredTrials.length, submitResults, telemetry]
  );

  useEffect(() => {
    if (submissionStatus !== "success") return;
    const timer = window.setTimeout(() => onComplete?.(), 1200);
    return () => window.clearTimeout(timer);
  }, [onComplete, submissionStatus]);

  if (state.phase === "INTRO") {
    return <NBackIntro onBegin={handleBegin} />;
  }

  if (state.phase === "PRACTICE") {
    return (
      <NBackPractice
        trials={practiceTrials}
        onTrialPresented={handlePracticeTrialPresented}
        onTrialResponse={handlePracticeResponse}
        onTrialTimeout={handlePracticeTimeout}
        onPracticeComplete={handlePracticeComplete}
      />
    );
  }

  if (state.phase === "READY") {
    return <NBackReady onStart={handleStartAssessment} />;
  }

  if (state.phase === "RUNNING") {
    const current = scoredTrials[scoredIndex];
    if (!current) {
      return (
        <NBackCompletion>
          <LoadingState title="Preparing N-Back" message="Setting up the assessment trials." />
        </NBackCompletion>
      );
    }

    return (
      <NBackCompletion progress={<NBackProgress currentTrial={scoredIndex} totalTrials={scoredTrials.length} />}>
        <NBackTrial
          key={current.trialId}
          trial={current}
          showFeedback={false}
          onPresented={(ts) => handleScoredTrialPresented(current, ts)}
          onResponse={(response, ts) => handleScoredResponse(current, response, ts)}
          onTimeout={(ts) => handleScoredTimeout(current, ts)}
          onTrialComplete={() => handleScoredTrialComplete(current)}
        />
      </NBackCompletion>
    );
  }

  return (
    <NBackCompletion>
      {submissionStatus === "submitting" || submissionStatus === "idle" ? (
        <LoadingState title="Saving N-Back results" message="Your responses are being processed." />
      ) : null}
      {submissionStatus === "success" && result ? (
        <CompletionState
          title="N-Back complete"
          message="Thank you. Your responses have been recorded for this stage."
        />
      ) : null}
      {submissionStatus === "error" ? (
        <ErrorState
          title="Unable to save your N-Back results"
          message={submissionError ?? "Please try again."}
          action={
            <button className="button button--primary" type="button" onClick={() => void submitResults()}>
              Try Again
            </button>
          }
        />
      ) : null}
    </NBackCompletion>
  );
}

export default NBackGame;
