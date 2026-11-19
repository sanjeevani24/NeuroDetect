import { useEffect, useRef } from "react";

interface AudioPreviewProps {
  audioUrl: string | null;
  durationSeconds: number;
}

export function AudioPreview({ audioUrl, durationSeconds }: AudioPreviewProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    // Reset playback position if audioUrl changes
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
    }
  }, [audioUrl]);

  if (!audioUrl) return null;

  const minutes = Math.floor(durationSeconds / 60);
  const seconds = Math.floor(durationSeconds % 60);
  const formattedDuration = `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;

  return (
    <div className="audio-preview-card" role="region" aria-label="Recording Preview">
      <div className="audio-preview-header">
        <span className="audio-preview-title">Playback Preview</span>
        <span className="audio-preview-duration">Duration: {formattedDuration}</span>
      </div>
      <audio
        ref={audioRef}
        src={audioUrl}
        controls
        className="audio-preview-player"
        aria-label="Recorded speech playback"
      >
        Your browser does not support the audio element.
      </audio>
      <p className="audio-preview-hint">
        Listen to check clarity and volume before submitting your assessment.
      </p>
    </div>
  );
}
