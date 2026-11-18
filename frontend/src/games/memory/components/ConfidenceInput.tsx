import { createMemoryEvent } from "../telemetry/memoryEvents";
import type { MemoryEvent } from "../telemetry/eventTypes";

const SCALE = [
  { value: 1, label: "Very unsure" },
  { value: 2, label: "Unsure" },
  { value: 3, label: "Neutral" },
  { value: 4, label: "Confident" },
  { value: 5, label: "Very confident" },
];

interface ConfidenceInputProps {
  assessmentId: string;
  phase: "immediate_recall" | "delayed_recall" | "recognition";
  label: string;
  onSubmit: (value: number, event: MemoryEvent) => void;
}

export function ConfidenceInput({ assessmentId, phase, label, onSubmit }: ConfidenceInputProps) {
  function handleSelect(value: number) {
    const event = createMemoryEvent({
      assessmentId,
      phase: "CONFIDENCE",
      eventType: "confidence_submitted",
      value: String(value),
      metadata: { phase },
    });
    onSubmit(value, event);
  }

  return (
    <div className="memory-phase confidence-input">
      <p className="memory-instruction">{label}</p>
      <div className="memory-confidence-scale">
        {SCALE.map((option) => (
          <button key={option.value} type="button" onClick={() => handleSelect(option.value)}>
            {option.value} — {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
