interface TrailMakingProgressProps {
  current: number;
  total: number;
  elapsedMs: number;
}

function formatSeconds(ms: number) {
  return `${(ms / 1000).toFixed(1)}s`;
}

export function TrailMakingProgress({ current, total, elapsedMs }: TrailMakingProgressProps) {
  return (
    <div className="trail-progress">
      <span className="trail-progress__pill">{current} / {total}</span>
      <span className="trail-progress__pill">{formatSeconds(elapsedMs)}</span>
    </div>
  );
}
