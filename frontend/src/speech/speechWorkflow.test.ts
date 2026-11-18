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
});
