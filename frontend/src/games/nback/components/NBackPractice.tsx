import { useState } from "react";

import { GameShell } from "../../../components/ui/GameShell";
import { InstructionCard } from "../../../components/ui/States";
import type { TrialResponse, TrialSpec } from "../types/nbackTypes";
import { NBackProgress } from "./NBackProgress";
import { NBackTrial } from "./NBackTrial";

interface NBackPracticeProps {
  trials: TrialSpec[];
  onTrialPresented: (trial: TrialSpec, timestampMs: number) => void;
  onTrialResponse: (trial: TrialSpec, response: TrialResponse, timestampMs: number) => void;
  onTrialTimeout: (trial: TrialSpec, timestampMs: number) => void;
  onPracticeComplete: () => void;
}

export function NBackPractice({
  trials,
  onTrialPresented,
  onTrialResponse,
  onTrialTimeout,
  onPracticeComplete,
}: NBackPracticeProps) {
  const [index, setIndex] = useState(0);
  const current = trials[index];

  function advance() {
    if (index + 1 >= trials.length) {
      onPracticeComplete();
    } else {
      setIndex(index + 1);
    }
  }

  if (!current) {
    return (
      <GameShell title="N-Back" phase="Practice" progress="03 / 03">
        <InstructionCard title="Preparing practice" message="Setting up the practice sequence." />
      </GameShell>
    );
  }

  return (
    <GameShell title="N-Back" phase="Practice Round" progress="03 / 03">
      <div className="nback-screen">
        <NBackProgress currentTrial={index} totalTrials={trials.length} />
        <NBackTrial
          key={current.trialId}
          trial={current}
          showFeedback
          onPresented={(ts) => onTrialPresented(current, ts)}
          onResponse={(response, ts) => onTrialResponse(current, response, ts)}
          onTimeout={(ts) => onTrialTimeout(current, ts)}
          onTrialComplete={advance}
        />
      </div>
    </GameShell>
  );
}
