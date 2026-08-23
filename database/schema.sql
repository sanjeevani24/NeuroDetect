-- NeuroDetect: Memory Recall milestone schema
-- Only the tables required for this milestone: patients, assessments,
-- memory_results. No PROCESS-2 tables, no diagnostic label columns.

create extension if not exists "pgcrypto";

create table if not exists patients (
    patient_id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now()
);

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
