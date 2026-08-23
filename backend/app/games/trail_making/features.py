from __future__ import annotations

import math
import statistics
from collections import Counter
from dataclasses import dataclass
from datetime import datetime

from app.games.trail_making.config import TrailNodeType
from app.games.trail_making.exceptions import FeatureComputationError
from app.games.trail_making.schemas import (
    TrailMakingErrorType,
    TrailMakingNodeLayout,
    TrailMakingTelemetryEvent,
)


@dataclass(frozen=True)
class FeatureDefinition:
    name: str
    definition: str
    formula: str
    unit: str
    valid_range: str
    source: str


FEATURE_DEFINITIONS: dict[str, FeatureDefinition] = {
    "path_efficiency": FeatureDefinition("path_efficiency", "How directly the participant moved through the board.", "ideal_path_length / actual_path_length", "ratio", "0..1", "pointer trajectory + layout"),
    "sequence_accuracy": FeatureDefinition("sequence_accuracy", "Correct expected transitions over total required targets.", "correct_target_count / total_targets", "ratio", "0..1", "click telemetry"),
    "switching_delay": FeatureDefinition("switching_delay", "Mean reaction time while switching between number and letter targets.", "mean(correct target reaction times after the first target)", "ms", ">=0", "target_completed events"),
    "backtracking_frequency": FeatureDefinition("backtracking_frequency", "Backtracking events per required target.", "backtracking_count / total_targets", "ratio", ">=0", "pointer trajectory"),
    "rule_violation_count": FeatureDefinition("rule_violation_count", "Wrong, repeated, or out-of-order node selections.", "count(error clicks)", "count", ">=0", "node_clicked events"),
    "cursor_movement_entropy": FeatureDefinition("cursor_movement_entropy", "Directional variability of cursor movement.", "-Σ p(dir) log2 p(dir)", "bits", ">=0", "pointer trajectory"),
    "trajectory_deviation": FeatureDefinition("trajectory_deviation", "Average excess path vs straight-line path for correct transitions.", "mean((segment_path - segment_ideal) / segment_ideal)", "ratio", ">=0", "pointer trajectory + layout"),
    "tremor_jitter_frequency": FeatureDefinition("tremor_jitter_frequency", "Interaction trajectory jitter metric from rapid small reversals.", "(direction_reversals + micro_movements) / total_time_seconds", "events/sec", ">=0", "pointer trajectory"),
}


def _distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)


def _safe_mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def _safe_median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _safe_variance(values: list[float]) -> float | None:
    return statistics.variance(values) if len(values) >= 2 else (0.0 if values else None)


def _direction_entropy(samples: list[TrailMakingTelemetryEvent]) -> float:
    directions: list[int] = []
    for current, nxt in zip(samples, samples[1:]):
        if current.pointer_x is None or current.pointer_y is None or nxt.pointer_x is None or nxt.pointer_y is None:
            continue
        dx = nxt.pointer_x - current.pointer_x
        dy = nxt.pointer_y - current.pointer_y
        if dx == 0 and dy == 0:
            continue
        angle = (math.atan2(dy, dx) + (2 * math.pi)) % (2 * math.pi)
        directions.append(int((angle / (2 * math.pi)) * 8) % 8)
    if not directions:
        return 0.0
    counts = Counter(directions)
    total = len(directions)
    entropy = 0.0
    for count in counts.values():
        probability = count / total
        entropy -= probability * math.log2(probability)
    return entropy


