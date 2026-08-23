import type { ReactNode } from "react";

interface StateProps {
  title: string;
  message: string;
  action?: ReactNode;
}

export function InstructionCard({ title, message }: Omit<StateProps, "action">) {
  return (
    <section className="state-card state-card--instruction">
      <h3>{title}</h3>
      <p>{message}</p>
    </section>
  );
}

export function LoadingState({ title, message }: Omit<StateProps, "action">) {
  return (
    <section className="state-card state-card--loading" aria-live="polite">
      <h3>{title}</h3>
      <p>{message}</p>
    </section>
  );
}

export function ErrorState({ title, message, action }: StateProps) {
  return (
    <section className="state-card state-card--error" role="alert">
      <h3>{title}</h3>
      <p>{message}</p>
      {action ? <div className="state-card__action">{action}</div> : null}
    </section>
  );
}

export function CompletionState({ title, message, action }: StateProps) {
  return (
    <section className="state-card state-card--completion">
      <h3>{title}</h3>
      <p>{message}</p>
      {action ? <div className="state-card__action">{action}</div> : null}
    </section>
  );
}
