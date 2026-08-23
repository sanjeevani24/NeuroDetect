import type { Stimulus } from "../config/nbackConfig";

export type NBackPhase =
  | "INTRO"
  | "PRACTICE"
  | "READY"
  | "RUNNING"
  | "COMPLETION";

export type TrialResponse = "MATCH" | "NO_MATCH" | "NONE";

export interface TrialSpec {
  trialId: string;
  trialIndex: number;
  stimulus: Stimulus;
  isWarmup: boolean;
  isTarget: boolean | null; // null only for warmup trials (no valid 2-back yet)
}

export interface TrialRuntimeState extends TrialSpec {
  presentedAt: number | null; // performance.now() ms
  responseStartedAt: number | null;
  responseAt: number | null;
  response: TrialResponse;
  correctAnswer: TrialResponse | null; // null for warmup
  responseLatencyMs: number | null;
  timedOut: boolean;
  completed: boolean;
}

export interface NBackSessionState {
  phase: NBackPhase;
  practiceTrials: TrialSpec[];
  scoredSequence: TrialSpec[]; // warmup + scored trials, in display order
  currentTrialPointer: number;
  trials: Record<string, TrialRuntimeState>;
  assessmentId: string;
  gameStartedAt: number | null;
  assessmentStartedAt: number | null;
  gameCompletedAt: number | null;
  error: string | null;
}
