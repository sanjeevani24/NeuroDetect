import type { MemoryPhase } from "../types/memoryTypes";

const PHASE_LABELS: Record<MemoryPhase, string> = {
  INTRO: "Introduction",
  LEARNING: "Learning",
  IMMEDIATE_RECALL: "Immediate Recall",
  DISTRACTOR: "Counting Task",
  DELAYED_RECALL: "Delayed Recall",
  RECOGNITION: "Recognition",
  CONFIDENCE: "Confidence",
  COMPLETE: "Complete",
};

const PHASE_ORDER: MemoryPhase[] = [
  "LEARNING",
  "IMMEDIATE_RECALL",
  "DISTRACTOR",
  "DELAYED_RECALL",
  "RECOGNITION",
  "CONFIDENCE",
];

export function MemoryProgress({ phase }: { phase: MemoryPhase }) {
  const currentIndex = PHASE_ORDER.indexOf(phase);
  return (
    <div className="memory-progress" aria-label="Task progress">
      {PHASE_ORDER.map((p, i) => (
        <div
          key={p}
          className={
            "memory-progress-step" +
            (i === currentIndex ? " active" : i < currentIndex ? " done" : "")
          }
        >
          {PHASE_LABELS[p]}
        </div>
      ))}
    </div>
  );
}
