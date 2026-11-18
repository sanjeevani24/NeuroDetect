# Model 1 Feature Mapping

This document mirrors the authoritative mapping table in `backend/app/ml/model1/feature_aggregator.py`.

| Model Feature | Source | Transformation | Unit | Valid Range |
| --- | --- | --- | --- | --- |
| `overall_mmse_score` | `mmse_results` | weighted MMSE domain reconstruction to 30-point scale | points | `0..30` |
| `orientation_score` | `mmse_results.orientation_accuracy` | direct | ratio | `0..1` |
| `attention_score` | `mmse_results.attention_accuracy` | direct | ratio | `0..1` |
| `recall_score` | `mmse_results.delayed_recall_accuracy` | direct | ratio | `0..1` |
| `language_score` | `mmse_results.language_accuracy` | direct | ratio | `0..1` |
| `question_accuracy` | `mmse_results` | weighted score divided by 26 MMSE scored prompts | ratio | `0..1` |
| `mean_reaction_time` | `mmse_results.response_latency` | direct | seconds | `>=0` |
| `reaction_time_variance` | `mmse_results.latency_variability` | direct backend variability metric | seconds | `>=0` |
| `hesitation_duration` | `mmse_results` | `response_latency * (1 - performance_consistency)` | seconds | `>=0` |
| `correction_frequency` | `mmse_results.correction_frequency` | direct | ratio | `0..1` |
| `skip_frequency` | `mmse_results.omission_errors` | omission errors divided by 30 MMSE response opportunities | ratio | `0..1` |
| `confidence_variability` | `mmse_results.performance_consistency` | `1 - performance_consistency` proxy | ratio | `0..1` |
| `completion_time` | `mmse_results.completion_time` | direct | seconds | `>0` |
| `error_recovery_time` | `mmse_results` | `response_latency * correction_frequency` | seconds | `>=0` |
| `immediate_recall_accuracy` | `memory_results.immediate_recall_accuracy` | direct | ratio | `0..1` |
| `delayed_recall_accuracy` | `memory_results.delayed_recall_accuracy` | direct | ratio | `0..1` |
| `recognition_accuracy` | `memory_results.recognition_accuracy` | direct | ratio | `0..1` |
| `recall_decay_rate` | `memory_results.recall_decay_rate` | direct | ratio | `0..1` |
| `recall_latency` | `memory_results.recall_latency` | direct | seconds | `>=0` |
| `omission_errors` | `memory_results.omission_errors` | direct | count | `>=0` |
| `intrusion_errors` | `memory_results.intrusion_errors` | direct | count | `>=0` |
| `sequence_recall_accuracy` | `memory_results.sequence_recall_accuracy` | direct | ratio | `0..1` |
| `retry_frequency` | `memory_results.retry_frequency` | direct | count | `>=0` |
| `memory_consistency_trend` | `memory_results.memory_consistency_trend` | direct | ratio | `0..1` |
| `naming_accuracy` | `boston_naming_results.naming_accuracy` | direct | ratio | `0..1` |
| `response_latency` | `boston_naming_results.mean_response_latency_ms` or `raw_trials.response_latency_ms` | milliseconds to seconds | seconds | `>=0` |
| `semantic_error_frequency` | `boston_naming_results.semantic_errors` | semantic errors divided by 20 scored trials | ratio | `0..1` |
| `phonemic_error_frequency` | `boston_naming_results.phonemic_errors` | phonemic errors divided by 20 scored trials | ratio | `0..1` |
| `cue_dependency_rate` | `boston_naming_results.total_cue_rate` | direct | ratio | `0..1` |
| `no_response_frequency` | `boston_naming_results.omission_errors` | omission errors divided by 20 scored trials | ratio | `0..1` |
| `typing_speaking_speed` | `boston_naming_results.raw_trials` | mean words per second from final transcript and response duration | words/sec | `>=0` |
| `time_per_image` | `boston_naming_results.completion_time_ms` | completion time divided by 20 scored images, then converted to seconds | seconds | `>0` |
| `nback_accuracy` | `nback_results.nback_accuracy` | direct | ratio | `0..1` |
| `false_positive_rate` | `nback_results.false_alarm_rate` | direct semantic alias | ratio | `0..1` |
| `missed_target_rate` | `nback_results.omission_errors` | omission errors divided by estimated target trials from documented 30-40% target ratio over 40 scored trials | ratio | `0..1` |
| `sustained_attention_score` | `nback_results.response_consistency` | direct proxy from backend response consistency | ratio | `0..1` |
| `attention_drift` | `nback_results.fatigue_trend` | absolute fatigue trend magnitude | ratio | `>=0` |
| `idle_time` | `nback_results` | completion time minus estimated active response time using hit and false-alarm activity | seconds | `>=0` |
| `fatigue_progression` | `nback_results.fatigue_trend` | direct semantic alias | delta accuracy | `-1..1` |
| `path_efficiency` | `trail_making_results.path_efficiency` | direct | ratio | `0..1` |
| `sequence_accuracy` | `trail_making_results.sequence_accuracy` | direct | ratio | `0..1` |
| `switching_delay` | `trail_making_results.switching_delay` | direct | milliseconds | `>=0` |
| `backtracking_frequency` | `trail_making_results.backtracking_frequency` | direct | ratio | `>=0` |
| `rule_violation_count` | `trail_making_results.rule_violation_count` | direct | count | `>=0` |
| `cursor_movement_entropy` | `trail_making_results.cursor_movement_entropy` | direct | entropy | `>=0` |
| `trajectory_deviation` | `trail_making_results.trajectory_deviation` | direct | ratio | `>=0` |
| `tremor_jitter_frequency` | `trail_making_results.tremor_jitter_frequency` | direct | events/sec | `>=0` |
