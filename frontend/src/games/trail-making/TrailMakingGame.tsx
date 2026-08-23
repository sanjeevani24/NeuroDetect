import { useEffect, useMemo, useRef, useState } from "react";

import "./TrailMakingGame.css";

import { CompletionState, ErrorState, LoadingState } from "../../components/ui/States";
import { completeTrailMakingGame, ApiError, type TrailMakingGameResult } from "../../services/api";
import { TRAIL_HESITATION_THRESHOLD_MS, TRAIL_POINTER_SAMPLE_INTERVAL_MS, TRAIL_SEQUENCE } from "./config/trailConfig";
import { TrailMakingBoard } from "./components/TrailMakingBoard";
import { TrailMakingCompletion } from "./components/TrailMakingCompletion";
import { TrailMakingIntro } from "./components/TrailMakingIntro";
import { TrailMakingProgress } from "./components/TrailMakingProgress";
import { TrailMakingTelemetryCollector } from "./telemetry/trailMakingEvents";
import type { TrailMakingErrorType, TrailNodeLayout } from "./types/trailMakingTypes";
import { generateTrailLayout } from "./utils/layout";
import { monotonicNowMs } from "./utils/timing";

interface TrailMakingGameProps {
  assessmentId: string;
}

type SubmissionStatus = "idle" | "submitting" | "success" | "error";

function classifyError(node: TrailNodeLayout, expectedNode: TrailNodeLayout, completedCount: number): TrailMakingErrorType {
  if (node.sequence_index < completedCount) return "REPEAT_TARGET";
  if (node.node_type !== expectedNode.node_type) return node.node_type === "number" ? "WRONG_NUMBER" : "WRONG_LETTER";
  if (node.sequence_index > expectedNode.sequence_index) return "OUT_OF_ORDER";
  return "WRONG_TARGET";
}

