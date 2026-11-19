import {
  uploadSpeechRecording,
  getSpeechResult,
  type SpeechUploadResponse,
  type SpeechResultResponse,
} from "../../services/api";

export async function submitSpeechRecording(
  assessmentId: string,
  audioBlob: Blob,
  filename?: string
): Promise<SpeechUploadResponse> {
  return uploadSpeechRecording(assessmentId, audioBlob, filename);
}

export async function fetchSpeechResult(
  assessmentId: string
): Promise<SpeechResultResponse> {
  return getSpeechResult(assessmentId);
}
