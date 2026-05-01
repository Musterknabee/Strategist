"use client";

import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import { MonoValue } from "./MonoValue";
import { SeverityBadge } from "./SeverityBadge";

export function EventTape() {
  const { tapeLines } = useTerminalCockpit();
  if (tapeLines.length === 0) {
    return (
      <div id="terminal-event-tape" className="term-tape term-tape--empty" tabIndex={-1}>
        <span className="muted">Evidence event tape · no derived events for this view</span>
      </div>
    );
  }
  return (
    <div id="terminal-event-tape" className="term-tape" tabIndex={-1} role="log" aria-label="Event tape">
      {tapeLines.map((line) => (
        <div key={line.id} className="term-tape__line">
          {line.ts && <MonoValue truncate>{line.ts}</MonoValue>}
          <SeverityBadge severity={line.severity}>{line.severity.toUpperCase()}</SeverityBadge>
          <span className="term-tape__text">{line.text}</span>
        </div>
      ))}
    </div>
  );
}
