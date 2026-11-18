export type MemoryPhase =
  | "INTRO"
  | "LEARNING"
  | "IMMEDIATE_RECALL"
  | "DISTRACTOR"
  | "DELAYED_RECALL"
  | "RECOGNITION"
  | "CONFIDENCE"
  | "COMPLETE";

export interface MemoryItem {
  id: string;
  label: string;
}

export interface ConfidenceRatings {
  immediate_recall?: number;
  delayed_recall?: number;
  recognition?: number;
}

export interface RecognitionTrial {
  trialId: string;
  itemId: string;
  isTarget: boolean;
  label: string;
}

export interface MemoryGameState {
  phase: MemoryPhase;
  currentItemIndex: number;
  startedAt: string | null;
  phaseStartedAt: string | null;
  events: import("../telemetry/eventTypes").MemoryEvent[];
  confidence: ConfidenceRatings;
  completed: boolean;
}
