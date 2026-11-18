/**
 * Must stay in exact sync with backend app/games/nback/schemas.py::NBackEventType.
 */
export const NBackEventType = {
  GAME_STARTED: "game_started",
  PRACTICE_STARTED: "practice_started",
  PRACTICE_TRIAL_STARTED: "practice_trial_started",
  PRACTICE_RESPONSE: "practice_response",
  PRACTICE_COMPLETED: "practice_completed",
  ASSESSMENT_STARTED: "assessment_started",
  TRIAL_STARTED: "trial_started",
  STIMULUS_PRESENTED: "stimulus_presented",
  RESPONSE_SUBMITTED: "response_submitted",
  RESPONSE_TIMEOUT: "response_timeout",
  TRIAL_COMPLETED: "trial_completed",
  PHASE_COMPLETED: "phase_completed",
  GAME_COMPLETED: "game_completed",
} as const;

export type NBackEventTypeValue = (typeof NBackEventType)[keyof typeof NBackEventType];
