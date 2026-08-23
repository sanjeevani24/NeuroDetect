interface BostonNamingProgressProps {
  currentTrial: number;
  totalTrials: number;
}

export function BostonNamingProgress({ currentTrial, totalTrials }: BostonNamingProgressProps) {
  return (
    <div className="boston-naming__progress" aria-label="Boston Naming progress">
      <span>{String(currentTrial + 1).padStart(2, "0")} / {String(totalTrials).padStart(2, "0")}</span>
    </div>
  );
}
