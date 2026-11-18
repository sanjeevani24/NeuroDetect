import { useEffect, useRef, useState } from "react";

import { GameShell } from "../../../components/ui/GameShell";
import { PrimaryButton } from "../../../components/ui/buttons";
import { ORIENTATION_QUESTIONS } from "../config/mmseConfig";
import { createMMSEEvent, type MMSEEvent } from "../telemetry/mmseEvents";

interface OrientationPhaseProps {
  assessmentId: string;
  onEvent: (event: MMSEEvent) => void;
  onComplete: () => void;
}

export function OrientationPhase({ assessmentId, onEvent, onComplete }: OrientationPhaseProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const hasLoggedQuestionsRef = useRef(false);

  useEffect(() => {
    if (hasLoggedQuestionsRef.current) return;
    hasLoggedQuestionsRef.current = true;
    ORIENTATION_QUESTIONS.forEach((question) => {
      onEvent(
        createMMSEEvent({
          assessmentId,
          phase: "ORIENTATION",
          eventType: "question_presented",
          questionId: question.id,
          metadata: { prompt: question.prompt, expected_answer: question.expectedAnswer },
        })
      );
    });
  }, [assessmentId, onEvent]);

  return (
    <GameShell title="MMSE" phase="Orientation" progress="02 / 07">
      <div className="mmse-stack">
        {ORIENTATION_QUESTIONS.map((question) => (
          <label key={question.id} className="mmse-field">
            <span>{question.prompt}</span>
            <input
              type="text"
              value={values[question.id] ?? ""}
              onFocus={() =>
                onEvent(
                  createMMSEEvent({
                    assessmentId,
                    phase: "ORIENTATION",
                    eventType: "response_started",
                    questionId: question.id,
                  })
                )
              }
              onChange={(event) => setValues((prev) => ({ ...prev, [question.id]: event.target.value }))}
            />
          </label>
        ))}
      </div>
      <div className="mmse-actions">
        <PrimaryButton
          type="button"
          onClick={() => {
            ORIENTATION_QUESTIONS.forEach((question) => {
              const value = values[question.id]?.trim() ?? "";
              onEvent(
                createMMSEEvent({
                  assessmentId,
                  phase: "ORIENTATION",
                  eventType: "response_submitted",
                  questionId: question.id,
                  value,
                  metadata: {
                    prompt: question.prompt,
                    expected_answer: question.expectedAnswer,
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
