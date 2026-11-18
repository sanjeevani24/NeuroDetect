import { useMemo, useState } from "react";
import { DISTRACTOR_ITEM_POOL, TARGET_ITEM_POOL } from "../config/memoryConfig";
import { createMemoryEvent } from "../telemetry/memoryEvents";
import type { MemoryEvent } from "../telemetry/eventTypes";
import type { MemoryItem } from "../types/memoryTypes";

interface ImmediateRecallProps {
  assessmentId: string;
  onEvent: (event: MemoryEvent) => void;
  onComplete: () => void;
}

function shuffledOnce(items: MemoryItem[], seed: number): MemoryItem[] {
  // Simple deterministic shuffle for a stable production-feeling layout;
  // tests exercise the underlying feature logic directly with fixed data,
  // so full random shuffling here is safe.
  const copy = [...items];
  let s = seed;
  for (let i = copy.length - 1; i > 0; i--) {
    s = (s * 9301 + 49297) % 233280;
    const j = Math.floor((s / 233280) * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

export function ImmediateRecall({ assessmentId, onEvent, onComplete }: ImmediateRecallProps) {
  const options = useMemo(
    () => shuffledOnce([...TARGET_ITEM_POOL, ...DISTRACTOR_ITEM_POOL], 42),
    []
  );
  const [selected, setSelected] = useState<Record<string, boolean>>({});

  const targetIds = useMemo(() => new Set(TARGET_ITEM_POOL.map((i) => i.id)), []);

  function toggle(item: MemoryItem) {
    const isNowSelected = !selected[item.id];
    setSelected((prev) => ({ ...prev, [item.id]: isNowSelected }));
    onEvent(
      createMemoryEvent({
        assessmentId,
        phase: "IMMEDIATE_RECALL",
        eventType: isNowSelected ? "item_selected" : "item_deselected",
        itemId: item.id,
        metadata: { is_target: targetIds.has(item.id) },
      })
    );
  }

  return (
    <div className="memory-phase immediate-recall-phase">
      <p className="memory-instruction">Select all the items you remember seeing.</p>
      <div className="memory-item-grid">
        {options.map((item) => (
          <button
            key={item.id}
            type="button"
            className={"memory-item-option" + (selected[item.id] ? " selected" : "")}
            onClick={() => toggle(item)}
            aria-pressed={!!selected[item.id]}
          >
            {item.label}
          </button>
        ))}
      </div>
      <button type="button" onClick={onComplete} className="memory-continue-button">
        Continue
      </button>
    </div>
  );
}
