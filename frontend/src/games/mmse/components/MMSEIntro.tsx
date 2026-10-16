import { InstructionCard } from "../../../components/ui/States";
import { PrimaryButton } from "../../../components/ui/buttons";
import { GameShell } from "../../../components/ui/GameShell";

export function MMSEIntro({ onStart }: { onStart: () => void }) {
  return (
    <GameShell title="Everyday questions" phase="Before you begin">
      <div className="mmse-stack">
        <InstructionCard
          title="Answer a few everyday questions"
          message="You’ll answer questions about the day and where you are, remember words, and follow simple instructions. Read each instruction carefully, then do your best."
        />
      </div>
      <div className="mmse-actions">
        <PrimaryButton type="button" onClick={onStart}>
          Begin questions
        </PrimaryButton>
      </div>
    </GameShell>
  );
}
