import { useState } from "react";

import { GameShell } from "../../../components/ui/GameShell";
import { InstructionCard } from "../../../components/ui/States";
import { PrimaryButton, SecondaryButton } from "../../../components/ui/buttons";
import { REGISTRATION_WORDS } from "../config/mmseConfig";
import { createMMSEEvent, type MMSEEvent } from "../telemetry/mmseEvents";

interface RegistrationPhaseProps {
  assessmentId: string;
  onEvent: (event: MMSEEvent) => void;
  onComplete: () => void;
}

export function RegistrationPhase({
  assessmentId,
  onEvent,
  onComplete,
}: RegistrationPhaseProps) {
  const [revealed, setRevealed] = useState(false);
  const [draft, setDraft] = useState("");
  const [responses, setResponses] = useState<string[]>([]);

  function addResponse() {
    const value = draft.trim();
    if (!value) return;
    onEvent(
      createMMSEEvent({
        assessmentId,
        phase: "REGISTRATION",
        eventType: "response_submitted",
        questionId: "registration_recall",
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
    <GameShell title="MMSE" phase="Registration" progress="03 / 07">
      <div className="mmse-stack">
        {!revealed ? (
          <>
            <InstructionCard
              title="Read and remember"
              message="Read these three words carefully. You will be asked to recall them now and again later."
            />
            <div className="mmse-word-row">
              {REGISTRATION_WORDS.map((word) => (
                <button
                  key={word}
                  type="button"
                  className="mmse-word-chip"
                  onClick={() =>
                    onEvent(
                      createMMSEEvent({
                        assessmentId,
                        phase: "REGISTRATION",
                        eventType: "item_presented",
                        itemId: word.toLowerCase(),
                        value: word,
                        metadata: { target: true },
                      })
                    )
                  }
                >
                  {word}
                </button>
              ))}
            </div>
            <PrimaryButton type="button" onClick={() => setRevealed(true)}>
              I am ready to recall them
            </PrimaryButton>
          </>
        ) : (
          <>
            <InstructionCard
              title="Immediate recall"
              message="Type each word you remember. Add one response at a time."
            />
            <div className="mmse-inline-form">
              <input
                type="text"
                value={draft}
                onFocus={() =>
                  onEvent(
                    createMMSEEvent({
                      assessmentId,
                      phase: "REGISTRATION",
                      eventType: "response_started",
                      questionId: "registration_recall",
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
            <PrimaryButton type="button" onClick={onComplete}>
              Continue
            </PrimaryButton>
          </>
        )}
      </div>
    </GameShell>
  );
}
