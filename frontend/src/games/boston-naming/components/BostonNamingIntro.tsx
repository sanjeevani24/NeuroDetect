import { PrimaryButton } from "../../../components/ui/buttons";

interface BostonNamingIntroProps {
  onContinue: () => void;
}

export function BostonNamingIntro({ onContinue }: BostonNamingIntroProps) {
  return (
    <section className="boston-naming__panel">
      <p className="boston-naming__eyebrow">Boston Naming-style task</p>
      <h2>Say the name of each object clearly.</h2>
      <div className="boston-naming__copy">
        <p>You will see pictures of different objects.</p>
        <p>Try to answer as quickly and accurately as possible.</p>
        <p>Your microphone will be used to record your answers during this stage.</p>
      </div>
      <PrimaryButton type="button" onClick={onContinue}>
        Continue
      </PrimaryButton>
    </section>
  );
}
