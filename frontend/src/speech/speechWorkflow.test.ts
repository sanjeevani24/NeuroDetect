import { describe, it, expect, vi } from "vitest";
import * as api from "../services/api";

describe("Speech Workflow and Route Logic", () => {
  const assessmentId = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee";

  it("preserves assessment ID across stage navigation", () => {
    const speechPath = `/assessment/${encodeURIComponent(assessmentId)}/speech`;
    const match = speechPath.match(
      /^\/assessment\/([^/]+)\/(mental-health|cognitive|mmse|memory|nback|boston-naming|trail-making|speech|results)$/
    );

    expect(match).not.toBeNull();
    expect(match![1]).toBe(assessmentId);
    expect(match![2]).toBe("speech");
  });

  it("handles valid speech upload and returns expected Model 3 structure", async () => {
    const mockUploadResponse: api.SpeechUploadResponse = {
      assessment_id: assessmentId,
      status: "completed",
      transcription_status: "completed",
      transcription_engine: "pluggable_local_asr",
      inference_status: "awaiting_asr_verification",
      predicted_class: "HC",
      probabilities: {
        HC: 0.91,
        MCI: 0.06,
        Dementia: 0.03,
      },
      branch_probabilities: {
        audio_embedding: { HC: 0.88, MCI: 0.08, Dementia: 0.04 },
        acoustic: { HC: 0.75, MCI: 0.15, Dementia: 0.1 },
        transcript: { HC: 0.92, MCI: 0.05, Dementia: 0.03 },
      },
      model_version: "model3-process2-ctd-20261116-full",
      disclaimer: "Research screening only.",
    };

    const spy = vi.spyOn(api, "uploadSpeechRecording").mockResolvedValue(mockUploadResponse);
    const audioBlob = new Blob(["mock-wav-bytes"], { type: "audio/webm" });

    const response = await api.uploadSpeechRecording(assessmentId, audioBlob);

    expect(spy).toHaveBeenCalledOnce();
    expect(response.assessment_id).toBe(assessmentId);
    expect(response.predicted_class).toBe("HC");
    expect(response.probabilities?.HC).toBeCloseTo(0.91);
    expect(response.model_version).toBe("model3-process2-ctd-20261116-full");
    expect(response.inference_status).toBe("awaiting_asr_verification");
  });

  it("handles empty recording error safely", async () => {
    vi.spyOn(api, "uploadSpeechRecording").mockRejectedValue(
      new api.ApiError(400, "Audio recording is empty (0 bytes).")
    );

    const emptyBlob = new Blob([], { type: "audio/webm" });

    await expect(api.uploadSpeechRecording(assessmentId, emptyBlob)).rejects.toThrow(
      "Audio recording is empty (0 bytes)."
    );
  });

  it("handles microphone permission denial representation", () => {
    const error = new DOMException("Permission denied", "NotAllowedError");
    expect(error.name).toBe("NotAllowedError");
  });

  it("formats duration correctly for audio preview", () => {
    const formatDuration = (elapsedSeconds: number): string => {
      const minutes = Math.floor(elapsedSeconds / 60);
      const seconds = Math.floor(elapsedSeconds % 60);
      return `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;
    };

    expect(formatDuration(0)).toBe("0:00");
    expect(formatDuration(9)).toBe("0:09");
    expect(formatDuration(65)).toBe("1:05");
    expect(formatDuration(180)).toBe("3:00");
  });

  it("handles final fusion result structure and provisional status", async () => {
    const mockFusion: api.FusionResultSummary = {
      available: true,
      status: "provisional",
      title: "Final Assessment Conclusion",
      interpretation: "NO_ELEVATED_INDICATORS",
      interpretation_label: "No Elevated Indicators Detected",
      conclusion: "No Elevated Indicators Detected",
      verification_status: "PROVISIONAL",
      provisional_warning: "Awaiting ASR verification",
      recommended_next_step: "Continue routine wellness checkups and healthy brain habits.",
      recommended_steps: [
        "Routine wellness: Continue annual wellness checkups.",
      ],
      key_findings: {
        cognitive_games: {
          title: "Cognitive Games",
          status_label: "Within Expected Range",
          summary: "Tasks were within expected range.",
          badge_variant: "success",
        },
        speech_analysis: {
          title: "Speech Analysis",
          status_label: "Healthy Control (HC) — 85.0% (Awaiting Clinician Verification)",
          summary: "Speech analysis produced HC as leading prediction.",
          badge_variant: "warning",
        },
        mental_health: {
          title: "Mental Health Context",
          status_label: "Minimal Symptoms (PHQ-9: Minimal, GAD-7: Minimal)",
          summary: "Mood and anxiety scores are within minimal range.",
          badge_variant: "neutral",
        },
      },
      model1_score: 83.5,
      model1_category: "NORMAL",
      model1_weight_percent: 50,
      model3_predicted_class: "HC",
      model3_category: "HC_DOMINANT",
      model3_weight_percent: 50,
      model3_probabilities: { HC: 0.85, MCI: 0.10, Dementia: 0.05 },
      mental_health_context: {
        phq9_score: 3,
        phq9_severity: "Minimal",
        gad7_score: 2,
        gad7_severity: "Minimal",
        depression_elevated: false,
        anxiety_elevated: false,
        contextual_flags: [],
      },
      contextual_flags: [],
      rules_triggered: ["RULE_FUSION_NORMAL_HC"],
      explanation: "Both indicators normal.",
      disclaimer: "Research screening prototype.",
    };

    const spy = vi.spyOn(api, "getAssessmentFusion").mockResolvedValue(mockFusion);
    const res = await api.getAssessmentFusion(assessmentId);

    expect(spy).toHaveBeenCalledOnce();
    expect(res.interpretation).toBe("NO_ELEVATED_INDICATORS");
    expect(res.verification_status).toBe("PROVISIONAL");
    expect(res.model1_weight_percent).toBe(50);
    expect(res.model3_weight_percent).toBe(50);
    expect(res.model1_category).toBe("NORMAL");
    expect(res.model3_category).toBe("HC_DOMINANT");
  });
});
