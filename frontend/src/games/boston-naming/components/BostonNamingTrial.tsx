import { useEffect, useMemo, useRef, useState } from "react";

import { PrimaryButton, SecondaryButton } from "../../../components/ui/buttons";
import {
  INITIAL_RESPONSE_WINDOW_MS,
  MAX_RESPONSE_WINDOW_MS,
  PHONEMIC_CUE_DELAY_MS,
} from "../config/bostonNamingConfig";
import type { BostonNamingStimulus, TrialCapture } from "../types/bostonNamingTypes";
import { latencyMs, monotonicNowMs } from "../utils/timing";

type SpeechRecognitionLike = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  start(): void;
  stop(): void;
};

type SpeechRecognitionCtor = new () => SpeechRecognitionLike;

interface SpeechRecognitionEventLike {
  results: ArrayLike<ArrayLike<{ transcript: string; confidence: number }>>;
}

interface BostonNamingTrialProps {
  stimulus: BostonNamingStimulus;
  isPractice: boolean;
  stream: MediaStream;
  onPresented: (timestampMs: number) => void;
  onCuePresented: (cueType: "semantic" | "phonemic", timestampMs: number) => void;
  onTimeout: (timestampMs: number) => void;
  onCaptureComplete: (capture: TrialCapture, timestampMs: number) => void;
}

function detectSelfCorrection(value: string) {
  const marker = value.match(/\b(no|sorry)\b/i);
  return marker ? marker.index ?? null : null;
}

