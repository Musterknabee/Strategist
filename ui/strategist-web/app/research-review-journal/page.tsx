"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiResearchOsReviewJournalLatest } from "@/hooks/useUiResearchOsReviewJournal";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

export default function ResearchReviewJournalPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiResearchOsReviewJournalLatest();
  const root = q.data ? asRecord(q.data) : null;
  const latest = root?.latest ? asRecord(root.latest) : null;
  const entries = Array.isArray(latest?.entries)
    ? latest.entries.map((x) => asRecord(x)).filter((r): r is Record<string, unknown> => r !== null)
    : [];
  const warnings = latest ? asStringArray(latest.warnings) : [];
  const blockers = latest ? asStringArray(latest.blockers) : [];

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "research-review-journal",
        ts: asString(root?.generated_at_utc),
        severity: blockers.length ? "bad" : warnings.length ? "warn" : "ok",
        text: latest ? `REVIEW JOURNAL ${asString(latest.status) ?? "UNKNOWN"} · entries=${entries.length}` : "NO_RESEARCH_OS_REVIEW_JOURNAL",
      },
    ],
    [blockers.length, entries.length, latest, root, warnings.length],
  );
  useTerminalPageBind(tape, []);

  if (!config.ok) {
    return <div className="term-page cockpit-page"><div className="term-page__banner">{config.error.message}</div></div>;
  }

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Research Review Journal</h1>
          <p className="muted">Local digest-linked review decision journal · not the canonical validator ledger</p>
        </div>
      </div>

      <div className="readiness" role="status">
        <strong>Review journal is read-plane evidence only</strong>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          This page summarizes policy, exception, readiness, handoff, and signoff artifacts. It does not approve deployment or enable live trading.
        </p>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Latest review journal" dense onInspect={() => openInspector({ title: "Research review journal", rawJson: q.data ?? {} })}>
          {q.isError && <p className="term-page__banner">Could not load /ui/research-os/review-journal/latest</p>}
          {!latest ? (
            <p className="muted">No review journal — run <code className="json-preview">strategy-validator-research-os-review-journal build --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "journal_id", v: asString(latest.journal_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(latest.status) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(latest.trust_banner) ?? "—"} /> },
                { k: "entry_count", v: String(latest.entry_count ?? 0) },
                { k: "deployment_approved", v: String(Boolean(latest.deployment_approved)) },
                { k: "journal_spine", v: (asString(latest.journal_spine_sha256) ?? "—").slice(0, 24) },
                { k: "manifest", v: (asString(latest.manifest_sha256) ?? "—").slice(0, 24) },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-research-os-review-journal build --artifact-root artifacts --journal-id daily-review-journal --overwrite --json
          </pre>
        </Pane>

        <Pane title="Journal entries" dense>
          {entries.length ? (
            <div className="terminal-table-wrap">
              <table className="terminal-table">
                <thead><tr><th>type</th><th>status</th><th>decision</th><th>source</th><th>sha</th></tr></thead>
                <tbody>
                  {entries.map((row) => (
                    <tr key={asString(row.entry_id) ?? JSON.stringify(row)}>
                      <td>{asString(row.entry_type) ?? "—"}</td>
                      <td><StatusBadge raw={asString(row.source_status) ?? "—"} /></td>
                      <td><StatusBadge raw={asString(row.source_decision) ?? "—"} /></td>
                      <td>{asString(row.source_id_hint) ?? asString(row.entry_id) ?? "—"}</td>
                      <td>{(asString(row.source_manifest_sha256) ?? asString(row.source_file_sha256) ?? "—").slice(0, 16)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <p className="muted">No journal entries.</p>}
        </Pane>

        <Pane title="Decision summary / warnings" dense>
          <JsonDetails summary="latest_decision_summary" data={latest?.latest_decision_summary ?? {}} />
          <JsonDetails summary="source_counts" data={latest?.source_counts ?? {}} />
          <JsonDetails summary="warnings" data={warnings} />
          <JsonDetails summary="blockers" data={blockers} />
        </Pane>
      </div>
    </main>
  );
}
