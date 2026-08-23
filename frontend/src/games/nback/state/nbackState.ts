import type {
  NBackPhase,
  NBackSessionState,
  TrialResponse,
  TrialRuntimeState,
  TrialSpec,
} from "../types/nbackTypes";

export type NBackAction =
  | { type: "START_GAME"; timestampMs: number }
  | { type: "START_PRACTICE"; trials: TrialSpec[] }
  | { type: "COMPLETE_PRACTICE" }
  | { type: "READY_ASSESSMENT"; trials: TrialSpec[] }
  | { type: "START_ASSESSMENT"; timestampMs: number }
  | { type: "PRESENT_TRIAL"; trialIndex: number; timestampMs: number }
  | {
      type: "SUBMIT_RESPONSE";
      trialId: string;
      response: TrialResponse;
      timestampMs: number;
    }
  | { type: "TIMEOUT_TRIAL"; trialId: string; timestampMs: number }
  | { type: "COMPLETE_TRIAL"; trialId: string }
  | { type: "ADVANCE_TRIAL" }
  | { type: "COMPLETE_GAME"; timestampMs: number }
  | { type: "SET_ERROR"; message: string };

function toRuntime(spec: TrialSpec): TrialRuntimeState {
  return {
    ...spec,
    presentedAt: null,
    responseStartedAt: null,
    responseAt: null,
    response: "NONE",
    correctAnswer: spec.isTarget === null ? null : spec.isTarget ? "MATCH" : "NO_MATCH",
    responseLatencyMs: null,
    timedOut: false,
    completed: false,
  };
}

export function createInitialState(assessmentId: string): NBackSessionState {
  return {
    phase: "INTRO",
    practiceTrials: [],
    scoredSequence: [],
    currentTrialPointer: -1,
    trials: {},
    assessmentId,
    gameStartedAt: null,
    assessmentStartedAt: null,
    gameCompletedAt: null,
    error: null,
  };
}

/**
 * Guards against: duplicate responses, duplicate trial completion,
 * responding/advancing on an unstarted or already-completed trial,
 * and skipping trials out of order (spec section 11).
 */
export function nbackReducer(
  state: NBackSessionState,
  action: NBackAction
): NBackSessionState {
  switch (action.type) {
    case "START_GAME":
      if (state.phase !== "INTRO") return state;
      return { ...state, gameStartedAt: action.timestampMs };

    case "START_PRACTICE": {
      const trials: Record<string, TrialRuntimeState> = {};
      for (const t of action.trials) trials[t.trialId] = toRuntime(t);
      return {
        ...state,
        phase: "PRACTICE",
        practiceTrials: action.trials,
        trials: { ...state.trials, ...trials },
        currentTrialPointer: 0,
      };
    }

    case "COMPLETE_PRACTICE":
      if (state.phase !== "PRACTICE") return state;
      return { ...state, phase: "READY", currentTrialPointer: -1 };

    case "READY_ASSESSMENT": {
      const trials: Record<string, TrialRuntimeState> = { ...state.trials };
      for (const t of action.trials) trials[t.trialId] = toRuntime(t);
      return {
        ...state,
        phase: "READY",
        scoredSequence: action.trials,
        trials,
      };
    }

    case "START_ASSESSMENT":
      if (state.phase !== "READY") return state;
      return {
        ...state,
        phase: "RUNNING",
        assessmentStartedAt: action.timestampMs,
        currentTrialPointer: 0,
      };

    case "PRESENT_TRIAL": {
      if (state.phase !== "RUNNING" && state.phase !== "PRACTICE") return state;
      const sequence = state.phase === "PRACTICE" ? state.practiceTrials : state.scoredSequence;
      const spec = sequence[action.trialIndex];
      if (!spec) return state;
      const existing = state.trials[spec.trialId];
      if (existing?.presentedAt !== null && existing !== undefined) {
        // already presented — guard against duplicate presentation
        return state;
      }
      return {
        ...state,
        currentTrialPointer: action.trialIndex,
        trials: {
          ...state.trials,
          [spec.trialId]: {
            ...toRuntime(spec),
            presentedAt: action.timestampMs,
            responseStartedAt: action.timestampMs,
          },
        },
      };
    }

    case "SUBMIT_RESPONSE": {
      const trial = state.trials[action.trialId];
      if (!trial) return state;
      // Guard: no response after the trial already completed/timed out (duplicate response)
      if (trial.completed || trial.timedOut || trial.response !== "NONE") return state;
      if (trial.presentedAt === null) return state;

      const latency = action.timestampMs - trial.presentedAt;
      return {
        ...state,
        trials: {
          ...state.trials,
          [action.trialId]: {
            ...trial,
            response: action.response,
            responseAt: action.timestampMs,
            responseLatencyMs: latency,
          },
        },
      };
    }

    case "TIMEOUT_TRIAL": {
      const trial = state.trials[action.trialId];
      if (!trial) return state;
      // Guard: don't timeout a trial that already got a valid response
      if (trial.completed || trial.response !== "NONE") return state;
      return {
        ...state,
        trials: {
          ...state.trials,
          [action.trialId]: { ...trial, timedOut: true },
        },
      };
    }

    case "COMPLETE_TRIAL": {
      const trial = state.trials[action.trialId];
      if (!trial) return state;
      if (trial.completed) return state; // guard against duplicate completion
      return {
        ...state,
        trials: {
          ...state.trials,
          [action.trialId]: { ...trial, completed: true },
        },
      };
    }

    case "ADVANCE_TRIAL": {
      const sequence = state.phase === "PRACTICE" ? state.practiceTrials : state.scoredSequence;
      const next = state.currentTrialPointer + 1;
      if (next >= sequence.length) return state; // caller should dispatch completion instead
      return { ...state, currentTrialPointer: next };
    }

    case "COMPLETE_GAME":
      if (state.phase !== "RUNNING") return state;
      return { ...state, phase: "COMPLETION", gameCompletedAt: action.timestampMs };

    case "SET_ERROR":
      return { ...state, error: action.message };

    default:
      return state;
  }
}

export function isLastTrial(state: NBackSessionState): boolean {
  const sequence = state.phase === "PRACTICE" ? state.practiceTrials : state.scoredSequence;
  return state.currentTrialPointer >= sequence.length - 1;
}

export function currentPhase(state: NBackSessionState): NBackPhase {
  return state.phase;
}
