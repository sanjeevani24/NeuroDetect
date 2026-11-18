import type { MMSEEvent } from "../telemetry/mmseEvents";
import type { MMSEPhase, MMSEState } from "../types/mmseTypes";

const PHASE_ORDER: MMSEPhase[] = [
  "INTRO",
  "ORIENTATION",
  "REGISTRATION",
  "ATTENTION",
  "LANGUAGE",
  "DELAYED_RECALL",
  "COMMAND",
  "COMPLETION",
];

export function initialMMSEState(): MMSEState {
  return {
    phase: "INTRO",
    events: [],
    completed: false,
    startedAt: null,
  };
}

type MMSEAction =
  | { type: "START"; event: MMSEEvent }
  | { type: "APPEND_EVENT"; event: MMSEEvent }
  | { type: "ADVANCE"; event: MMSEEvent }
  | { type: "COMPLETE"; event: MMSEEvent };

export function mmseReducer(state: MMSEState, action: MMSEAction): MMSEState {
  switch (action.type) {
    case "START":
      if (state.startedAt) return state;
      return {
        ...state,
        phase: "ORIENTATION",
        startedAt: action.event.timestamp,
        events: [...state.events, action.event],
      };
    case "APPEND_EVENT":
      return { ...state, events: [...state.events, action.event] };
    case "ADVANCE": {
      const nextIndex = PHASE_ORDER.indexOf(state.phase) + 1;
      const nextPhase = PHASE_ORDER[nextIndex];
      if (!nextPhase) return state;
      return {
        ...state,
        phase: nextPhase,
        events: [...state.events, action.event],
      };
    }
    case "COMPLETE":
      if (state.completed) return state;
      return {
        ...state,
        phase: "COMPLETION",
        completed: true,
        events: [...state.events, action.event],
      };
    default:
      return state;
  }
}
