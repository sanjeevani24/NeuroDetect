# Boston Naming Feature Contract Reconciliation

The integrated Boston Naming implementation stores 30 backend-computed features in `boston_naming_results`.

Model 1 mapping status:

- Directly aligned:
  - `naming_accuracy`
  - `uncued_accuracy`
  - `cued_accuracy`
  - `semantic_cue_rate`
  - `phonemic_cue_rate`
  - `total_cue_rate`
  - `mean_response_latency_ms`
  - `median_response_latency_ms`
  - `response_latency_std_ms`
  - `hesitation_duration_ms`
  - `hesitation_variability_ms`
  - `omission_errors`
  - `semantic_errors`
  - `phonemic_errors`
  - `visual_errors`
  - `unrelated_errors`
  - `ambiguous_errors`
  - `self_correction_rate`
  - `successful_self_correction_rate`
  - `mean_response_duration_ms`
  - `response_duration_std_ms`
  - `correct_response_latency_ms`
  - `incorrect_response_latency_ms`
  - `difficulty_adjusted_accuracy`
  - `easy_accuracy`
  - `medium_accuracy`
  - `hard_accuracy`
  - `naming_consistency`
  - `fatigue_trend`
  - `completion_time_ms`

Additional persisted audit payload:

- `raw_trials`

This is stored for traceability and review, not as a direct Model 1 scalar feature.
