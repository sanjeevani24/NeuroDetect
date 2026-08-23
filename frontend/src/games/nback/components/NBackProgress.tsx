interface Props {
  currentTrial: number; // 0-indexed
  totalTrials: number;
}

export function NBackProgress({ currentTrial, totalTrials }: Props): JSX.Element {
  const pct = totalTrials > 0 ? Math.round(((currentTrial + 1) / totalTrials) * 100) : 0;
  return (
    <div className="nback-progress" aria-label="Task progress">
      <div className="nback-progress-track">
        <div className="nback-progress-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="nback-progress-label">
        Trial {Math.min(currentTrial + 1, totalTrials)} of {totalTrials}
      </span>
    </div>
  );
}
