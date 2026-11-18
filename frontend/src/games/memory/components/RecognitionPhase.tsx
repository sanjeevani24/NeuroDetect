import { useMemo, useState } from "react";
import { TARGET_ITEM_POOL, DISTRACTOR_ITEM_POOL } from "../config/memoryConfig";
import { createMemoryEvent } from "../telemetry/memoryEvents";
import type { MemoryEvent } from "../telemetry/eventTypes";
import type { RecognitionTrial } from "../types/memoryTypes";

interface RecognitionPhaseProps {
  assessmentId: string;
  onEvent: (event: MemoryEvent) => void;
  onComplete: () => void;
}

function buildTrials(seed: number): RecognitionTrial[] {
  const all: RecognitionTrial[] = [
    ...TARGET_ITEM_POOL.map((item, i) => ({
      trialId: `trial_${String(i).padStart(3, "0")}`,
      itemId: item.id,
      isTarget: true,
      label: item.label,
    })),
    ...DISTRACTOR_ITEM_POOL.map((item, i) => ({
      trialId: `trial_d${String(i).padStart(3, "0")}`,
      itemId: item.id,
      isTarget: false,
      label: item.label,
    })),
  ];
  // deterministic shuffle, mirrors ImmediateRecall's approach
  let s = seed;
  for (let i = all.length - 1; i > 0; i--) {
    s = (s * 9301 + 49297) % 233280;
    const j = Math.floor((s / 233280) * (i + 1));
    [all[i], all[j]] = [all[j], all[i]];
  }
  return all;
}

export function RecognitionPhase({ assessmentId, onEvent, onComplete }: RecognitionPhaseProps) {
  const trials = useMemo(() => buildTrials(7), []);
  const [index, setIndex] = useState(0);
  const [presentedAt, setPresentedAt] = useState<number>(() => Date.now());

  if (index >= trials.length) {
    return null;
  }

  const trial = trials[index];

  function respond(answer: "YES" | "NO") {
    const responseTimeMs = Date.now() - presentedAt;
    onEvent(
      createMemoryEvent({
        assessmentId,
        phase: "RECOGNITION",
        eventType: "recognition_response",
        itemId: trial.itemId,
        trialId: trial.trialId,
        value: answer,
        metadata: {
          is_target: trial.isTarget,
          correct: (answer === "YES") === trial.isTarget,
          response_time_ms: responseTimeMs,
        },
      })
    );
    if (index + 1 >= trials.length) {
      onComplete();
    } else {
      setIndex((prev) => prev + 1);
      setPresentedAt(Date.now());
    }
  }

  return (
    <div className="memory-phase recognition-phase">
      <p className="memory-instruction">Was this item in the list you saw earlier?</p>
      <div className="memory-item-display">{trial.label}</div>
      <div className="memory-button-row">
        <button type="button" onClick={() => respond("YES")}>
          Yes
        </button>
        <button type="button" onClick={() => respond("NO")}>
          No
        </button>
      </div>
      <p className="memory-progress-count">
        {index + 1} / {trials.length}
      </p>
    </div>
  );
}