export function TrailMakingGame({ assessmentId }: TrailMakingGameProps) {
  const [phase, setPhase] = useState<"INTRO" | "RUNNING" | "COMPLETION">("INTRO");
  const [completedCount, setCompletedCount] = useState(0);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [submissionStatus, setSubmissionStatus] = useState<SubmissionStatus>("idle");
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [result, setResult] = useState<TrailMakingGameResult | null>(null);

  const sessionIdRef = useRef(crypto.randomUUID());
  const telemetryRef = useRef(new TrailMakingTelemetryCollector(assessmentId, sessionIdRef.current));
  const nodes = useMemo(
    () => generateTrailLayout(TRAIL_SEQUENCE, `${assessmentId}:${sessionIdRef.current}`),
    [assessmentId]
  );
  const startTimeRef = useRef<number | null>(null);
  const lastPointerSampleRef = useRef<number>(0);
  const lastCorrectAtRef = useRef<number | null>(null);
  const lastErrorAtRef = useRef<number | null>(null);
  const submittedRef = useRef(false);

  const expectedNode = nodes[completedCount] ?? null;
  const telemetry = telemetryRef.current;

  useEffect(() => {
    if (phase !== "RUNNING") return;
    const interval = window.setInterval(() => {
      if (startTimeRef.current !== null) {
        setElapsedMs(monotonicNowMs() - startTimeRef.current);
      }
    }, 100);
    return () => window.clearInterval(interval);
  }, [phase]);

  function handleStart() {
    const ts = monotonicNowMs();
    startTimeRef.current = ts;
    telemetry.markStarted(ts);
    telemetry.record("game_started", "INTRO", {
      timestampMs: ts,
      eventPayload: { layout: nodes },
    });
    setPhase("RUNNING");
  }

  function handlePointerMove(event: React.PointerEvent<SVGSVGElement>) {
    if (phase !== "RUNNING" || startTimeRef.current === null) return;
    const now = monotonicNowMs();
    if (now - lastPointerSampleRef.current < TRAIL_POINTER_SAMPLE_INTERVAL_MS) return;
    lastPointerSampleRef.current = now;
    const svg = event.currentTarget;
    const rect = svg.getBoundingClientRect();
    const scaleX = 900 / rect.width;
    const scaleY = 560 / rect.height;
    const x = (event.clientX - rect.left) * scaleX;
    const y = (event.clientY - rect.top) * scaleY;
    telemetry.record("pointer_sample", "RUNNING", {
      timestampMs: now,
      expectedSequenceIndex: completedCount,
      pointerX: x,
      pointerY: y,
      eventPayload: {
        time_since_last_correct_click_ms: lastCorrectAtRef.current === null ? null : now - lastCorrectAtRef.current,
        time_since_previous_error_ms: lastErrorAtRef.current === null ? null : now - lastErrorAtRef.current,
      },
    });
  }

  async function submitResults(finalTimestamp: number) {
    if (submittedRef.current) return;
    submittedRef.current = true;
    setSubmissionStatus("submitting");
    setSubmissionError(null);
    telemetry.record("game_submission_started", "COMPLETION", { timestampMs: finalTimestamp });
    try {
      const response = await completeTrailMakingGame(assessmentId, {
        game_session_id: sessionIdRef.current,
        node_layout: nodes,
        events: telemetry.getEvents(),
      });
      setResult(response);
      setSubmissionStatus("success");
      telemetry.record("game_submission_succeeded", "COMPLETION", { timestampMs: monotonicNowMs() });
    } catch (error) {
      submittedRef.current = false;
      setSubmissionStatus("error");
      setSubmissionError(error instanceof ApiError ? String(error.detail ?? error.message) : "Unable to save your Trail Making results.");
      telemetry.record("game_submission_failed", "COMPLETION", {
        timestampMs: monotonicNowMs(),
        eventPayload: { detail: error instanceof ApiError ? error.detail : String(error) },
      });
    }
  }

  function handleNodeClick(node: TrailNodeLayout, event: React.PointerEvent<SVGCircleElement>) {
    if (phase !== "RUNNING" || expectedNode === null || startTimeRef.current === null) return;
    const svg = event.currentTarget.ownerSVGElement;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const scaleX = 900 / rect.width;
    const scaleY = 560 / rect.height;
    const pointerX = (event.clientX - rect.left) * scaleX;
    const pointerY = (event.clientY - rect.top) * scaleY;
    const timestampMs = monotonicNowMs();
    const isCorrect = node.sequence_index === expectedNode.sequence_index;
    const errorType: TrailMakingErrorType = isCorrect ? "CORRECT" : classifyError(node, expectedNode, completedCount);
    const sinceLastCorrect = lastCorrectAtRef.current === null ? null : timestampMs - lastCorrectAtRef.current;
    const sinceLastError = lastErrorAtRef.current === null ? null : timestampMs - lastErrorAtRef.current;
    telemetry.record("node_clicked", "RUNNING", {
      timestampMs,
      node,
      expectedSequenceIndex: expectedNode.sequence_index,
      pointerX,
      pointerY,
      wasCorrect: isCorrect,
      errorType,
        eventPayload: {
          current_error_count: completedCount === 0 ? 0 : telemetry.getEvents().filter((item) => item.event_type === "node_clicked" && item.was_correct === false).length,
          current_correct_count: completedCount,
          current_sequence_position: completedCount,
          time_since_last_correct_click_ms: sinceLastCorrect,
          time_since_previous_error_ms: sinceLastError,
        },
    });

    if (!isCorrect) {
      lastErrorAtRef.current = timestampMs;
      return;
    }

    const reactionTime = lastCorrectAtRef.current === null ? timestampMs - startTimeRef.current : timestampMs - lastCorrectAtRef.current;
    const hesitationDuration = reactionTime >= TRAIL_HESITATION_THRESHOLD_MS ? reactionTime : 0;
    telemetry.record("target_completed", "RUNNING", {
      timestampMs,
      node,
      expectedSequenceIndex: expectedNode.sequence_index,
      pointerX,
      pointerY,
      wasCorrect: true,
      errorType: "CORRECT",
        eventPayload: {
          reaction_time: reactionTime,
          errors_since_previous_correct_target:
            telemetry.getEvents().filter(
              (item) =>
                item.event_type === "node_clicked" &&
                item.was_correct === false &&
                (lastCorrectAtRef.current === null || item.relative_time_ms > (lastCorrectAtRef.current - (startTimeRef.current ?? 0)))
            ).length,
          hesitation_duration: hesitationDuration,
          pre_click_idle_duration: hesitationDuration,
        },
    });
    lastCorrectAtRef.current = timestampMs;
    const nextCount = completedCount + 1;
    setCompletedCount(nextCount);
    if (nextCount >= nodes.length) {
      telemetry.record("game_completed", "COMPLETION", {
        timestampMs,
        eventPayload: { completion_count: nextCount },
      });
      setElapsedMs(timestampMs - startTimeRef.current);
      setPhase("COMPLETION");
      void submitResults(timestampMs);
    }
  }

  if (phase === "INTRO") {
    return <TrailMakingIntro onStart={handleStart} />;
  }

  if (phase === "RUNNING" && expectedNode) {
    return (
      <section className="trail-card">
        <TrailMakingProgress
          current={completedCount}
          total={nodes.length}
          elapsedMs={elapsedMs}
        />
        <TrailMakingBoard
          nodes={nodes}
          completedCount={completedCount}
          onPointerMove={handlePointerMove}
          onNodeClick={handleNodeClick}
        />
      </section>
    );
  }

  return (
    <TrailMakingCompletion>
      {submissionStatus === "submitting" || submissionStatus === "idle" ? (
        <LoadingState title="Saving Trail Making results" message="Your telemetry is being processed." />
      ) : null}
      {submissionStatus === "success" && result ? (
        <CompletionState
          title="Trail Making completed"
          message={`Time: ${(result.features.total_completion_time / 1000).toFixed(1)} seconds. Errors: ${result.features.total_error_count}.`}
        />
      ) : null}
      {submissionStatus === "error" ? (
        <ErrorState
          title="Unable to save your Trail Making results"
          message={submissionError ?? "Please try again."}
          action={
            <button className="button button--primary" type="button" onClick={() => void submitResults(monotonicNowMs())}>
              Try Again
            </button>
          }
        />
      ) : null}
    </TrailMakingCompletion>
  );
}

export default TrailMakingGame;
