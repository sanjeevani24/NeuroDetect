import { InstructionCard } from "../../../components/ui/States";
import { PrimaryButton } from "../../../components/ui/buttons";
import { GameShell } from "../../../components/ui/GameShell";

interface NBackReadyProps {
  onStart: () => void;
}

export function NBackReady({ onStart }: NBackReadyProps) {
  return (
    <GameShell title="N-Back" phase="Ready" progress="03 / 03">
      <div className="nback-screen">
        <InstructionCard
          title="Practice complete"
          message="The scored assessment begins now. You will no longer see immediate correctness feedback."
        />
        <InstructionCard
          title="Response controls"
          message="Press M for MATCH or N for NO MATCH, or use the on-screen buttons."
        />
        <div className="nback-actions">
          <PrimaryButton type="button" onClick={onStart}>
            Start N-Back
          </PrimaryButton>
        </div>
      </div>
    </GameShell>
  );
}
