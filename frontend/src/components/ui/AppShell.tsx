import type { ReactNode } from "react";

interface AppShellProps {
  children: ReactNode;
  header: ReactNode;
  footer?: ReactNode;
}

export function AppShell({ children, header, footer }: AppShellProps) {
  return (
    <div className="app-shell">
      <div className="app-shell__backdrop" aria-hidden="true" />
      <div className="app-shell__frame">
        <header className="app-shell__header">{header}</header>
        <main className="app-shell__main">{children}</main>
        {footer ? <footer className="app-shell__footer">{footer}</footer> : null}
      </div>
    </div>
  );
}
