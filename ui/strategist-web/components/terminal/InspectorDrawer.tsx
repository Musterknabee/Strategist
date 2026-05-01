"use client";

import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import { useEffect, useState } from "react";

export function InspectorDrawer() {
  const { inspector, closeInspector, rawJsonMode } = useTerminalCockpit();
  const [rawOpen, setRawOpen] = useState(false);

  useEffect(() => {
    if (rawJsonMode) setRawOpen(true);
  }, [rawJsonMode, inspector?.title]);

  const defaultInspector: InspectorPayload = {
    title: "System Inspector",
    subtitle: "Select any row, tile, or pane to inspect read-plane details",
    body: (
      <div className="term-inspector__empty">
        <p>STATUS: PENDING</p>
        <p>SUMMARY: no item selected. Raw JSON appears here only after a drilldown selection.</p>
        <p>WARNINGS: UNKNOWN until a read-plane object is selected.</p>
      </div>
    ),
  };
  const active: InspectorPayload = inspector ?? defaultInspector;

  const showRaw = rawJsonMode || rawOpen;

  return (
    <aside className="term-inspector" role="dialog" aria-label="Inspector">
      <header className="term-inspector__head">
        <div>
          <div className="term-inspector__title">{active.title}</div>
          {active.subtitle && <div className="term-inspector__sub muted">{active.subtitle}</div>}
        </div>
        <button type="button" className="term-icon-btn" onClick={closeInspector} aria-label="Close inspector" disabled={!inspector}>
          ✕
        </button>
      </header>
      {active.body != null && <div className="term-inspector__body">{active.body}</div>}
      {active.digestToCopy && (
        <div className="term-inspector__actions">
          <button
            type="button"
            className="term-btn term-btn--sm"
            onClick={() => void navigator.clipboard.writeText(active.digestToCopy ?? "")}
          >
            Copy digest
          </button>
        </div>
      )}
      {active.rawJson !== undefined && (
        <div className="term-inspector__raw">
          <button type="button" className="term-btn term-btn--sm" onClick={() => setRawOpen(!rawOpen)}>
            {showRaw ? "Hide" : "Show"} raw JSON
          </button>
          {showRaw && (
            <pre className="term-inspector__pre">{JSON.stringify(active.rawJson, null, 2)}</pre>
          )}
        </div>
      )}
    </aside>
  );
}
