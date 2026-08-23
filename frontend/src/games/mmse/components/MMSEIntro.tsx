import { InstructionCard } from "../../../components/ui/States";
import { PrimaryButton } from "../../../components/ui/buttons";
import { GameShell } from "../../../components/ui/GameShell";

export function MMSEIntro({ onStart }: { onStart: () => void }) {
  return (
    <GameShell title="MMSE" phase="Introduction" progress="01 / 07">
      <div className="mmse-stack">
        <InstructionCard
          title="Behavioural assessment prototype"
          message="This prototype covers orientation, registration, attention, language, delayed recall, and command following. Please answer carefully and continue when ready."
        />
      </div>
      <div className="mmse-actions">
        <PrimaryButton type="button" onClick={onStart}>
          Begin MMSE
        </PrimaryButton>
      </div>
    </GameShell>
  );
}
