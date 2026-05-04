"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiResearchOsDriftLatest } from "@/hooks/useUiResearchOsDrift";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

type DriftRow = Record<string, unknown> & { __id: string };

export default function ResearchDriftPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiResearchOsDriftLatest();
  const root = q.data ? asRecord(q.data) : null;
  const latest = root?.latest ? asRecord(root.latest) : null;
  const degraded = root ? asStringArray(root.degraded) : [];
  const warnings = latest ? asStringArray(latest.warnings) : [];
  const blockers = latest ? asStringArray(latest.blockers) : [];

  const entries: DriftRow[] = useMemo(() => {
    const raw = Array.isArray(latest?.entries) ? latest.entries : [];
    return raw
      .map((item, i) => {
        const r = asRecord(item);
        if (!r) return null;
        return { ...r, __id: `${asString(r.key) ?? "drift"}-${i}` };
      })
      .filter((x): x is DriftRow => x !== null);
  }, [latest]);

  const changedRows = entries.filter((r) => asString(r.change_type) !== "UNCHANGED");

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "research-drift",
        ts: asString(root?.generated_at_utc),
        severity: blockers.length ? "bad" : degraded.length || warnings.length ? "warn" : "ok",
        text: latest
          ? `DRIFT ${asString(latest.status) ?? "UNKNOWN"} · changed=${latest.changed_count ?? 0} added=${latest.added_count ?? 0} removed=${latest.removed_count ?? 0}`
          : "NO_RESEARCH_OS_EVIDENCE_DRIFT_REPORT",
      },
    ],
    [blockers.length, degraded.length, latest, root, warnings.length],
  );
  useTerminalPageBind(tape, []);

  const cols: DenseColumn<DriftRow>[] = [
    { key: "change", header: "Change", cell: (r) => <StatusBadge raw={asString(r.change_type) ?? "—"} /> },
    { key: "category", header: "Category", cell: (r) => <StatusBadge raw={asString(r.category) ?? "—"} /> },
    { key: "path", header: "Artifact", cell: (r) => <code>{asString(r.candidate_relative_path) ?? asString(r.baseline_relative_path) ?? "—"}</code> },
    { key: "base", header: "Base SHA", cell: (r) => (asString(r.baseline_file_sha256) ?? "—").slice(0, 12) },
    { key: "cand", header: "Cand SHA", cell: (r) => (asString(r.candidate_file_sha256) ?? "—").slice(0, 12) },
    { key: "fields", header: "Fields", cell: (r) => asStringArray(r.changed_fields).join(", ") || "—" },
    { key: "delta", header: "Δ bytes", cell: (r) => String(r.size_delta_bytes ?? "—") },
  ];

  if (!config.ok) {
    return <div className="term-page cockpit-page"><div className="term-page__banner">{config.error.message}</div></div>;
  }

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Research Drift</h1>
          <p className="muted">Catalog-to-catalog evidence diff · changed artifacts · status movement · read-plane only</p>
        </div>
      </div>

      <div className="readiness" role="status">
        <strong>Drift reports compare evidence catalogs only</strong>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          This page does not execute research, send broker orders, approve deployment, or certify profitability.
        </p>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Drift summary" dense onInspect={() => openInspector({ title: "Research evidence drift", rawJson: q.data ?? {} })}>
          {q.isError && <p className="term-page__banner">Could not load /ui/research-os/drift/latest</p>}
          {!latest ? (
            <p className="muted">No drift report — run <code className="json-preview">strategy-validator-research-os-drift build --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "drift_id", v: asString(latest.drift_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(latest.status) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(latest.trust_banner) ?? "—"} /> },
                { k: "baseline", v: asString(latest.baseline_catalog_id) ?? "—" },
                { k: "candidate", v: asString(latest.candidate_catalog_id) ?? "—" },
                { k: "added", v: String(latest.added_count ?? 0) },
                { k: "removed", v: String(latest.removed_count ?? 0) },
                { k: "changed", v: String(latest.changed_count ?? 0) },
                { k: "unchanged", v: String(latest.unchanged_count ?? 0) },
                { k: "drift_spine", v: (asString(latest.drift_spine_sha256) ?? "—").slice(0, 24) },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-research-os-drift build --overwrite --json
          </pre>
        </Pane>

        <Pane title="Category deltas" dense>
          <JsonDetails summary="category_change_counts" data={asRecord(latest?.category_change_counts) ?? {}} />
        </Pane>

        <Pane title="Warnings / blockers" dense>
          {warnings.length ? <JsonDetails summary="warnings" data={warnings} /> : <p className="muted">No drift warnings indexed.</p>}
          {blockers.length ? <JsonDetails summary="blockers" data={blockers} /> : <p className="muted">No drift blockers indexed.</p>}
        </Pane>

        <Pane title="Changed evidence entries" dense>
          <DenseTable
            columns={cols}
            rows={changedRows.length ? changedRows : entries}
            rowKey={(r) => r.__id}
            onRowClick={(r) => openInspector({ title: `Drift entry · ${asString(r.key) ?? "entry"}`, rawJson: r })}
          />
        </Pane>
      </div>
    </main>
  );
}
