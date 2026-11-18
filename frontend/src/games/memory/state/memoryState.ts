import type { ConfidenceRatings, MemoryGameState, MemoryPhase } from "../types/memoryTypes";
import type { MemoryEvent } from "../telemetry/eventTypes";

/**
 * Linear phase order. Transitions are only ever allowed to the immediate
 * next phase — no arbitrary jumps, no skipping, no going backwards. This
 * is the state machine referenced in spec section 7.
 */
const PHASE_ORDER: MemoryPhase[] = [
  "INTRO",
  "LEARNING",
  "IMMEDIATE_RECALL",
  "DISTRACTOR",
  "DELAYED_RECALL",
  "RECOGNITION",
  "CONFIDENCE",
  "COMPLETE",
];

export function initialMemoryState(): MemoryGameState {
  return {
    phase: "INTRO",
    currentItemIndex: 0,
    startedAt: null,
    phaseStartedAt: null,
    events: [],
    confidence: {},
    completed: false,
  };
}

export type MemoryAction =
  | { type: "START_GAME"; event: MemoryEvent }
  | { type: "ADVANCE_PHASE"; event: MemoryEvent }
  | { type: "SET_ITEM_INDEX"; index: number }
  | { type: "APPEND_EVENT"; event: MemoryEvent }
  | { type: "SET_CONFIDENCE"; phase: keyof ConfidenceRatings; value: number; event: MemoryEvent }
  | { type: "COMPLETE_GAME"; event: MemoryEvent };

function canAdvanceTo(current: MemoryPhase, next: MemoryPhase): boolean {
  const currentIndex = PHASE_ORDER.indexOf(current);
  const nextIndex = PHASE_ORDER.indexOf(next);
  return nextIndex === currentIndex + 1;
}

/**
 * The single reducer for Memory Recall game state. All phase transitions,
 * event appends, and confidence capture go through here so that critical
 * game state is never scattered across unrelated components. Timers are
 * not modeled here — components read timestamps from appended events;
 * this reducer never derives "now" itself except to stamp phaseStartedAt
 * from the event that triggered the transition, keeping timestamps as the
 * single source of truth (never frame counts).
 */
export function memoryReducer(state: MemoryGameState, action: MemoryAction): MemoryGameState {
  switch (action.type) {
    case "START_GAME": {
      if (state.startedAt !== null) {
        // duplicate game start guard
        return state;
      }
      const nextPhase: MemoryPhase = "LEARNING";
      if (!canAdvanceTo(state.phase, nextPhase)) return state;
      return {
        ...state,
        phase: nextPhase,
        startedAt: action.event.timestamp,
        phaseStartedAt: action.event.timestamp,
        events: [...state.events, action.event],
      };
    }

    case "ADVANCE_PHASE": {
      const nextPhaseIndex = PHASE_ORDER.indexOf(state.phase) + 1;
      const nextPhase = PHASE_ORDER[nextPhaseIndex];
      if (!nextPhase || !canAdvanceTo(state.phase, nextPhase)) {
        // prevents duplicate phase completion / arbitrary transitions
        return state;
      }
      return {
        ...state,
        phase: nextPhase,
        phaseStartedAt: action.event.timestamp,
        currentItemIndex: 0,
        events: [...state.events, action.event],
      };
    }

    case "SET_ITEM_INDEX":
      return { ...state, currentItemIndex: action.index };

    case "APPEND_EVENT":
      return { ...state, events: [...state.events, action.event] };

    case "SET_CONFIDENCE":
      return {
        ...state,
        confidence: { ...state.confidence, [action.phase]: action.value },
        events: [...state.events, action.event],
      };

    case "COMPLETE_GAME": {
      if (state.completed) {
        // prevents duplicate game completion
        return state;
      }
      return {
        ...state,
        completed: true,
        events: [...state.events, action.event],
      };
    }

    default:
      return state;
  }
}
