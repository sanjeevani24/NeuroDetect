from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TrailNodeType(str, Enum):
    NUMBER = "number"
    LETTER = "letter"


@dataclass(frozen=True)
class TrailMakingConfig:
    numbers: tuple[str, ...] = tuple(str(value) for value in range(1, 14))
    letters: tuple[str, ...] = tuple(chr(code) for code in range(ord("A"), ord("L") + 1))
    mode: str = "alternating"
    max_duration_seconds: int = 180
    board_width: int = 900
    board_height: int = 560
    node_radius: int = 26
    board_padding: int = 48
    min_node_distance: int = 82
    pointer_sample_interval_ms: int = 75
    hesitation_threshold_ms: int = 1200
    backtracking_distance_ratio_threshold: float = 1.08
    direction_reversal_cosine_threshold: float = -0.5
    jitter_distance_threshold: float = 18.0

    @property
    def sequence_labels(self) -> tuple[str, ...]:
        labels: list[str] = []
        for index, number in enumerate(self.numbers):
            labels.append(number)
            if index < len(self.letters):
                labels.append(self.letters[index])
        return tuple(labels)


DEFAULT_CONFIG = TrailMakingConfig()
