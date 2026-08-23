import { useState } from "react";

import { GameShell } from "../../../components/ui/GameShell";
import { InstructionCard } from "../../../components/ui/States";
import { PrimaryButton } from "../../../components/ui/buttons";
import { COMMAND_STEPS } from "../config/mmseConfig";
import { createMMSEEvent, type MMSEEvent } from "../telemetry/mmseEvents";

interface CommandPhaseProps {
  assessmentId: string;
  onEvent: (event: MMSEEvent) => void;
  onComplete: (sequence: string[]) => void;
}

export function CommandPhase({ assessmentId, onEvent, onComplete }: CommandPhaseProps) {
  const [sequence, setSequence] = useState<string[]>([]);

  function selectStep(stepId: string) {
    const next = [...sequence, stepId];
    setSequence(next);
    onEvent(
      createMMSEEvent({
        assessmentId,
        phase: "COMMAND",
        eventType: "item_selected",
        itemId: stepId,
        metadata: {
          selected_order: next.length,
          expected_sequence: COMMAND_STEPS.map((step) => step.id),
        },
      })
    );
  }

  return (
    <GameShell title="MMSE" phase="Command Following" progress="07 / 07">
      <div className="mmse-stack">
        <InstructionCard
          title="Follow the sequence"
          message="Tap the three buttons in this order: Left, then Center, then Right."
        />
        <div className="mmse-command-grid">
          {COMMAND_STEPS.map((step) => (
            <button
              key={step.id}
              type="button"
              className="mmse-command-button"
              onClick={() => selectStep(step.id)}
            >
              {step.label}
            </button>
          ))}
        </div>
        <p className="mmse-caption">Recorded sequence: {sequence.join(", ") || "None yet"}</p>
      </div>
      <div className="mmse-actions">
        <PrimaryButton
          type="button"
          onClick={() => {
            onComplete(sequence);
          }}
        >
          Finish MMSE
        </PrimaryButton>
      </div>
    </GameShell>
  );
}
