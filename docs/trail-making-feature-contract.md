# Trail Making Feature Contract

Model 1-compatible fields:

- `path_efficiency`
- `sequence_accuracy`
- `switching_delay`
- `backtracking_frequency`
- `rule_violation_count`
- `cursor_movement_entropy`
- `trajectory_deviation`
- `tremor_jitter_frequency`

Additional stored Trail Making fields:

- `total_completion_time`
- `total_error_count`
- `correct_target_count`
- `mean_reaction_time`
- `median_reaction_time`
- `reaction_time_variance`
- `hesitation_duration`
- `error_recovery_time`
- `first_half_time`
- `second_half_time`
- `time_degradation_ratio`
- `switch_count`
- `correct_switch_count`
- `incorrect_switch_count`
- `backtracking_distance`
- `trajectory_length`
- `ideal_path_length`
- `correction_count`
- `idle_time`

Storage model:

- `trail_making_results`: summary features plus `layout`
- `trail_making_events`: raw sampled pointer and click telemetry
