import type { BostonNamingTelemetryEvent } from "../games/boston-naming/telemetry/bostonNamingEvents";
import type { MemoryEvent } from "../games/memory/telemetry/eventTypes";
import type { ConfidenceRatings } from "../games/memory/types/memoryTypes";
import type { MMSEEvent } from "../games/mmse/telemetry/mmseEvents";
import type { NBackTelemetryEvent } from "../games/nback/telemetry/nbackEvents";
import type { TrailMakingTelemetryEvent, TrailNodeLayout } from "../games/trail-making/types/trailMakingTypes";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface AssessmentSession {
  patient_id: string;
  assessment_id: string;
  full_name: string;
  age: number;
  sex: string;
  education_years: number;
  current_stage:
    | "PATIENT_INFO"
    | "PHQ_GAD"
    | "COGNITIVE"
    | "MMSE"
    | "MEMORY"
    | "NBACK"
    | "BOSTON_NAMING"
    | "TRAIL_MAKING"
    | "SPEECH"
    | "RESULTS";
  completed_stages: string[];
}

export interface CreateAssessmentSessionPayload {
  full_name: string;
  age: number;
  sex: string;
  education_years: number;
}

export interface PHQ9Answers {
  q1: number;
  q2: number;
  q3: number;
  q4: number;
  q5: number;
  q6: number;
  q7: number;
  q8: number;
  q9: number;
}

export interface GAD7Answers {
  q1: number;
  q2: number;
  q3: number;
  q4: number;
  q5: number;
  q6: number;
  q7: number;
}

export interface MentalHealthCompletionPayload {
  phq9: PHQ9Answers;
  gad7: GAD7Answers;
}

export interface MentalHealthScore {
  total_score: number;
  severity: string;
  evaluation_cutoff_met: boolean;
}

export interface MentalHealthCompletionResult {
  assessment_id: string;
  status: "completed" | "already_completed";
  phq9: MentalHealthScore;
  gad7: MentalHealthScore;
}

export interface MemoryCompletionPayload {
  events: MemoryEvent[];
  confidence: Required<ConfidenceRatings>;
}

export interface MemoryFeatureSet {
  immediate_recall_accuracy: number;
  delayed_recall_accuracy: number;
  recognition_accuracy: number;
  recall_decay_rate: number;
  recall_latency: number;
  omission_errors: number;
  intrusion_errors: number;
  sequence_recall_accuracy: number;
  hesitation_duration: number;
  retry_frequency: number;
  confidence_variability: number;
  completion_time: number;
  memory_consistency_trend: number;
}

export interface MemoryGameResult {
  assessment_id: string;
  game: "memory";
  status: string;
  features: MemoryFeatureSet;
}

export interface MMSECompletionPayload {
  events: MMSEEvent[];
}

export interface MMSEFeatureSet {
  orientation_accuracy: number;
  registration_accuracy: number;
  attention_accuracy: number;
  serial7_accuracy: number;
  delayed_recall_accuracy: number;
  language_accuracy: number;
  command_following_accuracy: number;
  response_latency: number;
  latency_variability: number;
  omission_errors: number;
  intrusion_errors: number;
  correction_frequency: number;
  completion_time: number;
  performance_consistency: number;
}

export interface MMSEGameResult {
  assessment_id: string;
  game: "mmse";
  status: string;
  features: MMSEFeatureSet;
}

export interface NBackCompletionPayload {
  events: NBackTelemetryEvent[];
}

export interface NBackFeatureSet {
  nback_accuracy: number;
  hit_rate: number;
  false_alarm_rate: number;
  sensitivity: number;
  response_latency: number;
  latency_variability: number;
  omission_errors: number;
  commission_errors: number;
  d_prime: number;
  response_consistency: number;
  fatigue_trend: number;
  completion_time: number;
}

export interface NBackGameResult {
  assessment_id: string;
  game: "nback";
  status: string;
  features: NBackFeatureSet;
}

export interface BostonNamingCompletionPayload {
  events: BostonNamingTelemetryEvent[];
}

export interface BostonNamingFeatureSet {
  naming_accuracy: number;
  uncued_accuracy: number;
  cued_accuracy: number | null;
  semantic_cue_rate: number;
  phonemic_cue_rate: number;
  total_cue_rate: number;
  mean_response_latency_ms: number | null;
  median_response_latency_ms: number | null;
  response_latency_std_ms: number;
  hesitation_duration_ms: number;
  hesitation_variability_ms: number;
  omission_errors: number;
  semantic_errors: number;
  phonemic_errors: number;
  visual_errors: number;
  unrelated_errors: number;
  ambiguous_errors: number;
  self_correction_rate: number;
  successful_self_correction_rate: number | null;
  mean_response_duration_ms: number | null;
  response_duration_std_ms: number;
  correct_response_latency_ms: number | null;
  incorrect_response_latency_ms: number | null;
  difficulty_adjusted_accuracy: number;
  easy_accuracy: number | null;
  medium_accuracy: number | null;
  hard_accuracy: number | null;
  naming_consistency: number;
  fatigue_trend: number;
  completion_time_ms: number;
  raw_trials: Array<Record<string, unknown>>;
}

