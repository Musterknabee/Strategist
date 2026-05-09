"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiEvidenceBundles } from "@/hooks/useUiEvidenceBundles";
import type { UiEvidenceBundleIndexEntry } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo, useState } from "react";

type BundleRow = UiEvidenceBundleIndexEntry & { __id: string };
type Filter = "all" | "present" | "missing" | "verified" | "blocked";

function shortDigest(value: string | null | undefined): string {
  if (!value) return "—";
  return value.length > 16 ? `${value.slice(0, 16)}…` : value;
}

export default function EvidenceBundlesPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const bundles = useUiEvidenceBundles();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [filter, setFilter] = useState<Filter>("all");
  const [selected, setSelected] = useState<string | null>(null);

  const rows = useMemo<BundleRow[]>(() => {
    const entries = Array.isArray(bundles.data?.entries) ? bundles.data.entries : [];
    return entries.map((entry, i) => ({ ...entry, __id: `${entry.kind}:${entry.path || i}` }));
  }, [bundles.data]);

  const presentCount = rows.filter((row) => row.exists).length;
  const verifiedCount = rows.filter((row) => row.verified_integrity).length;
  const missingCount = rows.length - presentCount;
  const blockedCount = rows.filter((row) => ["BLOCKED", "FAIL", "FAILED", "ERROR"].includes(row.status.toUpperCase())).length;
  const warnings = asStringArray(bundles.data?.warnings);
  const blockers = asStringArray(bundles.data?.blockers);
  const disclaimers = asStringArray(bundles.data?.disclaimers);

  const filteredRows = useMemo(() => {
    return rows.filter((row) => {
      if (filter === "present") return row.exists;
      if (filter === "missing") return !row.exists;
      if (filter === "verified") return row.verified_integrity;
      if (filter === "blocked") return ["BLOCKED", "FAIL", "FAILED", "ERROR"].includes(row.status.toUpperCase());
      return true;
    });
  }, [filter, rows]);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "evidence-bundles",
        severity: blockers.length > 0 ? "bad" : warnings.length > 0 || missingCount > 0 ? "warn" : "ok",
        text: `evidence_bundles present=${presentCount}/${rows.length} verified=${verifiedCount} missing=${missingCount}`,
      },
      {
        id: "evidence-bundles-guardrail",
        severity: "info",
        text: "discovery-only · no deployment approval · no live trading authorization",
      },
    ],
    [blockers.length, warnings.length, missingCount, presentCount, rows.length, verifiedCount],
  );

  const ticker = useMemo(
    () => [
      { severity: "neutral" as const, text: `EB ${presentCount}/${rows.length}` },
      { severity: verifiedCount > 0 ? ("ok" as const) : ("warn" as const), text: `VER ${verifiedCount}` },
    ],
    [presentCount, rows.length, verifiedCount],
  );

  useTerminalPageBind(tape, ticker);

  const cols: DenseColumn<BundleRow>[] = useMemo(
    () => [
      { key: "kind", header: "kind", width: "20%", cell: (row) => <code>{row.kind}</code> },
      { key: "status", header: "status", width: "12%", cell: (row) => <StatusBadge raw={row.status} /> },
      { key: "exists", header: "exists", width: "8%", cell: (row) => (row.exists ? "Y" : "N") },
      { key: "verified", header: "verified", width: "9%", cell: (row) => (row.verified_integrity ? "Y" : "N") },
      { key: "digest", header: "sha256", width: "14%", cell: (row) => <code>{shortDigest(row.sha256)}</code> },
      { key: "path", header: "path", cell: (row) => <code>{row.path}</code> },
    ],
    [],
  );

  if (!config.ok) {
    return (
      <div className="term-page">
        <h1 className="term-page__title">EVIDENCE · BUNDLES</h1>
        <p className="muted">{config.error.message}</p>
      </div>
    );
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">EVIDENCE · BUNDLE INDEX</h1>
      <p className="muted" style={{ fontSize: "10px" }}>
        GET /ui/evidence-bundles · discovery-only · no approval, signing, mutation, broker order, or profitability claim
      </p>

      {bundles.isLoading && <p className="muted">Loading…</p>}
      {bundles.isError && (
        <p className="term-page__banner" style={{ color: "#f85149" }}>
          {bundles.error instanceof Error ? bundles.error.message : String(bundles.error)}
        </p>
      )}

      {bundles.data && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Index" onInspect={() => openInspector({ title: "Evidence bundle index", rawJson: bundles.data })}>
              <TermKV
                rows={[
                  { k: "schema", v: bundles.data.schema_version },
                  { k: "generated", v: bundles.data.generated_at_utc },
                  { k: "repo", v: bundles.data.repo_head_sha.slice(0, 12) || "UNKNOWN" },
                  { k: "artifact_root", v: bundles.data.artifact_root },
                ]}
              />
            </Pane>
            <Pane title="Coverage">
              <TermKV
                rows={[
                  { k: "entries", v: String(rows.length) },
                  { k: "present", v: String(presentCount) },
                  { k: "missing", v: String(missingCount) },
                  { k: "verified", v: String(verifiedCount) },
                ]}
              />
            </Pane>
            <Pane title="Guardrails">
              <TermKV
                rows={[
                  { k: "warnings", v: String(warnings.length) },
                  { k: "blockers", v: String(blockers.length) },
                  { k: "status", v: <span className={`sev sev--${blockedCount ? "bad" : missingCount ? "warn" : "ok"}`}>{blockedCount ? "BLOCKED" : missingCount ? "INCOMPLETE" : "DISCOVERED"}</span> },
                ]}
              />
            </Pane>
          </PaneGrid>

          <Pane title="Bundle artifacts" dense onInspect={() => openInspector({ title: "Bundle rows", rawJson: filteredRows })}>
            <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginBottom: "8px" }}>
              {(["all", "present", "missing", "verified", "blocked"] as Filter[]).map((f) => (
                <button
                  key={f}
                  type="button"
                  className={`term-btn term-btn--sm${filter === f ? " is-active" : ""}`}
                  onClick={() => setFilter(f)}
                >
                  {f.toUpperCase()}
                </button>
              ))}
            </div>
            <DenseTable
              columns={cols}
              rows={filteredRows}
              rowKey={(row) => row.__id}
              selectedKey={selected}
              onRowClick={(row) => {
                setSelected(row.__id);
                if (row.sha256) setLastDigest(row.sha256);
                openInspector({
                  title: `Evidence bundle · ${row.kind}`,
                  rawJson: row,
                  digestToCopy: row.sha256 ?? undefined,
                });
              }}
              empty="No bundle entries matched the current filter."
            />
          </Pane>

          {disclaimers.length > 0 && (
            <div className="term-tape" style={{ maxHeight: "96px", marginTop: "8px" }}>
              {disclaimers.map((line) => (
                <div key={line} className="term-tape__line">
                  <span className="sev sev--info">DISC</span>
                  <span className="term-tape__text">{line}</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {bundles.data && <JsonDetails summary="Drilldown: full /ui/evidence-bundles JSON" data={bundles.data} />}
    </div>
  );
}
