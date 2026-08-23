import type { NBackPhase } from "../types/nbackTypes";
import { monotonicNowMs, monotonicToISOString } from "../utils/timing";
import { NBackEventType, type NBackEventTypeValue } from "./eventTypes";

export interface NBackTelemetryEvent {
  event_id: string;
  assessment_id: string;
  game: "nback";
  phase: Lowercase<NBackPhase>;
  event_type: NBackEventTypeValue;
  timestamp: string; // ISO 8601
  trial_id: string | null;
  value: unknown;
  metadata: Record<string, unknown>;
}

/**
 * Collects telemetry events for a single N-Back session. Kept as a plain
 * class (not React state) so appends are cheap and don't trigger re-renders;
 * the events array is only read when the game completes and is POSTed.
 *
 * Mirrors the Memory Recall telemetry collector pattern.
 */
export class NBackTelemetryCollector {
  private events: NBackTelemetryEvent[] = [];
  private assessmentId: string;

  constructor(assessmentId: string) {
    this.assessmentId = assessmentId;
  }

  record(
    eventType: NBackEventTypeValue,
    phase: NBackPhase,
    opts: {
      trialId?: string | null;
      value?: unknown;
      metadata?: Record<string, unknown>;
      /** performance.now()-based monotonic timestamp; defaults to "now". */
      monotonicTimestampMs?: number;
    } = {}
  ): void {
    this.events.push({
      event_id: crypto.randomUUID(),
      assessment_id: this.assessmentId,
      game: "nback",
      phase: phase.toLowerCase() as Lowercase<NBackPhase>,
      event_type: eventType,
      timestamp: monotonicToISOString(opts.monotonicTimestampMs ?? monotonicNowMs()),
      trial_id: opts.trialId ?? null,
      value: opts.value ?? null,
      metadata: opts.metadata ?? {},
    });
  }

  getEvents(): NBackTelemetryEvent[] {
    return [...this.events];
  }

  reset(): void {
    this.events = [];
  }
}

export { NBackEventType };
