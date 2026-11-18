import { describe, it, expect, vi, beforeEach } from "vitest";
import { submitSpeechRecording, fetchSpeechResult } from "./services/speechService";
import * as api from "../services/api";

describe("speechService", () => {
  const assessmentId = "12345678-1234-4234-8234-123456789abc";

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("calls uploadSpeechRecording with correct parameters", async () => {
    const mockResponse: api.SpeechUploadResponse = {
      assessment_id: assessmentId,
      status: "completed",
      transcription_status: "completed",
      transcription_engine: "local_whisper_base",
      inference_status: "awaiting_asr_verification",
      predicted_class: "HC",
      probabilities: { HC: 0.85, MCI: 0.1, Dementia: 0.05 },
      model_version: "model3-process2-ctd-20261116-full",
      disclaimer: "Test disclaimer",
    };

    const spy = vi.spyOn(api, "uploadSpeechRecording").mockResolvedValue(mockResponse);
    const blob = new Blob(["fake audio"], { type: "audio/webm" });

    const result = await submitSpeechRecording(assessmentId, blob, "test.webm");

    expect(spy).toHaveBeenCalledWith(assessmentId, blob, "test.webm");
    expect(result.status).toBe("completed");
    expect(result.predicted_class).toBe("HC");
  });

  it("calls getSpeechResult with correct assessment ID", async () => {
    const mockResult: api.SpeechResultResponse = {
      assessment_id: assessmentId,
      status: "completed",
      transcription_status: "completed",
      transcription_engine: "local_whisper_base",
      inference_status: "awaiting_asr_verification",
      predicted_class: "MCI",
      hc_probability: 0.2,
      mci_probability: 0.7,
      dementia_probability: 0.1,
      model_version: "model3-process2-ctd-20261116-full",
      disclaimer: "Test disclaimer",
    };

    const spy = vi.spyOn(api, "getSpeechResult").mockResolvedValue(mockResult);

    const result = await fetchSpeechResult(assessmentId);

    expect(spy).toHaveBeenCalledWith(assessmentId);
    expect(result.predicted_class).toBe("MCI");
    expect(result.mci_probability).toBe(0.7);
  });
});
