import type { ReactNode } from "react";

export function TermKV({ rows }: { rows: { k: string; v: ReactNode }[] }) {
  return (
    <dl className="term-kv">
      {rows.map((r) => (
        <div key={r.k} className="term-kv__row">
          <dt>{r.k}</dt>
          <dd>{r.v}</dd>
        </div>
      ))}
    </dl>
  );
}
