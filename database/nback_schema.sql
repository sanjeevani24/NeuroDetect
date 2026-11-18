create table if not exists nback_results (
    nback_id uuid primary key default gen_random_uuid(),
    assessment_id uuid not null unique references assessments (assessment_id) on delete cascade,

    nback_accuracy double precision not null check (nback_accuracy between 0 and 1),
    hit_rate double precision not null check (hit_rate between 0 and 1),
    false_alarm_rate double precision not null check (false_alarm_rate between 0 and 1),
    sensitivity double precision not null check (sensitivity between -1 and 1),
    response_latency double precision not null check (response_latency >= 0),
    latency_variability double precision not null check (latency_variability >= 0),
    omission_errors integer not null check (omission_errors >= 0),
    commission_errors integer not null check (commission_errors >= 0),
    d_prime double precision not null,
    response_consistency double precision not null check (response_consistency >= 0),
    fatigue_trend double precision not null check (fatigue_trend between -1 and 1),
    completion_time double precision not null check (completion_time > 0),

    created_at timestamptz not null default now()
);

create index if not exists idx_nback_results_assessment_id on nback_results (assessment_id);
