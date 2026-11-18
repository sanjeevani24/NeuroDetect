import { useState } from "react";
import { createMemoryEvent } from "../telemetry/memoryEvents";
import type { MemoryEvent } from "../telemetry/eventTypes";
import { normalizeText } from "../utils/textNormalization";

interface DelayedRecallProps {
  assessmentId: string;
  onEvent: (event: MemoryEvent) => void;
  onComplete: () => void;
}

/**
 * Free-text recall. Every submission, edit, and retry is preserved as its
 * own raw telemetry event — the backend reconstructs accuracy from the
 * raw log, this component never scores anything itself.
 */
export function DelayedRecall({ assessmentId, onEvent, onComplete }: DelayedRecallProps) {
  const [draft, setDraft] = useState("");
  const [submitted, setSubmitted] = useState<string[]>([]);
  const [startedResponse, setStartedResponse] = useState(false);

  function handleFocus() {
    if (!startedResponse) {
      setStartedResponse(true);
      onEvent(
        createMemoryEvent({
          assessmentId,
          phase: "DELAYED_RECALL",
          eventType: "response_started",
        })
      );
    }
  }

  function handleSubmitItem() {
    const text = draft.trim();
    if (!text) return;
    onEvent(
      createMemoryEvent({
        assessmentId,
        phase: "DELAYED_RECALL",
        eventType: "response_submitted",
        value: text,
        metadata: { response_order: submitted.length, normalized_preview: normalizeText(text) },
      })
    );
    setSubmitted((prev) => [...prev, text]);
    setDraft("");
  }

  function handleRemove(index: number) {
    // Explicit retry: participant is revising what they've entered.
    onEvent(
      createMemoryEvent({
        assessmentId,
        phase: "DELAYED_RECALL",
        eventType: "retry",
        metadata: { removed_response: submitted[index] },
      })
    );
    setSubmitted((prev) => prev.filter((_, i) => i !== index));
  }

  return (
    <div className="memory-phase delayed-recall-phase">
      <p className="memory-instruction">Type the items you remember from the earlier list.</p>
      <div className="memory-response-row">
        <input
          type="text"
          value={draft}
          onFocus={handleFocus}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmitItem()}
          placeholder="Type an item and press Enter"
        />
        <button type="button" onClick={handleSubmitItem}>
          Add
        </button>
      </div>
      <ul className="memory-response-list">
        {submitted.map((text, i) => (
          <li key={`${text}_${i}`}>
            {text}
            <button type="button" onClick={() => handleRemove(i)} aria-label={`Remove ${text}`}>
              ×
            </button>
          </li>
        ))}
      </ul>
      <button type="button" onClick={onComplete} className="memory-continue-button">
        Continue
      </button>
    </div>
  );
}
