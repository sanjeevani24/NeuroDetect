import type { ReactNode } from "react";

interface GameShellProps {
  title: string;
  phase: string;
  progress?: string;
  timer?: string | null;
  children: ReactNode;
  footer?: ReactNode;
}

export function GameShell({ title, phase, progress, timer, children, footer }: GameShellProps) {
  return (
    <section className="game-shell">
      <div className="game-shell__top">
        <div>
          <p className="game-shell__eyebrow">{title}</p>
          <h2 className="game-shell__title">{phase}</h2>
        </div>
        <div className="game-shell__meta">
          {progress ? <span className="game-shell__pill">{progress}</span> : null}
          {timer ? <span className="game-shell__pill">{timer}</span> : null}
        </div>
      </div>
      <div className="game-shell__body">{children}</div>
      {footer ? <div className="game-shell__footer">{footer}</div> : null}
    </section>
  );
}
