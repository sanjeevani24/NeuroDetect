import { useCallback, useEffect, useRef, useState } from "react";
import { LoadingState } from "../components/ui/States";
import { PrimaryButton } from "../components/ui/buttons";
import { ApiError } from "../services/api";
import { AudioPreview } from "./components/AudioPreview";
import { RecordingControls, type RecordingControlState } from "./components/RecordingControls";
import { SpeechInstructions } from "./components/SpeechInstructions";
import { submitSpeechRecording } from "./services/speechService";
import "./SpeechAssessment.css";

interface SpeechAssessmentProps {
  assessmentId: string;
  onComplete: () => void;
}

type RecordingState = "idle" | "recording" | "recorded" | "submitting" | "completed" | "error";

export function SpeechAssessment({ assessmentId, onComplete }: SpeechAssessmentProps) {
  const [recordingState, setRecordingState] = useState<RecordingState>("idle");
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [permissionDenied, setPermissionDenied] = useState<boolean>(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<number | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const mimeTypeRef = useRef<string>("audio/webm");

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        window.clearInterval(timerRef.current);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  const selectSupportedMimeType = (): string => {
    if (typeof MediaRecorder === "undefined") return "audio/webm";
    const candidates = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/ogg;codecs=opus",
      "audio/mp4",
      "audio/wav",
    ];
    for (const mime of candidates) {
      if (MediaRecorder.isTypeSupported(mime)) {
        return mime;
      }
    }
    return "";
  };

  const startRecording = async () => {
    setErrorMessage(null);
    setPermissionDenied(false);

    // Clean up any existing audio URL
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setAudioBlob(null);
    chunksRef.current = [];

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Your browser does not support microphone recording.");
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      streamRef.current = stream;
      const mime = selectSupportedMimeType();
      mimeTypeRef.current = mime;

      const recorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event: BlobEvent) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const combinedBlob = new Blob(chunksRef.current, {
          type: mimeTypeRef.current || "audio/webm",
        });
        const url = URL.createObjectURL(combinedBlob);
        setAudioBlob(combinedBlob);
        setAudioUrl(url);
        setRecordingState("recorded");

        // Release microphone tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }
      };

      recorder.start(250); // Slice every 250ms
      setRecordingState("recording");
      setElapsedSeconds(0);

      timerRef.current = window.setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err: unknown) {
      if (err instanceof DOMException && (err.name === "NotAllowedError" || err.name === "PermissionDeniedError")) {
        setPermissionDenied(true);
        setErrorMessage("Microphone permission was denied. Please allow microphone access in your browser settings to record your speech.");
      } else if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Unable to access microphone. Please check your audio device settings.");
      }
      setRecordingState("error");
    }
  };

  const stopRecording = useCallback(() => {
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const handleRecordAgain = () => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setAudioBlob(null);
    setElapsedSeconds(0);
    setErrorMessage(null);
    setRecordingState("idle");
  };

  const handleSubmit = async () => {
    if (!audioBlob) return;
    if (recordingState === "submitting") return; // Prevent duplicate submission

    setRecordingState("submitting");
    setErrorMessage(null);

    const extension = mimeTypeRef.current.includes("mp4")
      ? "mp4"
      : mimeTypeRef.current.includes("ogg")
      ? "ogg"
      : mimeTypeRef.current.includes("wav")
      ? "wav"
      : "webm";
    const filename = `speech_${assessmentId}.${extension}`;

    try {
      await submitSpeechRecording(assessmentId, audioBlob, filename);
      setRecordingState("completed");
      // Advance to results
      onComplete();
    } catch (err: unknown) {
      setRecordingState("error");
      if (err instanceof ApiError) {
        setErrorMessage(typeof err.detail === "string" ? err.detail : "Speech analysis failed. Please try again.");
      } else if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to upload recording. Please verify your connection and try again.");
      }
    }
  };

  if (recordingState === "submitting") {
    return (
      <div className="page-stack">
        <LoadingState
          title="Processing speech assessment…"
          message="Extracting audio features, transcribing speech, and calculating Model 3 cognitive indicators. This may take a few moments."
        />
      </div>
    );
  }

  return (
    <div className="page-stack speech-assessment-page">
      <SpeechInstructions />

      <section className="hero-card hero-card--section speech-recorder-card">
        {permissionDenied && (
          <div className="speech-error-banner" role="alert">
            <strong>Microphone Access Required:</strong> {errorMessage}
          </div>
        )}

        {errorMessage && !permissionDenied && (
          <div className="speech-error-banner" role="alert">
            <strong>Recording Error:</strong> {errorMessage}
          </div>
        )}

        {audioUrl && (
          <AudioPreview audioUrl={audioUrl} durationSeconds={elapsedSeconds} />
        )}

        {(() => {
          const controlState: RecordingControlState =
            recordingState === "recording"
              ? "recording"
              : recordingState === "recorded"
              ? "recorded"
              : "idle";
          return (
            <RecordingControls
              recordingState={controlState}
              elapsedSeconds={elapsedSeconds}
              onStartRecording={startRecording}
              onStopRecording={stopRecording}
              onRecordAgain={handleRecordAgain}
              onSubmit={handleSubmit}
            />
          );
        })()}

        {recordingState === "error" && (
          <div className="speech-retry-action">
            <PrimaryButton type="button" onClick={handleRecordAgain}>
              Try Again
            </PrimaryButton>
          </div>
        )}
      </section>
    </div>
  );
}
