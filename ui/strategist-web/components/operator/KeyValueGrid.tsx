import type { ReactNode } from "react";

export type KeyValueRow = { key: string; value: ReactNode };

export function KeyValueGrid({ rows }: { rows: KeyValueRow[] }) {
  return (
    <dl className="key-value-grid">
      {rows.map((r) => (
        <div key={r.key} className="key-value-grid__row">
          <dt>{r.key}</dt>
          <dd>{r.value === null || r.value === undefined ? "—" : r.value}</dd>
        </div>
      ))}
    </dl>
  );
}
