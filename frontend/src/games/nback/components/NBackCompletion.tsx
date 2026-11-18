import type { ReactNode } from "react";

import { GameShell } from "../../../components/ui/GameShell";

interface NBackCompletionProps {
  children: ReactNode;
  progress?: ReactNode;
}

export function NBackCompletion({ children, progress }: NBackCompletionProps) {
  return (
    <GameShell title="N-Back" phase="Assessment" progress="03 / 03">
      <div className="nback-screen">
        {progress}
        {children}
      </div>
    </GameShell>
  );
}
