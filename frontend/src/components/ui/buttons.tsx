import type { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
}

export function PrimaryButton({ children, className = "", ...props }: ButtonProps) {
  return (
    <button {...props} className={`button button--primary ${className}`.trim()}>
      {children}
    </button>
  );
}

export function SecondaryButton({ children, className = "", ...props }: ButtonProps) {
  return (
    <button {...props} className={`button button--secondary ${className}`.trim()}>
      {children}
    </button>
  );
}
