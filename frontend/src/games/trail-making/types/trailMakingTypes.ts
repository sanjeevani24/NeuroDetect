export type TrailMakingPhase = "INTRO" | "RUNNING" | "COMPLETION";

export type TrailNodeType = "number" | "letter";

export type TrailMakingEventType =
  | "game_started"
  | "pointer_sample"
  | "node_clicked"
  | "target_completed"
  | "game_completed"
  | "game_submission_started"
  | "game_submission_succeeded"
  | "game_submission_failed";

export type TrailMakingErrorType =
  | "CORRECT"
  | "WRONG_TARGET"
  | "REPEAT_TARGET"
  | "OUT_OF_ORDER"
  | "WRONG_NUMBER"
  | "WRONG_LETTER"
  | "INVALID_CLICK"
  | "OTHER";

export interface TrailNodeLayout {
  node_id: string;
  label: string;
  node_type: TrailNodeType;
  sequence_index: number;
  x: number;
  y: number;
}

export interface TrailMakingTelemetryEvent {
  event_id: string;
  assessment_id: string;
  game_session_id: string;
  game: "trail_making";
  phase: Lowercase<TrailMakingPhase>;
  event_type: TrailMakingEventType;
  timestamp: string;
  relative_time_ms: number;
  node_id: string | null;
  node_label: string | null;
  node_type: TrailNodeType | null;
  sequence_index: number | null;
  expected_sequence_index: number | null;
  x: number | null;
  y: number | null;
  pointer_x: number | null;
  pointer_y: number | null;
  was_correct: boolean | null;
  error_type: TrailMakingErrorType | null;
  event_payload: Record<string, unknown>;
}