export interface BostonNamingGameResult {
  assessment_id: string;
  game: "boston_naming";
  status: string;
  features: BostonNamingFeatureSet;
}

export interface TrailMakingCompletionPayload {
  game_session_id: string;
  node_layout: TrailNodeLayout[];
  events: TrailMakingTelemetryEvent[];
}

export interface TrailMakingFeatureSet {
  path_efficiency: number;
  sequence_accuracy: number;
  switching_delay: number;
  backtracking_frequency: number;
  rule_violation_count: number;
  cursor_movement_entropy: number;
  trajectory_deviation: number;
  tremor_jitter_frequency: number;
  total_completion_time: number;
  total_error_count: number;
  correct_target_count: number;
  mean_reaction_time: number | null;
  median_reaction_time: number | null;
  reaction_time_variance: number | null;
  hesitation_duration: number;
  error_recovery_time: number | null;
  first_half_time: number | null;
  second_half_time: number | null;
  time_degradation_ratio: number | null;
  switch_count: number;
  correct_switch_count: number;
  incorrect_switch_count: number;
  backtracking_distance: number;
  trajectory_length: number;
  ideal_path_length: number;
  correction_count: number;
  idle_time: number;
  layout: Array<Record<string, unknown>>;
}

export interface TrailMakingGameResult {
  assessment_id: string;
  game: "trail_making";
  status: string;
  features: TrailMakingFeatureSet;
}

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : "Request failed");
    this.status = status;
    this.detail = detail;
  }
}

async function parseApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail: unknown = null;
    try {
      const body = await response.json();
      detail = body.detail ?? body;
    } catch {
      detail = await response.text();
    }
    throw new ApiError(response.status, detail);
  }

  return response.json();
}

async function requestJson<T>(input: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(input, init);
  } catch {
    throw new ApiError(
      0,
      "Could not reach the NeuroDetect API. Confirm the FastAPI server is running and VITE_API_BASE_URL is correct."
    );
  }

  return parseApiResponse<T>(response);
}

export function createAssessmentSession(payload: CreateAssessmentSessionPayload): Promise<AssessmentSession> {
  return requestJson<AssessmentSession>(`${API_BASE_URL}/api/assessments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getAssessmentSession(assessmentId: string): Promise<AssessmentSession> {
  return requestJson<AssessmentSession>(`${API_BASE_URL}/api/assessments/${encodeURIComponent(assessmentId)}`);
}

export function completeMentalHealthScreening(
  assessmentId: string,
  payload: MentalHealthCompletionPayload
): Promise<MentalHealthCompletionResult> {
  return requestJson<MentalHealthCompletionResult>(
    `${API_BASE_URL}/api/assessments/${encodeURIComponent(assessmentId)}/mental-health/complete`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );
}

export function completeMemoryGame(
  assessmentId: string,
  payload: MemoryCompletionPayload
): Promise<MemoryGameResult> {
  return requestJson<MemoryGameResult>(
    `${API_BASE_URL}/api/assessments/${encodeURIComponent(assessmentId)}/games/memory/complete`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );
}

export function completeMMSEGame(
  assessmentId: string,
  payload: MMSECompletionPayload
): Promise<MMSEGameResult> {
  return requestJson<MMSEGameResult>(
    `${API_BASE_URL}/api/assessments/${encodeURIComponent(assessmentId)}/games/mmse/complete`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );
}

export function completeNBackGame(
  assessmentId: string,
  payload: NBackCompletionPayload
): Promise<NBackGameResult> {
  return requestJson<NBackGameResult>(
    `${API_BASE_URL}/api/assessments/${encodeURIComponent(assessmentId)}/games/nback/complete`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );
}

export function completeBostonNamingGame(
  assessmentId: string,
  payload: BostonNamingCompletionPayload
): Promise<BostonNamingGameResult> {
  return requestJson<BostonNamingGameResult>(
    `${API_BASE_URL}/api/assessments/${encodeURIComponent(assessmentId)}/games/boston-naming/complete`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );
}

export function completeTrailMakingGame(
  assessmentId: string,
  payload: TrailMakingCompletionPayload
): Promise<TrailMakingGameResult> {
  return requestJson<TrailMakingGameResult>(
    `${API_BASE_URL}/api/assessments/${encodeURIComponent(assessmentId)}/games/trail-making/complete`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );
}
