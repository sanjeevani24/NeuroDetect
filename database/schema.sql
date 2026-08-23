-- NeuroDetect: Memory Recall milestone schema
-- Only the tables required for this milestone: patients, assessments,
-- memory_results. No PROCESS-2 tables, no diagnostic label columns.

create extension if not exists "pgcrypto";

create table if not exists patients (
    patient_id uuid primary key default gen_random_uuid(),
    full_name text,
    age integer,
    sex text,
    education_years integer,
    created_at timestamptz not null default now()
);

alter table patients add column if not exists full_name text;
alter table patients add column if not exists age integer;
alter table patients add column if not exists sex text;
alter table patients add column if not exists education_years integer;

create table if not exists assessments (
    assessment_id uuid primary key default gen_random_uuid(),
    patient_id uuid not null references patients (patient_id) on delete cascade,
    created_at timestamptz not null default now()
);

create table if not exists memory_results (
    memory_id uuid primary key default gen_random_uuid(),
    assessment_id uuid not null references assessments (assessment_id) on delete cascade,

    immediate_recall_accuracy double precision not null check (immediate_recall_accuracy between 0 and 1),
    delayed_recall_accuracy double precision not null check (delayed_recall_accuracy between 0 and 1),
    recognition_accuracy double precision not null check (recognition_accuracy between 0 and 1),
    recall_decay_rate double precision not null check (recall_decay_rate between 0 and 1),
    recall_latency double precision not null check (recall_latency >= 0),
    omission_errors integer not null check (omission_errors >= 0),
    intrusion_errors integer not null check (intrusion_errors >= 0),
    sequence_recall_accuracy double precision not null check (sequence_recall_accuracy between 0 and 1),
    hesitation_duration double precision not null check (hesitation_duration >= 0),
    retry_frequency integer not null check (retry_frequency >= 0),
    confidence_variability double precision not null check (confidence_variability >= 0),
    completion_time double precision not null check (completion_time > 0),
    memory_consistency_trend double precision not null check (memory_consistency_trend between 0 and 1),

    created_at timestamptz not null default now(),

    constraint memory_results_assessment_id_unique unique (assessment_id)
);

create index if not exists idx_memory_results_assessment_id on memory_results (assessment_id);
create index if not exists idx_assessments_patient_id on assessments (patient_id);

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

create table if not exists phq9_results (
    phq9_id uuid primary key default gen_random_uuid(),
    assessment_id uuid not null references assessments (assessment_id) on delete cascade,
    q1 integer not null check (q1 between 0 and 3),
    q2 integer not null check (q2 between 0 and 3),
    q3 integer not null check (q3 between 0 and 3),
    q4 integer not null check (q4 between 0 and 3),
    q5 integer not null check (q5 between 0 and 3),
    q6 integer not null check (q6 between 0 and 3),
    q7 integer not null check (q7 between 0 and 3),
    q8 integer not null check (q8 between 0 and 3),
    q9 integer not null check (q9 between 0 and 3),
    total_score integer not null check (total_score between 0 and 27),
    severity text not null,
    created_at timestamptz not null default now(),
    constraint phq9_results_assessment_id_unique unique (assessment_id)
);

create index if not exists idx_phq9_results_assessment_id on phq9_results (assessment_id);

create table if not exists gad7_results (
    gad7_id uuid primary key default gen_random_uuid(),
    assessment_id uuid not null references assessments (assessment_id) on delete cascade,
    q1 integer not null check (q1 between 0 and 3),
    q2 integer not null check (q2 between 0 and 3),
    q3 integer not null check (q3 between 0 and 3),
    q4 integer not null check (q4 between 0 and 3),
    q5 integer not null check (q5 between 0 and 3),
    q6 integer not null check (q6 between 0 and 3),
    q7 integer not null check (q7 between 0 and 3),
    total_score integer not null check (total_score between 0 and 21),
    severity text not null,
    created_at timestamptz not null default now(),
    constraint gad7_results_assessment_id_unique unique (assessment_id)
);

create index if not exists idx_gad7_results_assessment_id on gad7_results (assessment_id);

create table if not exists model1_results (
    model1_id uuid primary key default gen_random_uuid(),
    assessment_id uuid not null references assessments (assessment_id) on delete cascade,
    cognitive_performance_score double precision not null,
    model_name text not null,
    model_version text not null,
    feature_vector jsonb not null,
    created_at timestamptz not null default now(),
    constraint model1_results_assessment_unique unique (assessment_id)
);

create index if not exists idx_model1_results_assessment_id on model1_results (assessment_id);
