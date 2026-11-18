import { useEffect, useRef, useState } from "react";
import { LEARNING_ITEM_DURATION_MS, TARGET_ITEM_POOL } from "../config/memoryConfig";
import { createMemoryEvent } from "../telemetry/memoryEvents";
import type { MemoryEvent } from "../telemetry/eventTypes";

interface LearningPhaseProps {
  assessmentId: string;
  onItemEvent: (event: MemoryEvent) => void;
  onComplete: () => void;
}

/**
 * Displays each target item sequentially for LEARNING_ITEM_DURATION_MS.
 * Timing is driven by timestamps recorded at presentation/hide time, not
 * by frame counts — the setTimeout here is only a display mechanism.
 */
export function LearningPhase({ assessmentId, onItemEvent, onComplete }: LearningPhaseProps) {
  const [index, setIndex] = useState(0);
  const completedRef = useRef(false);

  useEffect(() => {
    if (index >= TARGET_ITEM_POOL.length) {
      if (!completedRef.current) {
        completedRef.current = true;
        onComplete();
      }
      return;
    }

    const item = TARGET_ITEM_POOL[index];
    const presentedEvent = createMemoryEvent({
      assessmentId,
      phase: "LEARNING",
      eventType: "item_presented",
      itemId: item.id,
      metadata: { label: item.label, position: index },
    });
    onItemEvent(presentedEvent);

    const timer = setTimeout(() => {
      const hiddenEvent = createMemoryEvent({
        assessmentId,
        phase: "LEARNING",
        eventType: "item_hidden",
        itemId: item.id,
      });
      onItemEvent(hiddenEvent);
      setIndex((prev) => prev + 1);
    }, LEARNING_ITEM_DURATION_MS);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index]);

  if (index >= TARGET_ITEM_POOL.length) {
    return null;
  }

  const item = TARGET_ITEM_POOL[index];
  return (
    <div className="memory-phase learning-phase">
      <p className="memory-instruction">Remember this item:</p>
      <div className="memory-item-display" key={item.id}>
        {item.label}
      </div>
      <p className="memory-progress-count">
        {index + 1} / {TARGET_ITEM_POOL.length}
      </p>
    </div>
  );
}
