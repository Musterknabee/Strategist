"use client";

import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import { useEffect, useState } from "react";

export function InspectorDrawer() {
  const { inspector, closeInspector, rawJsonMode } = useTerminalCockpit();
  const [rawOpen, setRawOpen] = useState(false);

  useEffect(() => {
    if (rawJsonMode) setRawOpen(true);
  }, [rawJsonMode, inspector?.title]);

  if (!inspector) return null;

  const showRaw = rawJsonMode || rawOpen;

  return (
    <aside className="term-inspector" role="dialog" aria-label="Inspector">
      <header className="term-inspector__head">
        <div>
          <div className="term-inspector__title">{inspector.title}</div>
          {inspector.subtitle && <div className="term-inspector__sub muted">{inspector.subtitle}</div>}
        </div>
        <button type="button" className="term-icon-btn" onClick={closeInspector} aria-label="Close inspector">
          ✕
        </button>
      </header>
      {inspector.body != null && <div className="term-inspector__body">{inspector.body}</div>}
      {inspector.digestToCopy && (
        <div className="term-inspector__actions">
          <button
            type="button"
            className="term-btn term-btn--sm"
            onClick={() => void navigator.clipboard.writeText(inspector.digestToCopy ?? "")}
          >
            Copy digest
          </button>
        </div>
      )}
      {inspector.rawJson !== undefined && (
        <div className="term-inspector__raw">
          <button type="button" className="term-btn term-btn--sm" onClick={() => setRawOpen(!rawOpen)}>
            {showRaw ? "Hide" : "Show"} raw JSON
          </button>
          {showRaw && (
            <pre className="term-inspector__pre">{JSON.stringify(inspector.rawJson, null, 2)}</pre>
          )}
        </div>
      )}
    </aside>
  );
}
