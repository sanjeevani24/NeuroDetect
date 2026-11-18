import type { MMSEPhase } from "../types/mmseTypes";

export type MMSEEventType =
  | "game_started"
  | "phase_started"
  | "question_presented"
  | "response_started"
  | "response_submitted"
  | "response_edited"
  | "item_presented"
  | "item_selected"
  | "item_completed"
  | "phase_completed"
  | "game_completed"
  | "error";

export interface MMSEEvent {
  event_id: string;
  assessment_id: string;
  game: "mmse";
  phase: MMSEPhase;
  event_type: MMSEEventType;
  timestamp: string;
  question_id: string | null;
  item_id: string | null;
  value: string | null;
  metadata: Record<string, unknown>;
}

let counter = 0;

function nextEventId(): string {
  counter += 1;
  return `mmse_evt_${Date.now()}_${counter}`;
}

export function createMMSEEvent(params: {
  assessmentId: string;
  phase: MMSEPhase;
  eventType: MMSEEventType;
  questionId?: string | null;
  itemId?: string | null;
  value?: string | null;
  metadata?: Record<string, unknown>;
}): MMSEEvent {
  return {
    event_id: nextEventId(),
    assessment_id: params.assessmentId,
    game: "mmse",
    phase: params.phase,
    event_type: params.eventType,
    timestamp: new Date().toISOString(),
    question_id: params.questionId ?? null,
    item_id: params.itemId ?? null,
    value: params.value ?? null,
    metadata: params.metadata ?? {},
  };
}
