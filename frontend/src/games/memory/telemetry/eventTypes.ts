import type { MemoryPhase } from "../types/memoryTypes";

export type MemoryEventType =
  | "game_started"
  | "phase_started"
  | "item_presented"
  | "item_hidden"
  | "item_selected"
  | "item_deselected"
  | "response_started"
  | "response_submitted"
  | "response_edited"
  | "retry"
  | "recognition_response"
  | "confidence_submitted"
  | "phase_completed"
  | "game_completed";

/**
 * Structured telemetry event. This shape must stay in sync with
 * backend/app/games/memory/schemas.py::MemoryEvent — the backend is the
 * source of truth for validation, this is the frontend's mirror of it.
 */
export interface MemoryEvent {
  event_id: string;
  assessment_id: string;
  game: "memory";
  phase: MemoryPhase;
  event_type: MemoryEventType;
  timestamp: string; // ISO 8601
  item_id?: string | null;
  trial_id?: string | null;
  value?: string | null;
  metadata: Record<string, unknown>;
}
