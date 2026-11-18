export const BostonNamingEventType = {
  GAME_STARTED: "game_started",
  PRACTICE_STARTED: "practice_started",
  PRACTICE_TRIAL_STARTED: "practice_trial_started",
  PRACTICE_RESPONSE: "practice_response",
  PRACTICE_COMPLETED: "practice_completed",
  ASSESSMENT_STARTED: "assessment_started",
  TRIAL_STARTED: "trial_started",
  STIMULUS_PRESENTED: "stimulus_presented",
  RESPONSE_RECORDING_STARTED: "response_recording_started",
  RESPONSE_RECORDING_STOPPED: "response_recording_stopped",
  TRANSCRIPTION_COMPLETED: "transcription_completed",
  RESPONSE_CLASSIFIED: "response_classified",
  CUE_PRESENTED: "cue_presented",
  SELF_CORRECTION_DETECTED: "self_correction_detected",
  TRIAL_COMPLETED: "trial_completed",
  RESPONSE_TIMEOUT: "response_timeout",
  GAME_COMPLETED: "game_completed",
  GAME_SUBMISSION_STARTED: "game_submission_started",
  GAME_SUBMISSION_SUCCEEDED: "game_submission_succeeded",
  GAME_SUBMISSION_FAILED: "game_submission_failed",
} as const;

export type BostonNamingEventTypeValue =
  (typeof BostonNamingEventType)[keyof typeof BostonNamingEventType];
