import { useEffect, useRef, useState } from "react";
import { DISTRACTOR_CONFIG } from "../config/memoryConfig";
import { createMemoryEvent } from "../telemetry/memoryEvents";
import type { MemoryEvent } from "../telemetry/eventTypes";

interface DistractorPhaseProps {
  assessmentId: string;
  onEvent: (event: MemoryEvent) => void;
  onComplete: () => void;
}

/**
 * Simple controlled distractor: count backwards from 100 by 3s. This
 * exists only to create a controlled delay before delayed recall — it
 * generates no memory features of its own.
 */
export function DistractorPhase({ assessmentId, onEvent, onComplete }: DistractorPhaseProps) {
  const [current, setCurrent] = useState(DISTRACTOR_CONFIG.startValue);
  const [input, setInput] = useState("");
  const startedRef = useRef(false);

  useEffect(() => {
    if (!startedRef.current) {
      startedRef.current = true;
      onEvent(
        createMemoryEvent({
          assessmentId,
          phase: "DISTRACTOR",
          eventType: "response_started",
          metadata: { note: "distractor_started" },
        })
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleSubmit() {
    const expected = current - DISTRACTOR_CONFIG.step;
    if (input.trim() === String(expected)) {
      setCurrent(expected);
      setInput("");
      if (expected <= 0) {
        finish();
      }
    } else {
      setInput("");
    }
  }

  function finish() {
    onEvent(
      createMemoryEvent({
        assessmentId,
        phase: "DISTRACTOR",
        eventType: "response_submitted",
        metadata: { note: "distractor_completed" },
      })
    );
    onComplete();
  }

  return (
    <div className="memory-phase distractor-phase">
      <p className="memory-instruction">{DISTRACTOR_CONFIG.prompt}</p>
      <p>
        Current: <strong>{current}</strong>
      </p>
      <input
        type="number"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder={`${current - DISTRACTOR_CONFIG.step}`}
      />
      <div className="memory-button-row">
        <button type="button" onClick={handleSubmit}>
          Submit
        </button>
        <button type="button" onClick={finish} className="memory-skip-button">
          Skip ahead
        </button>
      </div>
    </div>
  );
}
