import type { ReactNode } from "react";

export function MonoValue({ children, title, truncate }: { children: ReactNode; title?: string; truncate?: boolean }) {
  return (
    <span className={`mono-value${truncate ? " mono-value--truncate" : ""}`} title={title}>
      {children}
    </span>
  );
}
