import { PrimaryButton } from "../../../components/ui/buttons";

interface TrailMakingIntroProps {
  onStart: () => void;
}

export function TrailMakingIntro({ onStart }: TrailMakingIntroProps) {
  return (
    <section className="trail-card trail-card--intro">
      <p className="trail-card__eyebrow">Connect the circles</p>
      <h2>Go from a number to a letter.</h2>
      <p className="trail-card__body">
        Start with <strong>1</strong>, then <strong>A</strong>, then <strong>2</strong>, then <strong>B</strong>, and continue until the final circle.
        Work as quickly and accurately as possible.
      </p>
      <div className="trail-example" aria-hidden="true">
        <span>1</span>
        <span className="trail-example__arrow">→</span>
        <span>A</span>
        <span className="trail-example__arrow">→</span>
        <span>2</span>
        <span className="trail-example__arrow">→</span>
        <span>B</span>
      </div>
      <PrimaryButton type="button" onClick={onStart}>
        Start connecting
      </PrimaryButton>
    </section>
  );
}
