import type { MemoryItem } from "../types/memoryTypes";

/** Number of target items shown during the learning phase. */
export const TARGET_ITEM_COUNT = 12;

/** How long each item is displayed during learning, in milliseconds. */
export const LEARNING_ITEM_DURATION_MS = 3000;

/** Threshold used server-side for hesitation_duration; mirrored here for UI hints only. */
export const HESITATION_THRESHOLD_SECONDS = 2;

/** Number of recognition trials: 12 targets + distractors. */
export const RECOGNITION_TRIAL_COUNT = 16;
export const RECOGNITION_DISTRACTOR_COUNT = RECOGNITION_TRIAL_COUNT - TARGET_ITEM_COUNT;

export const DISTRACTOR_CONFIG = {
  startValue: 100,
  step: 3,
  prompt: "Count backwards from 100 by 3s.",
};

/**
 * Fixed MVP target item pool. This is a configuration object, not a
 * hardcoded assumption baked into game logic — future item pools
 * (localized, alternate forms) can be swapped in without touching the
 * game state machine or feature extraction.
 */
export const TARGET_ITEM_POOL: MemoryItem[] = [
  { id: "item_001", label: "apple" },
  { id: "item_002", label: "chair" },
  { id: "item_003", label: "train" },
  { id: "item_004", label: "river" },
  { id: "item_005", label: "clock" },
  { id: "item_006", label: "bottle" },
  { id: "item_007", label: "garden" },
  { id: "item_008", label: "book" },
  { id: "item_009", label: "camera" },
  { id: "item_010", label: "shoe" },
  { id: "item_011", label: "flower" },
  { id: "item_012", label: "key" },
];

/** Distractor items shown alongside targets during immediate recall / recognition. */
export const DISTRACTOR_ITEM_POOL: MemoryItem[] = [
  { id: "distractor_001", label: "mountain" },
  { id: "distractor_002", label: "window" },
  { id: "distractor_003", label: "guitar" },
  { id: "distractor_004", label: "pencil" },
];
