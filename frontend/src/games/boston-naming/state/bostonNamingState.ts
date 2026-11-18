import type { BostonNamingPhase } from "../types/bostonNamingTypes";

export interface BostonNamingState {
  phase: BostonNamingPhase;
}

export function createInitialState(): BostonNamingState {
  return { phase: "INTRO" };
}
