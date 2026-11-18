import type { ReactNode } from "react";

interface TrailMakingCompletionProps {
  children: ReactNode;
}

export function TrailMakingCompletion({ children }: TrailMakingCompletionProps) {
  return <section className="trail-card trail-card--completion">{children}</section>;
}
