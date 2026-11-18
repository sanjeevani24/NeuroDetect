import type {
  TrailMakingErrorType,
  TrailMakingEventType,
  TrailMakingPhase,
  TrailMakingTelemetryEvent,
  TrailNodeLayout,
} from "../types/trailMakingTypes";
import { monotonicNowMs, monotonicToISOString } from "../utils/timing";

export class TrailMakingTelemetryCollector {
  private assessmentId: string;
  private sessionId: string;
  private startTimeMs: number | null = null;
  private events: TrailMakingTelemetryEvent[] = [];

  constructor(assessmentId: string, sessionId: string) {
    this.assessmentId = assessmentId;
    this.sessionId = sessionId;
  }

  markStarted(timestampMs: number): void {
    this.startTimeMs = timestampMs;
  }

  record(
    eventType: TrailMakingEventType,
    phase: TrailMakingPhase,
    options: {
      timestampMs?: number;
      node?: TrailNodeLayout | null;
      expectedSequenceIndex?: number | null;
      pointerX?: number | null;
      pointerY?: number | null;
      wasCorrect?: boolean | null;
      errorType?: TrailMakingErrorType | null;
      eventPayload?: Record<string, unknown>;
    } = {}
  ): void {
    const timestampMs = options.timestampMs ?? monotonicNowMs();
    const relativeTimeMs = this.startTimeMs === null ? 0 : Math.max(0, timestampMs - this.startTimeMs);
    this.events.push({
      event_id: crypto.randomUUID(),
      assessment_id: this.assessmentId,
      game_session_id: this.sessionId,
      game: "trail_making",
      phase: phase.toLowerCase() as Lowercase<TrailMakingPhase>,
      event_type: eventType,
      timestamp: monotonicToISOString(timestampMs),
      relative_time_ms: relativeTimeMs,
      node_id: options.node?.node_id ?? null,
      node_label: options.node?.label ?? null,
      node_type: options.node?.node_type ?? null,
      sequence_index: options.node?.sequence_index ?? null,
      expected_sequence_index: options.expectedSequenceIndex ?? null,
      x: options.node?.x ?? null,
      y: options.node?.y ?? null,
      pointer_x: options.pointerX ?? null,
      pointer_y: options.pointerY ?? null,
      was_correct: options.wasCorrect ?? null,
      error_type: options.errorType ?? null,
      event_payload: options.eventPayload ?? {},
    });
  }

  getEvents(): TrailMakingTelemetryEvent[] {
    return [...this.events];
  }
}
