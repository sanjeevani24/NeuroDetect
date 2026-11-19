import { PrimaryButton, SecondaryButton } from "../../components/ui/buttons";

export type RecordingControlState = "idle" | "recording" | "recorded";

interface RecordingControlsProps {
  recordingState: RecordingControlState;
  elapsedSeconds: number;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onRecordAgain: () => void;
  onSubmit: () => void;
  disabled?: boolean;
}

export function RecordingControls({
  recordingState,
  elapsedSeconds,
  onStartRecording,
  onStopRecording,
  onRecordAgain,
  onSubmit,
  disabled = false,
}: RecordingControlsProps) {
  const minutes = Math.floor(elapsedSeconds / 60);
  const seconds = Math.floor(elapsedSeconds % 60);
  const formattedTime = `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;

  return (
    <div className="recording-controls" role="group" aria-label="Speech recording controls">
      {recordingState === "recording" && (
        <div className="recording-status is-active" aria-live="polite">
          <span className="recording-indicator" aria-hidden="true" />
          <span className="recording-label">Recording in progress…</span>
          <span className="recording-timer" aria-label={`Elapsed time: ${formattedTime}`}>
            {formattedTime}
          </span>
        </div>
      )}

      {recordingState === "recorded" && (
        <div className="recording-status is-recorded" aria-live="polite">
          <span className="recorded-badge" aria-hidden="true">✓</span>
          <span className="recording-label">Recording captured ({formattedTime})</span>
        </div>
      )}

      <div className="recording-actions">
        {recordingState === "idle" && (
          <PrimaryButton
            type="button"
            onClick={onStartRecording}
            disabled={disabled}
            className="speech-btn speech-btn--record"
          >
            Start Recording
          </PrimaryButton>
        )}

        {recordingState === "recording" && (
          <PrimaryButton
            type="button"
            onClick={onStopRecording}
            className="speech-btn speech-btn--stop"
          >
            Stop Recording
          </PrimaryButton>
        )}

        {recordingState === "recorded" && (
          <>
            <SecondaryButton
              type="button"
              onClick={onRecordAgain}
              disabled={disabled}
              className="speech-btn speech-btn--retry"
            >
              Record Again
            </SecondaryButton>
            <PrimaryButton
              type="button"
              onClick={onSubmit}
              disabled={disabled}
              className="speech-btn speech-btn--submit"
            >
              Submit Recording
            </PrimaryButton>
          </>
        )}
      </div>
    </div>
  );
}
