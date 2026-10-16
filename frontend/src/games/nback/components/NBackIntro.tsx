import { InstructionCard } from "../../../components/ui/States";
import { PrimaryButton } from "../../../components/ui/buttons";
import { GameShell } from "../../../components/ui/GameShell";
import { N_BACK_LEVEL } from "../config/nbackConfig";

interface NBackIntroProps {
  onBegin: () => void;
}

export function NBackIntro({ onBegin }: NBackIntroProps) {
  return (
    <GameShell title="Letter matching" phase="Let’s practise first">
      <div className="nback-screen">
        <InstructionCard
          title="How this task works"
          message={`You will see a sequence of letters one at a time. Decide whether the current letter matches the letter shown ${N_BACK_LEVEL} positions earlier.`}
        />
        <div className="nback-card-grid">
          <InstructionCard
            title="Example"
            message="A → B → A. When the second A appears, the correct response is MATCH."
          />
          <InstructionCard
            title="How to respond"
            message="Choose MATCH if the letter is the same as two letters ago. Choose NO MATCH if it is different."
          />
          <InstructionCard
            title="Before the assessment"
            message="You will begin with a short practice round. Practice does not affect the final result."
          />
        </div>
        <div className="nback-actions">
          <PrimaryButton type="button" onClick={onBegin}>
            Start Practice
          </PrimaryButton>
        </div>
      </div>
    </GameShell>
  );
}
