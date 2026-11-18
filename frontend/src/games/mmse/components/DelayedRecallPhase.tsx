import { useState } from "react";

import { GameShell } from "../../../components/ui/GameShell";
import { InstructionCard } from "../../../components/ui/States";
import { PrimaryButton, SecondaryButton } from "../../../components/ui/buttons";
import { REGISTRATION_WORDS } from "../config/mmseConfig";
import { createMMSEEvent, type MMSEEvent } from "../telemetry/mmseEvents";

interface DelayedRecallPhaseProps {
  assessmentId: string;
  onEvent: (event: MMSEEvent) => void;
  onComplete: () => void;
}

export function DelayedRecallPhase({
  assessmentId,
  onEvent,
  onComplete,
}: DelayedRecallPhaseProps) {
  const [draft, setDraft] = useState("");
  const [responses, setResponses] = useState<string[]>([]);

  function addResponse() {
    const value = draft.trim();
    if (!value) return;
    onEvent(
      createMMSEEvent({
        assessmentId,
        phase: "DELAYED_RECALL",
        eventType: "response_submitted",
        questionId: "delayed_recall",
        value,
        metadata: {
          response_order: responses.length + 1,
          target_words: REGISTRATION_WORDS,
        },
      })
    );
    setResponses((prev) => [...prev, value]);
    setDraft("");
  }

  return (
    <GameShell title="MMSE" phase="Delayed Recall" progress="06 / 07">
      <div className="mmse-stack">
        <InstructionCard
          title="Recall the earlier words"
          message="Please type each word you remember from the earlier registration step."
        />
        <div className="mmse-inline-form">
          <input
            type="text"
            value={draft}
            onFocus={() =>
              onEvent(
                createMMSEEvent({
                  assessmentId,
                  phase: "DELAYED_RECALL",
                  eventType: "response_started",
                  questionId: "delayed_recall",
                })
              )
            }
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") addResponse();
            }}
            placeholder="Type a word"
          />
          <SecondaryButton type="button" onClick={addResponse}>
            Add
          </SecondaryButton>
        </div>
        <ul className="mmse-response-list">
          {responses.map((response, index) => (
            <li key={`${response}_${index}`}>{response}</li>
          ))}
        </ul>
      </div>
      <div className="mmse-actions">
        <PrimaryButton type="button" onClick={onComplete}>
          Continue
        </PrimaryButton>
      </div>
    </GameShell>
  );
}
