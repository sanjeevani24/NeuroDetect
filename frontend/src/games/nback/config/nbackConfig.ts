/**
 * N-Back configuration.
 *
 * Mirrors backend/app/games/nback/config.py exactly. If you change a value
 * here, change it there too (or better: expose one via an API and remove
 * the duplication once the project has a shared-config mechanism).
 */

export const N_BACK_LEVEL = 2;

export const WARMUP_TRIALS = 2;
export const TOTAL_SCORED_TRIALS = 40;
export const PRACTICE_TRIALS = 6;

export const TOTAL_DISPLAYED_TRIALS = WARMUP_TRIALS + TOTAL_SCORED_TRIALS; // 42

// Target ratio: documented 30-40% of scored trials are targets (spec section 8)
export const TARGET_RATIO_MIN = 0.3;
export const TARGET_RATIO_MAX = 0.4;

// Non-semantic stimulus set (spec section 6)
export const STIMULUS_SET = ["A", "B", "C", "D", "E", "F"] as const;
export type Stimulus = (typeof STIMULUS_SET)[number];

// Timing (milliseconds)
export const STIMULUS_DURATION_MS = 1500;
export const RESPONSE_WINDOW_MS = 2500;
export const INTER_TRIAL_INTERVAL_MS = 500;

// Deterministic seed for test-mode trial generation
export const DETERMINISTIC_TEST_SEED = 42;

export const NBackConfig = {
  N_BACK_LEVEL,
  WARMUP_TRIALS,
  TOTAL_SCORED_TRIALS,
  PRACTICE_TRIALS,
  TOTAL_DISPLAYED_TRIALS,
  TARGET_RATIO_MIN,
  TARGET_RATIO_MAX,
  STIMULUS_SET,
  STIMULUS_DURATION_MS,
  RESPONSE_WINDOW_MS,
  INTER_TRIAL_INTERVAL_MS,
  DETERMINISTIC_TEST_SEED,
} as const;
