import { useEffect, useState } from "react";

import { GameShell } from "../../../components/ui/GameShell";
import { PrimaryButton } from "../../../components/ui/buttons";
import { LANGUAGE_TASKS } from "../config/mmseConfig";
import { createMMSEEvent, type MMSEEvent } from "../telemetry/mmseEvents";

interface LanguagePhaseProps {
  assessmentId: string;
  onEvent: (event: MMSEEvent) => void;
  onComplete: () => void;
}

export function LanguagePhase({ assessmentId, onEvent, onComplete }: LanguagePhaseProps) {
  const [values, setValues] = useState<Record<string, string>>({});

  useEffect(() => {
    LANGUAGE_TASKS.forEach((task) => {
      onEvent(
        createMMSEEvent({
          assessmentId,
          phase: "LANGUAGE",
          eventType: "question_presented",
          questionId: task.id,
          metadata: { prompt: task.prompt, expected_answer: task.expectedAnswer },
        })
      );
    });
  }, [assessmentId, onEvent]);

  return (
    <GameShell title="MMSE" phase="Language" progress="05 / 07">
      <div className="mmse-stack">
        {LANGUAGE_TASKS.map((task) => (
          <label key={task.id} className="mmse-field">
            <span>{task.prompt}</span>
            <input
              type="text"
              value={values[task.id] ?? ""}
              onFocus={() =>
                onEvent(
                  createMMSEEvent({
                    assessmentId,
                    phase: "LANGUAGE",
                    eventType: "response_started",
                    questionId: task.id,
                  })
                )
              }
              onChange={(event) => setValues((prev) => ({ ...prev, [task.id]: event.target.value }))}
            />
          </label>
        ))}
      </div>
      <div className="mmse-actions">
        <PrimaryButton
          type="button"
          onClick={() => {
            LANGUAGE_TASKS.forEach((task) => {
              onEvent(
                createMMSEEvent({
                  assessmentId,
                  phase: "LANGUAGE",
                  eventType: "response_submitted",
                  questionId: task.id,
                  value: values[task.id]?.trim() ?? "",
                  metadata: {
                    prompt: task.prompt,
                    expected_answer: task.expectedAnswer,
                  },
                })
              );
            });
            onComplete();
          }}
        >
          Continue
        </PrimaryButton>
      </div>
    </GameShell>
  );
}
