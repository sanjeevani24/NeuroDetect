import { useEffect, useRef, useState } from "react";

import { GameShell } from "../../../components/ui/GameShell";
import { PrimaryButton } from "../../../components/ui/buttons";
import { SERIAL7_SEQUENCE } from "../config/mmseConfig";
import { createMMSEEvent, type MMSEEvent } from "../telemetry/mmseEvents";

interface AttentionPhaseProps {
  assessmentId: string;
  onEvent: (event: MMSEEvent) => void;
  onComplete: () => void;
}

export function AttentionPhase({ assessmentId, onEvent, onComplete }: AttentionPhaseProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const hasLoggedQuestionsRef = useRef(false);

  useEffect(() => {
    if (hasLoggedQuestionsRef.current) return;
    hasLoggedQuestionsRef.current = true;
    SERIAL7_SEQUENCE.forEach((question) => {
      onEvent(
        createMMSEEvent({
          assessmentId,
          phase: "ATTENTION",
          eventType: "question_presented",
          questionId: question.id,
          metadata: { prompt: question.prompt, expected_answer: question.expectedAnswer, domain: "serial7" },
        })
      );
    });
  }, [assessmentId, onEvent]);

  return (
    <GameShell title="MMSE" phase="Attention and Serial 7s" progress="04 / 07">
      <div className="mmse-stack">
        {SERIAL7_SEQUENCE.map((question, index) => (
          <label key={question.id} className="mmse-field">
            <span>
              {index + 1}. {question.prompt}
            </span>
            <input
              type="text"
              value={values[question.id] ?? ""}
              onFocus={() =>
                onEvent(
                  createMMSEEvent({
                    assessmentId,
                    phase: "ATTENTION",
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
            SERIAL7_SEQUENCE.forEach((question) => {
              onEvent(
                createMMSEEvent({
                  assessmentId,
                  phase: "ATTENTION",
                  eventType: "response_submitted",
                  questionId: question.id,
                  value: values[question.id]?.trim() ?? "",
                  metadata: {
                    prompt: question.prompt,
                    expected_answer: question.expectedAnswer,
                    domain: "serial7",
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