export function BostonNamingTrial({
  stimulus,
  isPractice,
  stream,
  onPresented,
  onCuePresented,
  onTimeout,
  onCaptureComplete,
}: BostonNamingTrialProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingError, setRecordingError] = useState<string | null>(null);
  const [showSemanticCue, setShowSemanticCue] = useState(false);
  const [showPhonemicCue, setShowPhonemicCue] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [draftTranscript, setDraftTranscript] = useState("");
  const [transcriptConfidence, setTranscriptConfidence] = useState<number | null>(null);
  const [transcriptionStatus, setTranscriptionStatus] = useState<TrialCapture["transcriptionStatus"]>("UNAVAILABLE");
  const [recordingStatus, setRecordingStatus] = useState<TrialCapture["recordingStatus"]>("SUCCESS");
  const [responseStartedAt, setResponseStartedAt] = useState<number | null>(null);
  const [responseStoppedAt, setResponseStoppedAt] = useState<number | null>(null);
  const [presentedAt, setPresentedAt] = useState<number | null>(null);
  const [finished, setFinished] = useState(false);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const speechRef = useRef<SpeechRecognitionLike | null>(null);
  const semanticCueAtRef = useRef<number | null>(null);
  const phonemicCueAtRef = useRef<number | null>(null);

  const speechRecognitionCtor = useMemo(() => {
    const maybeWindow = window as Window & {
      SpeechRecognition?: SpeechRecognitionCtor;
      webkitSpeechRecognition?: SpeechRecognitionCtor;
    };
    return maybeWindow.SpeechRecognition ?? maybeWindow.webkitSpeechRecognition ?? null;
  }, []);

  useEffect(() => {
    const now = monotonicNowMs();
    setPresentedAt(now);
    onPresented(now);

    const semanticTimer = window.setTimeout(() => {
      const ts = monotonicNowMs();
      semanticCueAtRef.current = ts;
      setShowSemanticCue(true);
      onCuePresented("semantic", ts);
    }, INITIAL_RESPONSE_WINDOW_MS);

    const phonemicTimer = window.setTimeout(() => {
      const ts = monotonicNowMs();
      phonemicCueAtRef.current = ts;
      setShowPhonemicCue(true);
      onCuePresented("phonemic", ts);
    }, INITIAL_RESPONSE_WINDOW_MS + PHONEMIC_CUE_DELAY_MS);

    const timeoutTimer = window.setTimeout(() => {
      const ts = monotonicNowMs();
      onTimeout(ts);
      void stopRecording(true);
    }, MAX_RESPONSE_WINDOW_MS);

    void startRecording();

    return () => {
      window.clearTimeout(semanticTimer);
      window.clearTimeout(phonemicTimer);
      window.clearTimeout(timeoutTimer);
      speechRef.current?.stop();
      if (recorderRef.current && recorderRef.current.state !== "inactive") {
        recorderRef.current.stop();
      }
    };
  }, []);

  async function startRecording() {
    try {
      const mediaRecorder = new MediaRecorder(stream);
      recorderRef.current = mediaRecorder;
      const startedAt = monotonicNowMs();
      setResponseStartedAt(startedAt);
      setIsRecording(true);
      setRecordingError(null);
      mediaRecorder.start();
      if (speechRecognitionCtor) {
        const speech = new speechRecognitionCtor();
        speech.continuous = true;
        speech.interimResults = true;
        speech.lang = "en-US";
        speech.onresult = (event) => {
          const lastResult = event.results[event.results.length - 1];
          const candidate = lastResult?.[0];
          if (candidate?.transcript) {
            setTranscript(candidate.transcript.trim());
            setDraftTranscript(candidate.transcript.trim());
            setTranscriptConfidence(candidate.confidence ?? null);
            setTranscriptionStatus("SUCCESS");
          }
        };
        speech.onerror = () => {
          setTranscriptionStatus("FAILED");
        };
        speech.start();
        speechRef.current = speech;
      } else {
        setTranscriptionStatus("UNAVAILABLE");
      }
    } catch (error) {
      setRecordingStatus("FAILED");
      setRecordingError("Microphone recording could not be started for this trial.");
    }
  }

  async function stopRecording(timeout = false) {
    if (finished) return;
    setFinished(true);
    speechRef.current?.stop();
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
    const stoppedAt = monotonicNowMs();
    setResponseStoppedAt(stoppedAt);
    setIsRecording(false);
    const finalTranscript = draftTranscript.trim() || transcript.trim();
    const selfCorrectionIndex = detectSelfCorrection(finalTranscript);
    onCaptureComplete(
      {
        transcript: finalTranscript,
        initialResponse: selfCorrectionIndex !== null ? finalTranscript.slice(0, selfCorrectionIndex).trim() : finalTranscript || null,
        finalResponse: finalTranscript || null,
        transcriptConfidence,
        transcriptionStatus,
        recordingStatus,
        responseDurationMs: responseStartedAt !== null ? latencyMs(responseStartedAt, stoppedAt) : null,
        responseLatencyMs: presentedAt !== null && responseStartedAt !== null ? latencyMs(presentedAt, responseStartedAt) : null,
        hesitationDurationMs: presentedAt !== null && responseStartedAt !== null ? latencyMs(presentedAt, responseStartedAt) : null,
        selfCorrected: selfCorrectionIndex !== null,
        selfCorrectionLatencyMs: selfCorrectionIndex !== null && responseStartedAt !== null ? latencyMs(responseStartedAt, stoppedAt) : null,
        semanticCueUsed: showSemanticCue,
        phonemicCueUsed: showPhonemicCue,
        timeout,
      },
      stoppedAt
    );
  }

  return (
    <section className="boston-naming__trial-card">
      <div className="boston-naming__stimulus" role="img" aria-label={stimulus.alt}>
        <span aria-hidden="true">{stimulus.display}</span>
      </div>
      <div className="boston-naming__trial-meta">
        <p className="boston-naming__eyebrow">{isPractice ? "Practice" : stimulus.difficulty}</p>
        <h3>Name this object.</h3>
        <p className="boston-naming__hint">
          {isRecording ? "Recording in progress. Stop when your spoken answer is complete." : "Review the transcript if needed, then continue."}
        </p>
      </div>

      {showSemanticCue ? <p className="boston-naming__cue">Semantic cue: {stimulus.semanticCue}</p> : null}
      {showPhonemicCue ? <p className="boston-naming__cue">Phonemic cue: {stimulus.phonemicCue}</p> : null}

      <label className="boston-naming__label" htmlFor={`transcript-${stimulus.stimulusId}`}>
        Transcript helper
      </label>
      <textarea
        id={`transcript-${stimulus.stimulusId}`}
        className="boston-naming__textarea"
        value={draftTranscript}
        onChange={(event) => setDraftTranscript(event.target.value)}
        placeholder="If speech recognition is unavailable, type the spoken answer here so the backend can classify it."
      />

      <div className="boston-naming__actions">
        {isRecording ? (
          <PrimaryButton type="button" onClick={() => void stopRecording(false)}>
            Stop Recording
          </PrimaryButton>
        ) : (
          <SecondaryButton type="button" onClick={() => void stopRecording(false)}>
            Continue
          </SecondaryButton>
        )}
      </div>

      {recordingError ? <p className="boston-naming__error">{recordingError}</p> : null}
      {responseStoppedAt ? (
        <p className="boston-naming__hint">
          Recording stopped. {transcriptionStatus === "SUCCESS" ? "You can edit the transcript before continuing." : "Speech recognition was not available for this response."}
        </p>
      ) : null}
    </section>
  );
}
