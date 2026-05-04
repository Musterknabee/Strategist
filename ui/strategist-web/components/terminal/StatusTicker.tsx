"use client";

import { MonoValue } from "./MonoValue";
import { SeverityBadge } from "./SeverityBadge";
import type { TapeLine } from "@/lib/terminal/cockpit-context";

export function StatusTicker({ items }: { items: Pick<TapeLine, "severity" | "text">[] }) {
  if (items.length === 0) return null;
  return (
    <div className="term-ticker" aria-label="Status rail">
      {items.map((it, i) => (
        <span key={i} className="term-ticker__item">
          <SeverityBadge severity={it.severity}>{it.severity[0].toUpperCase()}</SeverityBadge>
          <MonoValue truncate title={it.text}>
            {it.text}
          </MonoValue>
        </span>
      ))}
    </div>
  );
}
