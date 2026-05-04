import type { ReactNode } from "react";

export function Pane({
  title,
  badge,
  children,
  onInspect,
  dense,
}: {
  title: string;
  badge?: ReactNode;
  children: ReactNode;
  onInspect?: () => void;
  dense?: boolean;
}) {
  return (
    <section className={`term-pane${dense ? " term-pane--dense" : ""}`}>
      <header className="term-pane__head">
        <span className="term-pane__title">{title}</span>
        {badge}
        {onInspect && (
          <button type="button" className="term-pane__inspect" onClick={onInspect} title="Inspect">
            ⧉
          </button>
        )}
      </header>
      <div className="term-pane__body">{children}</div>
    </section>
  );
}
