create table if not exists mmse_results (
    mmse_id uuid primary key default gen_random_uuid(),
    assessment_id uuid not null unique references assessments (assessment_id) on delete cascade,

    orientation_accuracy double precision not null check (orientation_accuracy between 0 and 1),
    registration_accuracy double precision not null check (registration_accuracy between 0 and 1),
    attention_accuracy double precision not null check (attention_accuracy between 0 and 1),
    serial7_accuracy double precision not null check (serial7_accuracy between 0 and 1),
    delayed_recall_accuracy double precision not null check (delayed_recall_accuracy between 0 and 1),
    language_accuracy double precision not null check (language_accuracy between 0 and 1),
    command_following_accuracy double precision not null check (command_following_accuracy between 0 and 1),
    response_latency double precision not null check (response_latency >= 0),
    latency_variability double precision not null check (latency_variability >= 0),
    omission_errors integer not null check (omission_errors >= 0),
    intrusion_errors integer not null check (intrusion_errors >= 0),
    correction_frequency double precision not null check (correction_frequency between 0 and 1),
    completion_time double precision not null check (completion_time > 0),
    performance_consistency double precision not null check (performance_consistency between 0 and 1),

    created_at timestamptz not null default now()
);

create index if not exists idx_mmse_results_assessment_id on mmse_results (assessment_id);
