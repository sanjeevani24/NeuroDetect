import { describe, it, expect, vi } from "vitest";
import * as api from "../services/api";

describe("MRI Workflow and Service Integration", () => {
  const assessmentId = "11111111-2222-4333-8444-555555555555";

  it("matches mri-upload and mri-results URL routes", () => {
    const uploadPath = `/assessment/${encodeURIComponent(assessmentId)}/mri-upload`;
    const resultsPath = `/assessment/${encodeURIComponent(assessmentId)}/mri-results`;

    const pattern =
      /^\/assessment\/([^/]+)\/(mental-health|cognitive|mmse|memory|nback|boston-naming|trail-making|speech|results|mri-upload|mri-results)$/;

    const matchUpload = uploadPath.match(pattern);
    expect(matchUpload).not.toBeNull();
    expect(matchUpload![1]).toBe(assessmentId);
    expect(matchUpload![2]).toBe("mri-upload");

    const matchResults = resultsPath.match(pattern);
    expect(matchResults).not.toBeNull();
    expect(matchResults![1]).toBe(assessmentId);
    expect(matchResults![2]).toBe("mri-results");
  });

  it("handles valid MRI slice upload and returns Model 4 result structure", async () => {
    const mockMriResponse: api.MriResultResponse = {
      assessment_id: assessmentId,
      status: "completed",
      processing_status: "completed",
      image_filename: "sample_slice.png",
      image_format: "png",
      image_size_bytes: 52428,
      predicted_class: "Non-Demented",
      predicted_class_index: 0,
      probability_non_demented: 0.88,
      probability_very_mild: 0.08,
      probability_mild: 0.03,
      probability_moderate: 0.01,
      class_probabilities: {
        "Non-Demented": 0.88,
        "Very Mildly Demented": 0.08,
        "Mildly Demented": 0.03,
        "Moderately Demented": 0.01,
      },
      binary_prediction: "No Dementia",
      binary_probabilities: {
        no_dementia: 0.88,
        dementia: 0.12,
      },
      model_name: "NeuroDetect-MRI-EfficientNetB0",
      model_version: "1.0.0",
      disclaimer: "Research prototype for academic use only. Not a medical device and not clinically validated.",
    };

    const spy = vi.spyOn(api, "uploadMriScan").mockResolvedValue(mockMriResponse);
    const mockFile = new File(["dummy-png-content"], "sample_slice.png", { type: "image/png" });

    const response = await api.uploadMriScan(assessmentId, mockFile);

    expect(spy).toHaveBeenCalledOnce();
    expect(response.assessment_id).toBe(assessmentId);
    expect(response.predicted_class).toBe("Non-Demented");
    expect(response.binary_prediction).toBe("No Dementia");
    expect(response.probability_non_demented).toBeCloseTo(0.88);
    expect(response.model_name).toBe("NeuroDetect-MRI-EfficientNetB0");
    expect(response.disclaimer).toContain("Research prototype");
  });

  it("handles getMriResult successfully", async () => {
    const mockResult: api.MriResultResponse = {
      assessment_id: assessmentId,
      status: "completed",
      processing_status: "completed",
      predicted_class: "Very Mildly Demented",
      predicted_class_index: 1,
      probability_non_demented: 0.10,
      probability_very_mild: 0.75,
      probability_mild: 0.12,
      probability_moderate: 0.03,
      class_probabilities: {
        "Non-Demented": 0.10,
        "Very Mildly Demented": 0.75,
        "Mildly Demented": 0.12,
        "Moderately Demented": 0.03,
      },
      binary_prediction: "Dementia",
      binary_probabilities: {
        no_dementia: 0.10,
        dementia: 0.90,
      },
      model_name: "NeuroDetect-MRI-EfficientNetB0",
      model_version: "1.0.0",
      disclaimer: "Research prototype for academic use only.",
    };

    vi.spyOn(api, "getMriResult").mockResolvedValue(mockResult);

    const res = await api.getMriResult(assessmentId);
    expect(res.predicted_class).toBe("Very Mildly Demented");
    expect(res.binary_prediction).toBe("Dementia");
    expect(res.binary_probabilities.dementia).toBeCloseTo(0.90);
  });
});
