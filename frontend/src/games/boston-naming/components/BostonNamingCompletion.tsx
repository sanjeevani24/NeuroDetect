import type { ReactNode } from "react";

interface BostonNamingCompletionProps {
  children: ReactNode;
  progress?: ReactNode;
}

export function BostonNamingCompletion({ children, progress }: BostonNamingCompletionProps) {
  return (
    <section className="boston-naming__completion">
      {progress ? <div className="boston-naming__completion-progress">{progress}</div> : null}
      {children}
    </section>
  );
}
