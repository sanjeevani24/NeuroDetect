# N-Back Feature Contract Reconciliation

## Current Integrated N-Back Result Schema

The integrated NeuroDetect N-Back implementation persists 12 backend-computed features:

1. `nback_accuracy`
2. `hit_rate`
3. `false_alarm_rate`
4. `sensitivity`
5. `response_latency`
6. `latency_variability`
7. `omission_errors`
8. `commission_errors`
9. `d_prime`
10. `response_consistency`
11. `fatigue_trend`
12. `completion_time`

These are computed from raw telemetry in `backend/app/games/nback/` and stored in `nback_results`.

## Earlier Model 1 N-Back Contract Mentioned In Project Notes

An earlier 11-feature list referenced:

1. `nback_accuracy`
2. `false_positive_rate`
3. `missed_target_rate`
4. `mean_reaction_time`
5. `reaction_time_variance`
6. `sustained_attention_score`
7. `attention_drift`
8. `hesitation_duration`
9. `idle_time`
10. `fatigue_progression`
11. `completion_time`

## Reconciliation Status

- Generated / integrated N-Back features: `12`
- Earlier Model 1 list: `11`
- Directly retained without renaming:
  - `nback_accuracy`
  - `completion_time`
- Likely near-equivalents but **not silently mapped in code**:
  - `false_alarm_rate` vs `false_positive_rate`
  - `response_latency` vs `mean_reaction_time`
  - `latency_variability` vs `reaction_time_variance`
  - `fatigue_trend` vs `fatigue_progression`
- Features with no scientifically safe one-to-one mapping from the current implementation:
  - `hit_rate`
  - `sensitivity`
  - `d_prime`
  - `response_consistency`
  - `omission_errors`
  - `commission_errors`
  - earlier `missed_target_rate`
  - earlier `sustained_attention_score`
  - earlier `attention_drift`
  - earlier `hesitation_duration`
  - earlier `idle_time`

## Decision

The richer 12-feature integrated schema was retained in the application and database.

No silent renaming or forced semantic mapping was introduced. Any downstream Model 1 adapter should be implemented explicitly, with feature-by-feature scientific review, rather than inferred during gameplay persistence.
