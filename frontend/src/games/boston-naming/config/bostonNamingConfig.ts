import type { BostonNamingStimulus } from "../types/bostonNamingTypes";

export const PRACTICE_TRIALS = 3;
export const TOTAL_SCORED_TRIALS = 20;
export const INITIAL_RESPONSE_WINDOW_MS = 5000;
export const PHONEMIC_CUE_DELAY_MS = 3000;
export const MAX_RESPONSE_WINDOW_MS = 12000;

export const PRACTICE_STIMULI: BostonNamingStimulus[] = [
  { stimulusId: "practice_01", order: 1, display: "🍎", alt: "Apple illustration", canonicalName: "apple", acceptedAnswers: ["apple"], category: "food", difficulty: "EASY", semanticCue: "This is something you eat.", phonemicCue: "It starts with 'ap'." },
  { stimulusId: "practice_02", order: 2, display: "🪑", alt: "Chair illustration", canonicalName: "chair", acceptedAnswers: ["chair"], category: "household", difficulty: "EASY", semanticCue: "You sit on this.", phonemicCue: "It starts with 'ch'." },
  { stimulusId: "practice_03", order: 3, display: "🕒", alt: "Clock illustration", canonicalName: "clock", acceptedAnswers: ["clock"], category: "household", difficulty: "EASY", semanticCue: "It tells time.", phonemicCue: "It starts with 'cl'." },
];

export const SCORED_STIMULI: BostonNamingStimulus[] = [
  { stimulusId: "stim_01", order: 1, display: "🍎", alt: "Apple illustration", canonicalName: "apple", acceptedAnswers: ["apple"], category: "food", difficulty: "EASY", semanticCue: "This is a fruit you can eat.", phonemicCue: "It starts with 'ap'." },
  { stimulusId: "stim_02", order: 2, display: "✂️", alt: "Scissors illustration", canonicalName: "scissors", acceptedAnswers: ["scissors", "a pair of scissors"], category: "tool", difficulty: "EASY", semanticCue: "You use this to cut paper.", phonemicCue: "It starts with 'sc'." },
  { stimulusId: "stim_03", order: 3, display: "🚲", alt: "Bicycle illustration", canonicalName: "bicycle", acceptedAnswers: ["bicycle", "bike"], category: "transport", difficulty: "EASY", semanticCue: "You ride this with two wheels.", phonemicCue: "It starts with 'bi'." },
  { stimulusId: "stim_04", order: 4, display: "☂️", alt: "Umbrella illustration", canonicalName: "umbrella", acceptedAnswers: ["umbrella"], category: "weather", difficulty: "EASY", semanticCue: "You use this in the rain.", phonemicCue: "It starts with 'um'." },
  { stimulusId: "stim_05", order: 5, display: "🪜", alt: "Ladder illustration", canonicalName: "ladder", acceptedAnswers: ["ladder"], category: "tool", difficulty: "EASY", semanticCue: "You climb up with this.", phonemicCue: "It starts with 'la'." },
  { stimulusId: "stim_06", order: 6, display: "🧤", alt: "Glove illustration", canonicalName: "glove", acceptedAnswers: ["glove", "gloves"], category: "clothing", difficulty: "EASY", semanticCue: "You wear this on your hand.", phonemicCue: "It starts with 'gl'." },
  { stimulusId: "stim_07", order: 7, display: "🌵", alt: "Cactus illustration", canonicalName: "cactus", acceptedAnswers: ["cactus"], category: "plant", difficulty: "MEDIUM", semanticCue: "This plant has spines.", phonemicCue: "It starts with 'cac'." },
  { stimulusId: "stim_08", order: 8, display: "⚓", alt: "Anchor illustration", canonicalName: "anchor", acceptedAnswers: ["anchor"], category: "nautical", difficulty: "MEDIUM", semanticCue: "A boat drops this to stay in place.", phonemicCue: "It starts with 'an'." },
  { stimulusId: "stim_09", order: 9, display: "🧭", alt: "Compass illustration", canonicalName: "compass", acceptedAnswers: ["compass"], category: "tool", difficulty: "MEDIUM", semanticCue: "This helps you find north.", phonemicCue: "It starts with 'com'." },
  { stimulusId: "stim_10", order: 10, display: "🐎", alt: "Horse saddle illustration", canonicalName: "saddle", acceptedAnswers: ["saddle"], category: "animal", difficulty: "MEDIUM", semanticCue: "You sit on this when riding a horse.", phonemicCue: "It starts with 'sad'." },
  { stimulusId: "stim_11", order: 11, display: "🧊", alt: "Igloo illustration", canonicalName: "igloo", acceptedAnswers: ["igloo"], category: "dwelling", difficulty: "MEDIUM", semanticCue: "A snow house.", phonemicCue: "It starts with 'ig'." },
  { stimulusId: "stim_12", order: 12, display: "🥨", alt: "Pretzel illustration", canonicalName: "pretzel", acceptedAnswers: ["pretzel"], category: "food", difficulty: "MEDIUM", semanticCue: "A twisted baked snack.", phonemicCue: "It starts with 'pre'." },
  { stimulusId: "stim_13", order: 13, display: "🫗", alt: "Funnel illustration", canonicalName: "funnel", acceptedAnswers: ["funnel"], category: "tool", difficulty: "MEDIUM", semanticCue: "This helps pour liquid into a narrow opening.", phonemicCue: "It starts with 'fun'." },
  { stimulusId: "stim_14", order: 14, display: "🎼", alt: "Harp illustration", canonicalName: "harp", acceptedAnswers: ["harp"], category: "instrument", difficulty: "MEDIUM", semanticCue: "A string instrument with a frame.", phonemicCue: "It starts with 'ha'." },
  { stimulusId: "stim_15", order: 15, display: "🩺", alt: "Stethoscope illustration", canonicalName: "stethoscope", acceptedAnswers: ["stethoscope"], category: "medical", difficulty: "HARD", semanticCue: "A doctor listens with this.", phonemicCue: "It starts with 'steth'." },
  { stimulusId: "stim_16", order: 16, display: "📷", alt: "Tripod illustration", canonicalName: "tripod", acceptedAnswers: ["tripod"], category: "tool", difficulty: "HARD", semanticCue: "A camera can stand on this.", phonemicCue: "It starts with 'tri'." },
  { stimulusId: "stim_17", order: 17, display: "⏳", alt: "Hourglass illustration", canonicalName: "hourglass", acceptedAnswers: ["hourglass", "sand timer"], category: "time", difficulty: "HARD", semanticCue: "Sand falls through this to measure time.", phonemicCue: "It starts with 'hour'." },
  { stimulusId: "stim_18", order: 18, display: "🔭", alt: "Binoculars illustration", canonicalName: "binoculars", acceptedAnswers: ["binoculars"], category: "tool", difficulty: "HARD", semanticCue: "You look through these to see far away.", phonemicCue: "It starts with 'bin'." },
  { stimulusId: "stim_19", order: 19, display: "🌡️", alt: "Thermometer illustration", canonicalName: "thermometer", acceptedAnswers: ["thermometer"], category: "medical", difficulty: "HARD", semanticCue: "This measures temperature.", phonemicCue: "It starts with 'ther'." },
  { stimulusId: "stim_20", order: 20, display: "🪗", alt: "Accordion illustration", canonicalName: "accordion", acceptedAnswers: ["accordion"], category: "instrument", difficulty: "HARD", semanticCue: "A musical instrument that expands and folds.", phonemicCue: "It starts with 'ac'." },
];
