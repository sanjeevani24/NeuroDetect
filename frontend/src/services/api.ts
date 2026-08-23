import type { MemoryEvent } from "../games/memory/telemetry/eventTypes";
import type { ConfidenceRatings } from "../games/memory/types/memoryTypes";
import type { MMSEEvent } from "../games/mmse/telemetry/mmseEvents";
import type { NBackTelemetryEvent } from "../games/nback/telemetry/nbackEvents";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface AssessmentSession {
  patient_id: string;
  assessment_id: string;
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

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : "Request failed");
    this.status = status;
    this.detail = detail;
  }
}

export async function createAssessmentSession(): Promise<AssessmentSession> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/assessments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    throw new ApiError(
      0,
      "Could not reach the NeuroDetect API. Confirm the FastAPI server is running and VITE_API_BASE_URL is correct."
    );
  }

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

/**
 * The frontend API service does not know how features are calculated — it
 * only sends raw telemetry + confidence and returns whatever the backend
 * computed and persisted.
 */
export async function completeMemoryGame(
  assessmentId: string,
  payload: MemoryCompletionPayload
): Promise<MemoryGameResult> {
  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/api/assessments/${encodeURIComponent(assessmentId)}/games/memory/complete`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    );
  } catch (error) {
    throw new ApiError(
      0,
      "Could not reach the NeuroDetect API. Confirm the FastAPI server is running and VITE_API_BASE_URL is correct."
    );
  }

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

export async function completeMMSEGame(
  assessmentId: string,
  payload: MMSECompletionPayload
): Promise<MMSEGameResult> {
  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/api/assessments/${encodeURIComponent(assessmentId)}/games/mmse/complete`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    );
  } catch (error) {
    throw new ApiError(
      0,
      "Could not reach the NeuroDetect API. Confirm the FastAPI server is running and VITE_API_BASE_URL is correct."
    );
  }

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

export async function completeNBackGame(
  assessmentId: string,
  payload: NBackCompletionPayload
): Promise<NBackGameResult> {
  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/api/assessments/${encodeURIComponent(assessmentId)}/games/nback/complete`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    );
  } catch (error) {
    throw new ApiError(
      0,
      "Could not reach the NeuroDetect API. Confirm the FastAPI server is running and VITE_API_BASE_URL is correct."
    );
  }

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
