export type AssessmentStage = "mmse" | "memory" | "nback" | "naming" | "trail" | "complete";

const STAGE_LABELS: Record<AssessmentStage, string> = {
  mmse: "MMSE",
  memory: "Memory Recall",
  nback: "N-Back",
  naming: "Boston Naming",
  trail: "Trail Making",
  complete: "Complete",
};

const STAGES: AssessmentStage[] = ["mmse", "memory", "nback", "naming", "trail"];

interface AssessmentProgressProps {
  currentStage: AssessmentStage;
  completedStages?: AssessmentStage[];
}

export function AssessmentProgress({
  currentStage,
  completedStages = [],
}: AssessmentProgressProps) {
  const currentIndex = currentStage === "complete" ? STAGES.length : STAGES.indexOf(currentStage);
  const completed = new Set(completedStages);

  return (
    <ol className="assessment-progress" aria-label="Assessment progress">
      {STAGES.map((stage, index) => {
        const state =
          completed.has(stage) || index < currentIndex
            ? "completed"
            : stage === currentStage
              ? "current"
              : "upcoming";
        const marker = state === "completed" ? "✓" : state === "current" ? "●" : "○";

        return (
          <li key={stage} className={`assessment-progress__step is-${state}`}>
            <span className="assessment-progress__marker" aria-hidden="true">
              {marker}
            </span>
            <span>{STAGE_LABELS[stage]}</span>
          </li>
        );
      })}
    </ol>
  );
}
