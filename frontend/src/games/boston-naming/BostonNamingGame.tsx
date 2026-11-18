import { useEffect, useRef, useState } from "react";

import "./BostonNamingGame.css";

import { CompletionState, ErrorState, LoadingState } from "../../components/ui/States";
import { completeBostonNamingGame, ApiError, type BostonNamingGameResult } from "../../services/api";
import {
  PRACTICE_STIMULI,
  SCORED_STIMULI,
  TOTAL_SCORED_TRIALS,
} from "./config/bostonNamingConfig";
import { BostonNamingCompletion } from "./components/BostonNamingCompletion";
import { BostonNamingIntro } from "./components/BostonNamingIntro";
import { BostonNamingProgress } from "./components/BostonNamingProgress";
import { BostonNamingReady } from "./components/BostonNamingReady";
import { BostonNamingTrial } from "./components/BostonNamingTrial";
import { createInitialState } from "./state/bostonNamingState";
import { BostonNamingTelemetryCollector } from "./telemetry/bostonNamingEvents";
import { BostonNamingEventType } from "./telemetry/eventTypes";
import type { BostonNamingPhase, TrialCapture } from "./types/bostonNamingTypes";
import { monotonicNowMs } from "./utils/timing";

interface BostonNamingGameProps {
  assessmentId: string;
  onComplete?: () => void;
}

type SubmissionStatus = "idle" | "submitting" | "success" | "error";
type PermissionState = "idle" | "requesting" | "granted" | "denied" | "unsupported";

function createTrialId(prefix: "practice" | "scored", index: number) {
  return `${prefix}-trial-${index + 1}`;
}

