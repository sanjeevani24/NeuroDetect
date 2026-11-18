from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DifficultyLevel(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


@dataclass(frozen=True)
class StimulusDefinition:
    stimulus_id: str
    canonical_name: str
    accepted_answers: tuple[str, ...]
    category: str
    difficulty: DifficultyLevel
    order: int
    semantic_cue: str
    phonemic_cue: str


@dataclass(frozen=True)
class BostonNamingConfig:
    PRACTICE_TRIALS: int = 3
    TOTAL_SCORED_TRIALS: int = 20
    INITIAL_RESPONSE_WINDOW_MS: int = 5000
    PHONEMIC_CUE_DELAY_MS: int = 3000
    MAX_RESPONSE_WINDOW_MS: int = 12000


PRACTICE_STIMULI: tuple[StimulusDefinition, ...] = (
    StimulusDefinition("practice_01", "apple", ("apple",), "food", DifficultyLevel.EASY, 1, "This is something you eat.", "It starts with 'ap'."),
    StimulusDefinition("practice_02", "chair", ("chair",), "household", DifficultyLevel.EASY, 2, "You sit on this.", "It starts with 'ch'."),
    StimulusDefinition("practice_03", "clock", ("clock",), "household", DifficultyLevel.EASY, 3, "It tells time.", "It starts with 'cl'."),
)

SCORED_STIMULI: tuple[StimulusDefinition, ...] = (
    StimulusDefinition("stim_01", "apple", ("apple",), "food", DifficultyLevel.EASY, 1, "This is a fruit you can eat.", "It starts with 'ap'."),
    StimulusDefinition("stim_02", "scissors", ("scissors", "a pair of scissors"), "tool", DifficultyLevel.EASY, 2, "You use this to cut paper.", "It starts with 'sc'."),
    StimulusDefinition("stim_03", "bicycle", ("bicycle", "bike"), "transport", DifficultyLevel.EASY, 3, "You ride this with two wheels.", "It starts with 'bi'."),
    StimulusDefinition("stim_04", "umbrella", ("umbrella",), "weather", DifficultyLevel.EASY, 4, "You use this in the rain.", "It starts with 'um'."),
    StimulusDefinition("stim_05", "ladder", ("ladder",), "tool", DifficultyLevel.EASY, 5, "You climb up with this.", "It starts with 'la'."),
    StimulusDefinition("stim_06", "glove", ("glove", "gloves"), "clothing", DifficultyLevel.EASY, 6, "You wear this on your hand.", "It starts with 'gl'."),
    StimulusDefinition("stim_07", "cactus", ("cactus",), "plant", DifficultyLevel.MEDIUM, 7, "This plant has spines.", "It starts with 'cac'."),
    StimulusDefinition("stim_08", "anchor", ("anchor",), "nautical", DifficultyLevel.MEDIUM, 8, "A boat drops this to stay in place.", "It starts with 'an'."),
    StimulusDefinition("stim_09", "compass", ("compass",), "tool", DifficultyLevel.MEDIUM, 9, "This helps you find north.", "It starts with 'com'."),
    StimulusDefinition("stim_10", "saddle", ("saddle",), "animal", DifficultyLevel.MEDIUM, 10, "You sit on this when riding a horse.", "It starts with 'sad'."),
    StimulusDefinition("stim_11", "igloo", ("igloo",), "dwelling", DifficultyLevel.MEDIUM, 11, "A snow house.", "It starts with 'ig'."),
    StimulusDefinition("stim_12", "pretzel", ("pretzel",), "food", DifficultyLevel.MEDIUM, 12, "A twisted baked snack.", "It starts with 'pre'."),
    StimulusDefinition("stim_13", "funnel", ("funnel",), "tool", DifficultyLevel.MEDIUM, 13, "This helps pour liquid into a narrow opening.", "It starts with 'fun'."),
    StimulusDefinition("stim_14", "harp", ("harp",), "instrument", DifficultyLevel.MEDIUM, 14, "A string instrument with a frame.", "It starts with 'ha'."),
    StimulusDefinition("stim_15", "stethoscope", ("stethoscope",), "medical", DifficultyLevel.HARD, 15, "A doctor listens with this.", "It starts with 'steth'."),
    StimulusDefinition("stim_16", "tripod", ("tripod",), "tool", DifficultyLevel.HARD, 16, "A camera can stand on this.", "It starts with 'tri'."),
    StimulusDefinition("stim_17", "hourglass", ("hourglass", "sand timer"), "time", DifficultyLevel.HARD, 17, "Sand falls through this to measure time.", "It starts with 'hour'."),
    StimulusDefinition("stim_18", "binoculars", ("binoculars",), "tool", DifficultyLevel.HARD, 18, "You look through these to see far away.", "It starts with 'bin'."),
    StimulusDefinition("stim_19", "thermometer", ("thermometer",), "medical", DifficultyLevel.HARD, 19, "This measures temperature.", "It starts with 'ther'."),
    StimulusDefinition("stim_20", "accordion", ("accordion",), "instrument", DifficultyLevel.HARD, 20, "A musical instrument that expands and folds.", "It starts with 'ac'."),
)

STIMULUS_LOOKUP = {stimulus.stimulus_id: stimulus for stimulus in (*PRACTICE_STIMULI, *SCORED_STIMULI)}

DEFAULT_CONFIG = BostonNamingConfig()
