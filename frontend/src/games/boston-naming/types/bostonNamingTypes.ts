export type BostonNamingPhase = "INTRO" | "PRACTICE" | "READY" | "RUNNING" | "COMPLETION";

export type DifficultyLevel = "EASY" | "MEDIUM" | "HARD";

export type RecordingStatus = "SUCCESS" | "FAILED" | "DENIED" | "NOT_SUPPORTED";
export type TranscriptionStatus = "SUCCESS" | "FAILED" | "UNAVAILABLE";

export interface BostonNamingStimulus {
  stimulusId: string;
  order: number;
  display: string;
  alt: string;
  canonicalName: string;
  acceptedAnswers: string[];
  category: string;
  difficulty: DifficultyLevel;
  semanticCue: string;
  phonemicCue: string;
}

export interface TrialCapture {
  transcript: string;
  initialResponse?: string | null;
  finalResponse?: string | null;
  transcriptConfidence?: number | null;
  transcriptionStatus: TranscriptionStatus;
  recordingStatus: RecordingStatus;
  responseDurationMs?: number | null;
  responseLatencyMs?: number | null;
  hesitationDurationMs?: number | null;
  selfCorrected?: boolean | null;
  selfCorrectionLatencyMs?: number | null;
  semanticCueUsed: boolean;
  phonemicCueUsed: boolean;
  timeout: boolean;
}
