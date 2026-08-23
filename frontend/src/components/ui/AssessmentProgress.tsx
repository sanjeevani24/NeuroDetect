export interface AssessmentProgressStep {
  id: string;
  label: string;
}

interface AssessmentProgressProps {
  currentStage: string;
  steps: AssessmentProgressStep[];
  completedStages?: string[];
}

export function AssessmentProgress({
  currentStage,
  steps,
  completedStages = [],
}: AssessmentProgressProps) {
  const currentIndex = steps.findIndex((step) => step.id === currentStage);
  const completed = new Set(completedStages);

  return (
    <ol className="assessment-progress" aria-label="Assessment progress">
      {steps.map((step, index) => {
        const state =
          completed.has(step.id) || (currentIndex >= 0 && index < currentIndex)
            ? "completed"
            : step.id === currentStage
              ? "current"
              : "upcoming";
        const marker = state === "completed" ? "✓" : state === "current" ? "•" : "○";

        return (
          <li key={step.id} className={`assessment-progress__step is-${state}`}>
            <span className="assessment-progress__marker" aria-hidden="true">
              {marker}
            </span>
            <span>{step.label}</span>
          </li>
        );
      })}
    </ol>
  );
}
