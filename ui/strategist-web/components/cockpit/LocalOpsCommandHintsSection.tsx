"use client";

import { useState } from "react";
import { StatusBadge } from "@/components/operator/StatusBadge";
import type { LocalOpsCommandEntry } from "@/lib/operator/local-ops-command-hints";
import { localOpsCommandById } from "@/lib/operator/local-ops-command-hints";

export type LocalOpsCommandHintsSectionProps = {
  /** Registry command ids in display order */
  commandIds: readonly string[];
  /** data-testid prefix for section and rows */
  testIdPrefix: string;
  /** Optional intro line under the heading */
  intro?: string;
};

function CopyRow({ entry, testIdPrefix }: { entry: LocalOpsCommandEntry; testIdPrefix: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div
      className="local-ops-command-hint-row"
      data-testid={`${testIdPrefix}-row-${entry.id}`}
      style={{ marginBottom: "10px", fontSize: "10px" }}
    >
      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", alignItems: "center", marginBottom: "4px" }}>
        <strong>{entry.label}</strong>
        <StatusBadge raw={entry.safetyClass} />
      </div>
      <div className="muted" style={{ fontSize: "9px", marginBottom: "4px" }}>
        Expected evidence: {entry.expectedEvidence}
      </div>
      <div className="muted" style={{ fontSize: "9px", marginBottom: "4px" }}>
        Cockpit: {entry.cockpitPane} · Gate: {entry.ciTruthGate}
      </div>
      {entry.productionWarning ? (
        <div className="term-page__banner" style={{ fontSize: "9px", marginBottom: "4px" }} role="status">
          {entry.productionWarning}
        </div>
      ) : null}
      <div style={{ display: "flex", gap: "6px", alignItems: "flex-start", flexWrap: "wrap" }}>
        <code
          className="json-preview"
          data-testid={`${testIdPrefix}-command-${entry.id}`}
          style={{ flex: "1 1 240px", wordBreak: "break-all", fontSize: "10px" }}
        >
          {entry.commandText}
        </code>
        <button
          type="button"
          className="linkish"
          data-testid={`${testIdPrefix}-copy-${entry.id}`}
          onClick={() => {
            void navigator.clipboard.writeText(entry.commandText).then(() => {
              setCopied(true);
              window.setTimeout(() => setCopied(false), 2000);
            });
          }}
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
    </div>
  );
}

/**
 * Renders registry-backed CLI hints only (copy text + metadata). Never runs shell.
 */
export function LocalOpsCommandHintsSection({ commandIds, testIdPrefix, intro }: LocalOpsCommandHintsSectionProps) {
  const entries: LocalOpsCommandEntry[] = [];
  for (const id of commandIds) {
    const c = localOpsCommandById(id);
    if (c) entries.push(c);
  }

  return (
    <section aria-label="Local operator CLI hints" data-testid={testIdPrefix}>
      <p className="muted" style={{ fontSize: "10px", margin: "0 0 8px" }} data-testid={`${testIdPrefix}-browser-note`}>
        <strong>Browser does not execute shell commands.</strong> Copy into your own terminal. Governed operator actions that
        require a mutation token use <code>POST /ui/commands/{"{action}"}</code> via the Operator Command panel — not these CLI
        strings.
      </p>
      {intro ? (
        <p className="muted" style={{ fontSize: "10px", margin: "0 0 8px" }}>
          {intro}
        </p>
      ) : null}
      {entries.map((e) => (
        <CopyRow key={e.id} entry={e} testIdPrefix={testIdPrefix} />
      ))}
    </section>
  );
}
