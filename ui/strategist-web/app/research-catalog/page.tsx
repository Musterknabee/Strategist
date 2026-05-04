"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiResearchOsCatalogLatest } from "@/hooks/useUiResearchOsCatalog";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

type CatalogRow = Record<string, unknown> & { __id: string };

export default function ResearchCatalogPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiResearchOsCatalogLatest();
  const root = q.data ? asRecord(q.data) : null;
  const latest = root?.latest ? asRecord(root.latest) : null;
  const degraded = root ? asStringArray(root.degraded) : [];
  const warnings = latest ? asStringArray(latest.warnings) : [];
  const blockers = latest ? asStringArray(latest.blockers) : [];

  const entries: CatalogRow[] = useMemo(() => {
    const raw = Array.isArray(latest?.entries) ? latest.entries : [];
    return raw
      .map((item, i) => {
        const r = asRecord(item);
        if (!r) return null;
        return { ...r, __id: `${asString(r.relative_path) ?? "entry"}-${i}` };
      })
      .filter((x): x is CatalogRow => x !== null);
  }, [latest]);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "research-catalog",
        ts: asString(root?.generated_at_utc),
        severity: blockers.length ? "bad" : degraded.length || warnings.length ? "warn" : "ok",
        text: latest
          ? `CATALOG ${asString(latest.status) ?? "UNKNOWN"} · entries=${entries.length}`
          : "NO_RESEARCH_OS_EVIDENCE_CATALOG",
      },
    ],
    [blockers.length, degraded.length, entries.length, latest, root, warnings.length],
  );
  useTerminalPageBind(tape, []);

  const cols: DenseColumn<CatalogRow>[] = [
    { key: "category", header: "Category", cell: (r) => <StatusBadge raw={asString(r.category) ?? "—"} /> },
    { key: "path", header: "Artifact", cell: (r) => <code>{asString(r.relative_path) ?? "—"}</code> },
    { key: "status", header: "Status", cell: (r) => <StatusBadge raw={asString(r.status_hint) ?? "—"} /> },
    { key: "latest", header: "Latest", cell: (r) => (r.latest_alias ? "yes" : "no") },
    { key: "size", header: "Size", cell: (r) => String(r.size_bytes ?? "—") },
    { key: "sha", header: "SHA", cell: (r) => (asString(r.file_sha256) ?? "—").slice(0, 16) },
    { key: "warn", header: "Warn", cell: (r) => String(asStringArray(r.warnings).length) },
    { key: "block", header: "Block", cell: (r) => String(asStringArray(r.blockers).length) },
  ];

  if (!config.ok) {
    return <div className="term-page cockpit-page"><div className="term-page__banner">{config.error.message}</div></div>;
  }

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Research Catalog</h1>
          <p className="muted">Evidence inventory · artifact digests · historical Research OS records · read-plane only</p>
        </div>
      </div>

      <div className="readiness" role="status">
        <strong>Catalog is an offline index, not execution authority</strong>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          It records existing artifact paths and SHA-256s. It does not authorize live trading, broker orders, deployment approval, or profitability claims.
        </p>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Catalog summary" dense onInspect={() => openInspector({ title: "Research evidence catalog", rawJson: q.data ?? {} })}>
          {q.isError && <p className="term-page__banner">Could not load /ui/research-os/catalog/latest</p>}
          {!latest ? (
            <p className="muted">No catalog — run <code className="json-preview">strategy-validator-research-os-catalog build --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "catalog_id", v: asString(latest.catalog_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(latest.status) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(latest.trust_banner) ?? "—"} /> },
                { k: "entries", v: String(latest.entry_count ?? entries.length) },
                { k: "latest_entries", v: String(latest.latest_entry_count ?? "—") },
                { k: "catalog_spine", v: (asString(latest.catalog_spine_sha256) ?? "—").slice(0, 24) },
                { k: "manifest_sha256", v: (asString(latest.manifest_sha256) ?? "—").slice(0, 24) },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-research-os-catalog build --overwrite --json
          </pre>
        </Pane>

        <Pane title="Category counts" dense>
          <JsonDetails summary="category_counts" data={asRecord(latest?.category_counts) ?? {}} />
          <JsonDetails summary="latest_by_category" data={asRecord(latest?.latest_by_category) ?? {}} />
        </Pane>

        <Pane title="Warnings / blockers" dense>
          {warnings.length ? <JsonDetails summary="warnings" data={warnings} /> : <p className="muted">No catalog warnings indexed.</p>}
          {blockers.length ? <JsonDetails summary="blockers" data={blockers} /> : <p className="muted">No catalog blockers indexed.</p>}
        </Pane>

        <Pane title="Evidence entries" dense>
          <DenseTable
            columns={cols}
            rows={entries}
            rowKey={(r) => r.__id}
            onRowClick={(r) => openInspector({ title: `Catalog entry · ${asString(r.relative_path) ?? "entry"}`, rawJson: r })}
          />
        </Pane>
      </div>
    </main>
  );
}