def compute_all_features(
    events: list[TrailMakingTelemetryEvent],
    node_layout: list[TrailMakingNodeLayout],
) -> dict[str, object]:
    if not events:
        raise FeatureComputationError("event stream is empty")

    started = next((event for event in events if event.event_type.value == "game_started"), None)
    completed = next((event for event in events if event.event_type.value == "game_completed"), None)
    if started is None or completed is None:
        raise FeatureComputationError("missing game_started or game_completed event")

    total_completion_time = completed.relative_time_ms - started.relative_time_ms
    if total_completion_time <= 0:
        raise FeatureComputationError("total_completion_time must be > 0")

    layout_by_sequence = {
        node.sequence_index: node for node in sorted(node_layout, key=lambda item: item.sequence_index)
    }
    total_targets = len(layout_by_sequence)
    if total_targets == 0:
        raise FeatureComputationError("node layout is empty")

    pointer_samples = [event for event in events if event.event_type.value == "pointer_sample"]
    click_events = [event for event in events if event.event_type.value == "node_clicked"]
    correct_targets = sorted(
        [event for event in events if event.event_type.value == "target_completed"],
        key=lambda event: event.sequence_index if event.sequence_index is not None else -1,
    )
    if len(correct_targets) != total_targets:
        raise FeatureComputationError("incomplete target_completed sequence")

    actual_path_length = 0.0
    direction_reversals = 0
    micro_movements = 0
    backtracking_count = 0
    backtracking_distance = 0.0

    previous_dx = None
    previous_dy = None
    current_expected_index = 0

    for current, nxt in zip(pointer_samples, pointer_samples[1:]):
        if current.pointer_x is None or current.pointer_y is None or nxt.pointer_x is None or nxt.pointer_y is None:
            continue
        dx = nxt.pointer_x - current.pointer_x
        dy = nxt.pointer_y - current.pointer_y
        step_distance = _distance(current.pointer_x, current.pointer_y, nxt.pointer_x, nxt.pointer_y)
        actual_path_length += step_distance
        if previous_dx is not None and previous_dy is not None:
            prev_norm = math.hypot(previous_dx, previous_dy)
            cur_norm = math.hypot(dx, dy)
            if prev_norm > 0 and cur_norm > 0:
                cosine = ((previous_dx * dx) + (previous_dy * dy)) / (prev_norm * cur_norm)
                if cosine < -0.5:
                    direction_reversals += 1
                    if step_distance <= 18.0:
                        micro_movements += 1
        previous_dx = dx
        previous_dy = dy

        target = layout_by_sequence.get(min(current_expected_index, total_targets - 1))
        if target is not None:
            previous_distance = _distance(current.pointer_x, current.pointer_y, target.x, target.y)
            next_distance = _distance(nxt.pointer_x, nxt.pointer_y, target.x, target.y)
            if next_distance > previous_distance * 1.08 and step_distance > 0:
                backtracking_count += 1
                backtracking_distance += next_distance - previous_distance
        while (
            current_expected_index + 1 < total_targets
            and current.relative_time_ms >= (correct_targets[current_expected_index].relative_time_ms if current_expected_index < len(correct_targets) else float("inf"))
        ):
            current_expected_index += 1

    ideal_path_length = 0.0
    segment_deviations: list[float] = []
    reaction_times: list[float] = []
    switch_times: list[float] = []
    hesitation_durations: list[float] = []
    segment_times: list[float] = []

    for index, target in enumerate(correct_targets):
        node = layout_by_sequence[target.sequence_index or 0]
        if index == 0:
            prev_time = started.relative_time_ms
            prev_node = None
        else:
            prev_time = correct_targets[index - 1].relative_time_ms
            prev_node = layout_by_sequence[correct_targets[index - 1].sequence_index or 0]

        reaction_time = target.relative_time_ms - prev_time
        reaction_times.append(reaction_time)
        if reaction_time >= 1200:
            hesitation_durations.append(reaction_time)
        if index > 0:
            switch_times.append(reaction_time)
            segment_times.append(reaction_time)
            if prev_node is not None:
                segment_ideal = _distance(prev_node.x, prev_node.y, node.x, node.y)
                ideal_path_length += segment_ideal
                segment_samples = [
                    sample for sample in pointer_samples
                    if prev_time <= sample.relative_time_ms <= target.relative_time_ms
                    and sample.pointer_x is not None and sample.pointer_y is not None
                ]
                segment_actual = 0.0
                for sample_a, sample_b in zip(segment_samples, segment_samples[1:]):
                    segment_actual += _distance(
                        sample_a.pointer_x or 0.0,
                        sample_a.pointer_y or 0.0,
                        sample_b.pointer_x or 0.0,
                        sample_b.pointer_y or 0.0,
                    )
                if segment_ideal > 0 and segment_actual > 0:
                    segment_deviations.append(max(0.0, (segment_actual - segment_ideal) / segment_ideal))

    error_clicks = [event for event in click_events if not event.was_correct]
    total_error_count = len(error_clicks)
    correct_target_count = len(correct_targets)
    sequence_accuracy = correct_target_count / total_targets
    path_efficiency = 1.0 if actual_path_length <= 0 and ideal_path_length <= 0 else min(1.0, ideal_path_length / actual_path_length) if actual_path_length > 0 else 0.0
    switching_delay = _safe_mean(switch_times) or 0.0
    backtracking_frequency = backtracking_count / total_targets
    rule_violation_count = total_error_count
    cursor_movement_entropy = _direction_entropy(pointer_samples)
    trajectory_deviation = _safe_mean(segment_deviations) or 0.0
    tremor_jitter_frequency = (direction_reversals + micro_movements) / max(total_completion_time / 1000.0, 1e-9)

    error_recovery_times: list[float] = []
    for error in error_clicks:
        subsequent_correct = next(
            (event for event in correct_targets if event.relative_time_ms > error.relative_time_ms),
            None,
        )
        if subsequent_correct is not None:
            error_recovery_times.append(subsequent_correct.relative_time_ms - error.relative_time_ms)

    midpoint = total_targets // 2
    first_half_targets = correct_targets[:midpoint]
    second_half_targets = correct_targets[midpoint:]
    first_half_time = (first_half_targets[-1].relative_time_ms - started.relative_time_ms) if first_half_targets else None
    second_half_time = (completed.relative_time_ms - first_half_targets[-1].relative_time_ms) if first_half_targets and second_half_targets else None
    time_degradation_ratio = (
        (statistics.mean([
            first_half_targets[index].relative_time_ms - (started.relative_time_ms if index == 0 else first_half_targets[index - 1].relative_time_ms)
            for index in range(len(first_half_targets))
        ]) if first_half_targets else 0.0)
    )
    if first_half_targets and second_half_targets:
        first_mean = statistics.mean([
            first_half_targets[index].relative_time_ms - (started.relative_time_ms if index == 0 else first_half_targets[index - 1].relative_time_ms)
            for index in range(len(first_half_targets))
        ])
        second_mean = statistics.mean([
            second_half_targets[index].relative_time_ms - ((first_half_targets[-1].relative_time_ms) if index == 0 else second_half_targets[index - 1].relative_time_ms)
            for index in range(len(second_half_targets))
        ])
        time_degradation_ratio = (second_mean / first_mean) if first_mean > 0 else None
    else:
        time_degradation_ratio = None

    return {
        "path_efficiency": path_efficiency,
        "sequence_accuracy": sequence_accuracy,
        "switching_delay": switching_delay,
        "backtracking_frequency": backtracking_frequency,
        "rule_violation_count": rule_violation_count,
        "cursor_movement_entropy": cursor_movement_entropy,
        "trajectory_deviation": trajectory_deviation,
        "tremor_jitter_frequency": tremor_jitter_frequency,
        "total_completion_time": total_completion_time,
        "total_error_count": total_error_count,
        "correct_target_count": correct_target_count,
        "mean_reaction_time": _safe_mean(reaction_times),
        "median_reaction_time": _safe_median(reaction_times),
        "reaction_time_variance": _safe_variance(reaction_times),
        "hesitation_duration": sum(hesitation_durations),
        "error_recovery_time": _safe_mean(error_recovery_times),
        "first_half_time": first_half_time,
        "second_half_time": second_half_time,
        "time_degradation_ratio": time_degradation_ratio,
        "switch_count": max(0, total_targets - 1),
        "correct_switch_count": max(0, len(switch_times) - total_error_count),
        "incorrect_switch_count": total_error_count,
        "backtracking_distance": backtracking_distance,
        "trajectory_length": actual_path_length,
        "ideal_path_length": ideal_path_length,
        "correction_count": len(error_recovery_times),
        "idle_time": sum(hesitation_durations),
        "layout": [node.model_dump() for node in node_layout],
    }
