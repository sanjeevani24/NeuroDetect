import {
  N_BACK_LEVEL,
  STIMULUS_SET,
  TARGET_RATIO_MAX,
  TARGET_RATIO_MIN,
  TOTAL_SCORED_TRIALS,
  WARMUP_TRIALS,
  type Stimulus,
} from "../config/nbackConfig";
import type { TrialSpec } from "../types/nbackTypes";

/**
 * Minimal seeded PRNG (mulberry32) so `generateTrialSequence({ seed })`
 * is fully reproducible for tests, independent of Math.random().
 */
function mulberry32(seed: number): () => number {
  let a = seed;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export interface GenerateTrialSequenceOptions {
  totalScoredTrials?: number;
  warmupTrials?: number;
  nBackLevel?: number;
  stimulusSet?: readonly Stimulus[];
  targetRatioMin?: number;
  targetRatioMax?: number;
  /** Provide a seed for deterministic, reproducible sequences (used in tests). */
  seed?: number;
}

/**
 * Generates the full displayed trial sequence: WARMUP_TRIALS trials with no
 * valid n-back comparison (isTarget = null), followed by totalScoredTrials
 * scored trials with a controlled target/non-target ratio.
 *
 * The generator deliberately places targets rather than relying on pure
 * randomness to hit the ratio (spec section 8): it decides in advance how
 * many of the scored trials will be targets, shuffles their positions
 * (deterministically if seeded), then fills each position's stimulus to
 * satisfy or deliberately violate the n-back match as required.
 */
export function generateTrialSequence(
  options: GenerateTrialSequenceOptions = {}
): TrialSpec[] {
  const totalScoredTrials = options.totalScoredTrials ?? TOTAL_SCORED_TRIALS;
  const warmupTrials = options.warmupTrials ?? WARMUP_TRIALS;
  const nBackLevel = options.nBackLevel ?? N_BACK_LEVEL;
  const stimulusSet = options.stimulusSet ?? STIMULUS_SET;
  const targetRatioMin = options.targetRatioMin ?? TARGET_RATIO_MIN;
  const targetRatioMax = options.targetRatioMax ?? TARGET_RATIO_MAX;

  const rng = options.seed !== undefined ? mulberry32(options.seed) : Math.random;

  const targetCount = Math.round(
    totalScoredTrials * ((targetRatioMin + targetRatioMax) / 2)
  );

  // Build a shuffled boolean plan: which scored-trial positions are targets.
  const plan: boolean[] = Array.from({ length: totalScoredTrials }, (_, i) => i < targetCount);
  shuffleInPlace(plan, rng);

  const trials: TrialSpec[] = [];
  const stimulusHistory: Stimulus[] = [];

  // Warmup trials: random stimuli, no valid n-back comparison exists yet.
  for (let i = 0; i < warmupTrials; i++) {
    const stimulus = randomStimulus(stimulusSet, rng);
    stimulusHistory.push(stimulus);
    trials.push({
      trialId: `warmup-${i}`,
      trialIndex: i,
      stimulus,
      isWarmup: true,
      isTarget: null,
    });
  }

  // Scored trials.
  for (let i = 0; i < totalScoredTrials; i++) {
    const trialIndex = warmupTrials + i;
    const isTarget = plan[i];
    const nBackStimulus = stimulusHistory[stimulusHistory.length - nBackLevel];

    let stimulus: Stimulus;
    if (isTarget) {
      stimulus = nBackStimulus;
    } else {
      // pick any stimulus that is NOT equal to nBackStimulus, to avoid an
      // accidental target/non-target ambiguity (spec section 21).
      stimulus = randomStimulusExcluding(stimulusSet, nBackStimulus, rng);
    }

    stimulusHistory.push(stimulus);
    trials.push({
      trialId: `scored-${i}`,
      trialIndex,
      stimulus,
      isWarmup: false,
      isTarget,
    });
  }

  return trials;
}

function randomStimulus(set: readonly Stimulus[], rng: () => number): Stimulus {
  return set[Math.floor(rng() * set.length)];
}

function randomStimulusExcluding(
  set: readonly Stimulus[],
  excluded: Stimulus | undefined,
  rng: () => number
): Stimulus {
  if (excluded === undefined) {
    return randomStimulus(set, rng);
  }
  const candidates = set.filter((s) => s !== excluded);
  return candidates[Math.floor(rng() * candidates.length)];
}

function shuffleInPlace<T>(arr: T[], rng: () => number): void {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
}

/** Generates a short practice sequence (not scored, separate config knob). */
export function generatePracticeSequence(
  practiceTrialCount: number,
  options: Omit<GenerateTrialSequenceOptions, "totalScoredTrials" | "warmupTrials"> = {}
): TrialSpec[] {
  return generateTrialSequence({
    ...options,
    totalScoredTrials: Math.max(0, practiceTrialCount - N_BACK_LEVEL),
    warmupTrials: N_BACK_LEVEL,
  }).map((t, i) => ({ ...t, trialId: `practice-${i}` }));
}
