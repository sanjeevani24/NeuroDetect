"""
N-Back configuration.

All game-tunable constants live here. Nothing in the service, feature
extraction, or validation layers should hardcode these values.

Mirrors the config pattern used by the Memory Recall game (see
app/games/memory_recall/config.py in the reference architecture).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class NBackConfig:
    # Task definition
    N_BACK_LEVEL: int = 2

    # Trial counts
    WARMUP_TRIALS: int = 2          # trials 0..N_BACK_LEVEL-1, unscored by design
    TOTAL_SCORED_TRIALS: int = 40   # scored trials used for feature extraction
    PRACTICE_TRIALS: int = 6        # practice-phase trials, never scored

    # Target ratio (documented: 30-40% of scored trials are targets)
    TARGET_RATIO_MIN: float = 0.30
    TARGET_RATIO_MAX: float = 0.40

    # Stimulus set (MVP: non-semantic letters only, per spec section 6)
    STIMULUS_SET: tuple = ("A", "B", "C", "D", "E", "F")

    # Timing (milliseconds)
    STIMULUS_DURATION_MS: int = 1500
    RESPONSE_WINDOW_MS: int = 2500  # window during which a response is accepted
    INTER_TRIAL_INTERVAL_MS: int = 500

    # Random seed for deterministic test-mode sequence generation.
    # Production runs pass seed=None to the generator for true randomness.
    DETERMINISTIC_TEST_SEED: int = 42

    @property
    def TOTAL_DISPLAYED_TRIALS(self) -> int:
        return self.WARMUP_TRIALS + self.TOTAL_SCORED_TRIALS


DEFAULT_CONFIG = NBackConfig()