export function BostonNamingGame({ assessmentId, onComplete }: BostonNamingGameProps) {
  const [phase, setPhase] = useState<BostonNamingPhase>(createInitialState().phase);
  const telemetryRef = useRef(new BostonNamingTelemetryCollector(assessmentId));
  const streamRef = useRef<MediaStream | null>(null);
  const presentedTrialsRef = useRef(new Set<string>());
  const completedTrialsRef = useRef(new Set<string>());
  const timeoutTrialsRef = useRef(new Set<string>());
  const emittedCuesRef = useRef(new Set<string>());
  const [permissionState, setPermissionState] = useState<PermissionState>("idle");
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const [practiceIndex, setPracticeIndex] = useState(0);
  const [scoredIndex, setScoredIndex] = useState(0);
  const [submissionStatus, setSubmissionStatus] = useState<SubmissionStatus>("idle");
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [result, setResult] = useState<BostonNamingGameResult | null>(null);

  const telemetry = telemetryRef.current;

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  async function requestMicrophonePermission() {
    if (!navigator.mediaDevices?.getUserMedia) {
      setPermissionState("unsupported");
      setPermissionError("This browser does not support microphone capture for the Boston Naming stage.");
      return;
    }

    setPermissionState("requesting");
    setPermissionError(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = stream;
      setPermissionState("granted");
    } catch (error) {
      setPermissionState("denied");
      setPermissionError("Microphone permission was denied. Please allow access and try again.");
    }
  }

  async function handleBeginIntro() {
    if (permissionState !== "granted") {
      await requestMicrophonePermission();
      if (!streamRef.current) {
        return;
      }
    }
    const ts = monotonicNowMs();
    telemetry.record(BostonNamingEventType.GAME_STARTED, "INTRO", { monotonicTimestampMs: ts });
    telemetry.record(BostonNamingEventType.PRACTICE_STARTED, "PRACTICE", { monotonicTimestampMs: ts });
    setPhase("PRACTICE");
  }

  function handlePracticePresented(trialId: string, stimulusId: string, trialIndex: number, ts: number) {
    if (presentedTrialsRef.current.has(trialId)) {
      return;
    }
    presentedTrialsRef.current.add(trialId);
    telemetry.record(BostonNamingEventType.PRACTICE_TRIAL_STARTED, "PRACTICE", {
      trialId,
      monotonicTimestampMs: ts,
      metadata: { trial_index: trialIndex + 1, stimulus_id: stimulusId },
    });
    telemetry.record(BostonNamingEventType.STIMULUS_PRESENTED, "PRACTICE", {
      trialId,
      monotonicTimestampMs: ts,
      metadata: { trial_index: trialIndex + 1, stimulus_id: stimulusId },
    });
  }

  function handleScoredPresented(trialId: string, stimulusId: string, trialIndex: number, difficulty: string, ts: number) {
    if (presentedTrialsRef.current.has(trialId)) {
      return;
    }
    presentedTrialsRef.current.add(trialId);
    telemetry.record(BostonNamingEventType.TRIAL_STARTED, "RUNNING", {
      trialId,
      monotonicTimestampMs: ts,
    });
    telemetry.record(BostonNamingEventType.STIMULUS_PRESENTED, "RUNNING", {
      trialId,
      monotonicTimestampMs: ts,
      metadata: { trial_index: trialIndex + 1, stimulus_id: stimulusId, difficulty },
    });
  }

  function recordCapture(phaseName: "PRACTICE" | "RUNNING", trialId: string, capture: TrialCapture, timestampMs: number) {
    telemetry.record(BostonNamingEventType.RESPONSE_RECORDING_STARTED, phaseName, {
      trialId,
      monotonicTimestampMs: timestampMs - (capture.responseDurationMs ?? 0),
      metadata: {
        response_latency_ms: capture.responseLatencyMs,
        hesitation_duration_ms: capture.hesitationDurationMs,
      },
    });
    telemetry.record(BostonNamingEventType.RESPONSE_RECORDING_STOPPED, phaseName, {
      trialId,
      monotonicTimestampMs: timestampMs,
      metadata: {
        response_duration_ms: capture.responseDurationMs,
        recording_status: capture.recordingStatus,
        response_latency_ms: capture.responseLatencyMs,
        hesitation_duration_ms: capture.hesitationDurationMs,
      },
    });
    telemetry.record(BostonNamingEventType.TRANSCRIPTION_COMPLETED, phaseName, {
      trialId,
      monotonicTimestampMs: timestampMs,
      value: capture.transcript,
      metadata: {
        transcript: capture.transcript,
        initial_response: capture.initialResponse,
        final_response: capture.finalResponse,
        transcript_confidence: capture.transcriptConfidence,
        transcription_status: capture.transcriptionStatus,
      },
    });
    if (capture.selfCorrected) {
      telemetry.record(BostonNamingEventType.SELF_CORRECTION_DETECTED, phaseName, {
        trialId,
        monotonicTimestampMs: timestampMs,
        metadata: {
          initial_response: capture.initialResponse,
          final_response: capture.finalResponse,
          self_correction_latency_ms: capture.selfCorrectionLatencyMs,
        },
      });
    }
  }

  function handlePracticeCapture(capture: TrialCapture, timestampMs: number) {
    const trialId = createTrialId("practice", practiceIndex);
    if (completedTrialsRef.current.has(trialId)) {
      return;
    }
    completedTrialsRef.current.add(trialId);
    recordCapture("PRACTICE", trialId, capture, timestampMs);
    telemetry.record(BostonNamingEventType.PRACTICE_RESPONSE, "PRACTICE", {
      trialId,
      monotonicTimestampMs: timestampMs,
      metadata: {
        transcript: capture.transcript,
        timeout: capture.timeout,
        semantic_cue_used: capture.semanticCueUsed,
        phonemic_cue_used: capture.phonemicCueUsed,
      },
    });
    telemetry.record(BostonNamingEventType.TRIAL_COMPLETED, "PRACTICE", {
      trialId,
      monotonicTimestampMs: timestampMs,
    });

    if (practiceIndex + 1 >= PRACTICE_STIMULI.length) {
      telemetry.record(BostonNamingEventType.PRACTICE_COMPLETED, "PRACTICE", { monotonicTimestampMs: timestampMs });
      setPhase("READY");
    } else {
      setPracticeIndex((current) => current + 1);
    }
  }

  function handleScoredCapture(capture: TrialCapture, timestampMs: number) {
    const trialId = createTrialId("scored", scoredIndex);
    if (completedTrialsRef.current.has(trialId)) {
      return;
    }
    completedTrialsRef.current.add(trialId);
    recordCapture("RUNNING", trialId, capture, timestampMs);
    telemetry.record(BostonNamingEventType.RESPONSE_CLASSIFIED, "RUNNING", {
      trialId,
      monotonicTimestampMs: timestampMs,
      metadata: {
        transcript: capture.transcript,
        timeout: capture.timeout,
        semantic_cue_used: capture.semanticCueUsed,
        phonemic_cue_used: capture.phonemicCueUsed,
      },
    });
    telemetry.record(BostonNamingEventType.TRIAL_COMPLETED, "RUNNING", {
      trialId,
      monotonicTimestampMs: timestampMs,
    });

    if (scoredIndex + 1 >= TOTAL_SCORED_TRIALS) {
      telemetry.record(BostonNamingEventType.GAME_COMPLETED, "COMPLETION", { monotonicTimestampMs: timestampMs });
      setPhase("COMPLETION");
      void submitResults();
    } else {
      setScoredIndex((current) => current + 1);
    }
  }

  function handleCuePresented(phaseName: "PRACTICE" | "RUNNING", trialId: string, cueType: "semantic" | "phonemic", ts: number) {
    const cueKey = `${trialId}:${cueType}`;
    if (emittedCuesRef.current.has(cueKey)) {
      return;
    }
    emittedCuesRef.current.add(cueKey);
    telemetry.record(BostonNamingEventType.CUE_PRESENTED, phaseName, {
      trialId,
      monotonicTimestampMs: ts,
      metadata: { cue_type: cueType },
    });
  }

  function handleTimeout(phaseName: "PRACTICE" | "RUNNING", trialId: string, ts: number) {
    if (timeoutTrialsRef.current.has(trialId)) {
      return;
    }
    timeoutTrialsRef.current.add(trialId);
    telemetry.record(BostonNamingEventType.RESPONSE_TIMEOUT, phaseName, {
      trialId,
      monotonicTimestampMs: ts,
    });
  }

  function handleStartScoredAssessment() {
    const ts = monotonicNowMs();
    telemetry.record(BostonNamingEventType.ASSESSMENT_STARTED, "RUNNING", { monotonicTimestampMs: ts });
    setPhase("RUNNING");
  }

  async function submitResults() {
    setSubmissionStatus("submitting");
    setSubmissionError(null);
    const ts = monotonicNowMs();
    telemetry.record(BostonNamingEventType.GAME_SUBMISSION_STARTED, "COMPLETION", { monotonicTimestampMs: ts });
    try {
      const response = await completeBostonNamingGame(assessmentId, { events: telemetry.getEvents() });
      setResult(response);
      setSubmissionStatus("success");
      telemetry.record(BostonNamingEventType.GAME_SUBMISSION_SUCCEEDED, "COMPLETION", { monotonicTimestampMs: monotonicNowMs() });
    } catch (error) {
      setSubmissionStatus("error");
      setSubmissionError(
        error instanceof ApiError
          ? String(error.detail ?? error.message)
          : "Unable to save your Boston Naming results."
      );
      telemetry.record(BostonNamingEventType.GAME_SUBMISSION_FAILED, "COMPLETION", {
        monotonicTimestampMs: monotonicNowMs(),
        metadata: { detail: error instanceof ApiError ? error.detail : String(error) },
      });
    }
  }

  useEffect(() => {
    if (submissionStatus !== "success") return;
    const timer = window.setTimeout(() => onComplete?.(), 1200);
    return () => window.clearTimeout(timer);
  }, [onComplete, submissionStatus]);

  if (phase === "INTRO") {
    return <BostonNamingIntro onContinue={handleBeginIntro} />;
  }

  if (phase === "PRACTICE") {
    const stimulus = PRACTICE_STIMULI[practiceIndex];
    const trialId = createTrialId("practice", practiceIndex);
    if (!streamRef.current) {
      return (
        <BostonNamingCompletion>
          <LoadingState title="Preparing microphone access" message="Enable the microphone on the next step to continue with practice." />
        </BostonNamingCompletion>
      );
    }
    return (
      <BostonNamingCompletion progress={<BostonNamingProgress currentTrial={practiceIndex} totalTrials={PRACTICE_STIMULI.length} />}>
        <BostonNamingTrial
          key={trialId}
          stimulus={stimulus}
          isPractice
          stream={streamRef.current}
          onPresented={(ts) => handlePracticePresented(trialId, stimulus.stimulusId, practiceIndex, ts)}
          onCuePresented={(cueType, ts) => handleCuePresented("PRACTICE", trialId, cueType, ts)}
          onTimeout={(ts) => handleTimeout("PRACTICE", trialId, ts)}
          onCaptureComplete={handlePracticeCapture}
        />
      </BostonNamingCompletion>
    );
  }

  if (phase === "READY") {
    return (
      <BostonNamingReady
        permissionState={permissionState}
        permissionError={permissionError}
        onRequestPermission={() => void requestMicrophonePermission()}
        onStart={handleStartScoredAssessment}
      />
    );
  }

  if (phase === "RUNNING") {
    const stimulus = SCORED_STIMULI[scoredIndex];
    const trialId = createTrialId("scored", scoredIndex);
    if (!streamRef.current) {
      return (
        <ErrorState
          title="Microphone unavailable"
          message="Boston Naming requires microphone access before the scored trials can begin."
          action={
            <button className="button button--primary" type="button" onClick={() => void requestMicrophonePermission()}>
              Enable microphone
            </button>
          }
        />
      );
    }
    return (
      <BostonNamingCompletion progress={<BostonNamingProgress currentTrial={scoredIndex} totalTrials={SCORED_STIMULI.length} />}>
        <BostonNamingTrial
          key={trialId}
          stimulus={stimulus}
          isPractice={false}
          stream={streamRef.current}
          onPresented={(ts) => handleScoredPresented(trialId, stimulus.stimulusId, scoredIndex, stimulus.difficulty, ts)}
          onCuePresented={(cueType, ts) => handleCuePresented("RUNNING", trialId, cueType, ts)}
          onTimeout={(ts) => handleTimeout("RUNNING", trialId, ts)}
          onCaptureComplete={handleScoredCapture}
        />
      </BostonNamingCompletion>
    );
  }

  return (
    <BostonNamingCompletion>
      {submissionStatus === "submitting" || submissionStatus === "idle" ? (
        <LoadingState title="Saving Boston Naming results" message="Your responses are being processed." />
      ) : null}
      {submissionStatus === "success" && result ? (
        <CompletionState
          title="Boston Naming complete"
          message="Your naming responses have been saved. The assessment can now continue to Trail Making."
        />
      ) : null}
      {submissionStatus === "error" ? (
        <ErrorState
          title="Unable to save your Boston Naming results"
          message={submissionError ?? "Please try again."}
          action={
            <button className="button button--primary" type="button" onClick={() => void submitResults()}>
              Try Again
            </button>
          }
        />
      ) : null}
    </BostonNamingCompletion>
  );
}
