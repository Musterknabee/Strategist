import type { ReactNode } from "react";

export function PaneGrid({ children, cols = 2 }: { children: ReactNode; cols?: 2 | 3 | 4 }) {
  return <div className={`term-pane-grid term-pane-grid--${cols}`}>{children}</div>;
}
