"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiResearchOsClosureLatest } from "@/hooks/useUiResearchOsClosure";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

type ArtifactRow = Record<string, unknown> & { __id: string };

export default function ResearchClosurePage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiResearchOsClosureLatest();
  const root = q.data ? asRecord(q.data) : null;
  const latest = root?.latest ? asRecord(root.latest) : null;
  const degraded = root ? asStringArray(root.degraded) : [];
  const warnings = latest ? asStringArray(latest.warnings) : [];
  const blockers = latest ? asStringArray(latest.blockers) : [];

  const artifacts: ArtifactRow[] = useMemo(() => {
    const raw = Array.isArray(latest?.artifacts) ? latest.artifacts : [];
    return raw
      .map((item, i) => {
        const r = asRecord(item);
        if (!r) return null;
        return { ...r, __id: `${asString(r.artifact_kind) ?? "artifact"}-${i}` };
      })
      .filter((x): x is ArtifactRow => x !== null);
  }, [latest]);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "research-closure",
        ts: asString(root?.generated_at_utc),
        severity: blockers.length ? "bad" : degraded.length ? "warn" : "ok",
        text: latest
          ? `CLOSURE ${asString(latest.status) ?? "UNKNOWN"} · artifacts=${artifacts.length}`
          : "NO_RESEARCH_OS_CLOSURE_MANIFEST",
      },
    ],
    [artifacts.length, blockers.length, degraded.length, latest, root],
  );
  useTerminalPageBind(tape, []);

  const cols: DenseColumn<ArtifactRow>[] = [
    { key: "kind", header: "Artifact", cell: (r) => <code>{asString(r.artifact_kind) ?? "—"}</code> },
    { key: "exists", header: "Exists", cell: (r) => String(Boolean(r.exists)) },
    { key: "status", header: "Status", cell: (r) => <StatusBadge raw={asString(r.status_hint) ?? (r.exists ? "PRESENT" : "MISSING")} /> },
    { key: "schema", header: "Schema", cell: (r) => asString(r.schema_version_observed) ?? "—" },
    { key: "sha", header: "SHA256", cell: (r) => (asString(r.file_sha256) ?? "—").slice(0, 16) },
  ];

  if (!config.ok) {
    return <div className="term-page cockpit-page"><div className="term-page__banner">{config.error.message}</div></div>;
  }

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Research Closure</h1>
          <p className="muted">Digest-linked Research OS evidence closure · read-plane only · no live trading · no broker orders</p>
        </div>
      </div>

      <div className="readiness" role="status">
        <strong>Evidence closure is not deployment approval</strong>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          This page summarizes which local Research OS artifacts were present and digest-linked. It does not certify profitability or authorize live execution.
        </p>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Closure manifest" dense onInspect={() => openInspector({ title: "Research OS closure", rawJson: q.data ?? {} })}>
          {q.isError && <p className="term-page__banner">Could not load /ui/research-os/closure/latest</p>}
          {!latest ? (
            <p className="muted">No closure manifest — run <code className="json-preview">strategy-validator-research-os-closure build --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "closure_id", v: asString(latest.closure_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(latest.status) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(latest.trust_banner) ?? "—"} /> },
                { k: "present_artifacts", v: String(latest.present_artifact_count ?? "—") },
                { k: "artifact_root", v: asString(latest.artifact_root) ?? "—" },
                { k: "manifest_sha256", v: (asString(latest.manifest_sha256) ?? "—").slice(0, 24) },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-research-os-closure build --closure-id daily-research-close --overwrite --json
          </pre>
        </Pane>

        <Pane title="Warnings / blockers" dense>
          {warnings.length ? <JsonDetails summary="warnings" data={warnings} /> : <p className="muted">No warnings indexed.</p>}
          {blockers.length ? <JsonDetails summary="blockers" data={blockers} /> : <p className="muted">No blockers indexed.</p>}
        </Pane>

        <Pane title="Evidence artifacts" dense>
          <DenseTable
            columns={cols}
            rows={artifacts}
            rowKey={(r) => r.__id}
            onRowClick={(r) => openInspector({ title: `Evidence · ${asString(r.artifact_kind) ?? "artifact"}`, rawJson: r })}
          />
        </Pane>
      </div>
    </main>
  );
}
