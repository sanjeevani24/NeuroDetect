import type { BostonNamingPhase } from "../types/bostonNamingTypes";
import { monotonicNowMs, monotonicToISOString } from "../utils/timing";
import type { BostonNamingEventTypeValue } from "./eventTypes";

export interface BostonNamingTelemetryEvent {
  event_id: string;
  assessment_id: string;
  game: "boston_naming";
  phase: Lowercase<BostonNamingPhase>;
  event_type: BostonNamingEventTypeValue;
  timestamp: string;
  trial_id: string | null;
  value: unknown;
  metadata: Record<string, unknown>;
}

export class BostonNamingTelemetryCollector {
  private events: BostonNamingTelemetryEvent[] = [];
  private assessmentId: string;

  constructor(assessmentId: string) {
    this.assessmentId = assessmentId;
  }

  record(
    eventType: BostonNamingEventTypeValue,
    phase: BostonNamingPhase,
    opts: {
      trialId?: string | null;
      value?: unknown;
      metadata?: Record<string, unknown>;
      monotonicTimestampMs?: number;
    } = {}
  ): void {
    this.events.push({
      event_id: crypto.randomUUID(),
      assessment_id: this.assessmentId,
      game: "boston_naming",
      phase: phase.toLowerCase() as Lowercase<BostonNamingPhase>,
      event_type: eventType,
      timestamp: monotonicToISOString(opts.monotonicTimestampMs ?? monotonicNowMs()),
      trial_id: opts.trialId ?? null,
      value: opts.value ?? null,
      metadata: opts.metadata ?? {},
    });
  }

  getEvents(): BostonNamingTelemetryEvent[] {
    return [...this.events];
  }
}
