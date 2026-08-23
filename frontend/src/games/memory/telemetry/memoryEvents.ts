import type { MemoryPhase } from "../types/memoryTypes";
import type { MemoryEvent, MemoryEventType } from "./eventTypes";

/**
 * The telemetry system is deliberately independent of any UI component.
 * Components call `createMemoryEvent(...)` and append the result to the
 * game state's `events` array — they never format or interpret events
 * themselves.
 */
let counter = 0;

function nextEventId(): string {
  counter += 1;
  // Good enough uniqueness for client-side telemetry; the backend does not
  // rely on this format, only on uniqueness within a submission.
  return `evt_${Date.now()}_${counter}`;
}

export function createMemoryEvent(params: {
  assessmentId: string;
  phase: MemoryPhase;
  eventType: MemoryEventType;
  itemId?: string | null;
  trialId?: string | null;
  value?: string | null;
  metadata?: Record<string, unknown>;
}): MemoryEvent {
  return {
    event_id: nextEventId(),
    assessment_id: params.assessmentId,
    game: "memory",
    phase: params.phase,
    event_type: params.eventType,
    timestamp: new Date().toISOString(),
    item_id: params.itemId ?? null,
    trial_id: params.trialId ?? null,
    value: params.value ?? null,
    metadata: params.metadata ?? {},
  };
}
