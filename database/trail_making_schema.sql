create table if not exists trail_making_results (
    trail_id uuid primary key default gen_random_uuid(),
    assessment_id uuid not null references assessments (assessment_id) on delete cascade,
    game_session_id uuid not null,

    path_efficiency double precision not null check (path_efficiency between 0 and 1),
    sequence_accuracy double precision not null check (sequence_accuracy between 0 and 1),
    switching_delay double precision not null check (switching_delay >= 0),
    backtracking_frequency double precision not null check (backtracking_frequency >= 0),
    rule_violation_count integer not null check (rule_violation_count >= 0),
    cursor_movement_entropy double precision not null check (cursor_movement_entropy >= 0),
    trajectory_deviation double precision not null check (trajectory_deviation >= 0),
    tremor_jitter_frequency double precision not null check (tremor_jitter_frequency >= 0),
    total_completion_time double precision not null check (total_completion_time > 0),
    total_error_count integer not null check (total_error_count >= 0),
    correct_target_count integer not null check (correct_target_count >= 0),
    mean_reaction_time double precision null check (mean_reaction_time >= 0),
    median_reaction_time double precision null check (median_reaction_time >= 0),
    reaction_time_variance double precision null check (reaction_time_variance >= 0),
    hesitation_duration double precision null check (hesitation_duration >= 0),
    error_recovery_time double precision null check (error_recovery_time >= 0),
    first_half_time double precision null check (first_half_time >= 0),
    second_half_time double precision null check (second_half_time >= 0),
    time_degradation_ratio double precision null check (time_degradation_ratio >= 0),
    switch_count integer not null check (switch_count >= 0),
    correct_switch_count integer not null check (correct_switch_count >= 0),
    incorrect_switch_count integer not null check (incorrect_switch_count >= 0),
    backtracking_distance double precision null check (backtracking_distance >= 0),
    trajectory_length double precision null check (trajectory_length >= 0),
    ideal_path_length double precision null check (ideal_path_length >= 0),
    correction_count integer not null check (correction_count >= 0),
    idle_time double precision null check (idle_time >= 0),
    layout jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),

    constraint trail_making_results_assessment_id_unique unique (assessment_id)
);

create index if not exists idx_trail_making_results_assessment_id
on trail_making_results (assessment_id);

create table if not exists trail_making_events (
    event_id uuid primary key,
    assessment_id uuid not null references assessments (assessment_id) on delete cascade,
    game_session_id uuid not null,
    event_type text not null,
    timestamp timestamptz not null default now(),
    relative_time_ms double precision not null check (relative_time_ms >= 0),
    node_id text,
    node_label text,
    node_type text,
    sequence_index integer,
    expected_sequence_index integer,
    x double precision,
    y double precision,
    pointer_x double precision,
    pointer_y double precision,
    was_correct boolean,
    error_type text,
    event_payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_trail_making_events_assessment_id
on trail_making_events (assessment_id);
create index if not exists idx_trail_making_events_game_session_id
on trail_making_events (game_session_id);
create index if not exists idx_trail_making_events_event_type
on trail_making_events (event_type);
