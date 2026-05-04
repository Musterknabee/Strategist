"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiResearchOsExportLatest } from "@/hooks/useUiResearchOsExport";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

type FileRow = Record<string, unknown> & { __id: string };

export default function ResearchExportPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiResearchOsExportLatest();
  const root = q.data ? asRecord(q.data) : null;
  const latest = root?.latest_export ? asRecord(root.latest_export) : null;
  const verification = root?.latest_verification ? asRecord(root.latest_verification) : null;
  const degraded = root ? asStringArray(root.degraded) : [];
  const warnings = latest ? asStringArray(latest.warnings) : [];
  const blockers = latest ? asStringArray(latest.blockers) : [];

  const files: FileRow[] = useMemo(() => {
    const raw = Array.isArray(latest?.files) ? latest.files : [];
    return raw
      .map((item, i) => {
        const r = asRecord(item);
        if (!r) return null;
        return { ...r, __id: `${asString(r.label) ?? "file"}-${i}` };
      })
      .filter((x): x is FileRow => x !== null);
  }, [latest]);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "research-export",
        ts: asString(root?.generated_at_utc),
        severity: blockers.length ? "bad" : degraded.length || warnings.length ? "warn" : "ok",
        text: latest
          ? `EXPORT ${asString(latest.status) ?? "UNKNOWN"} · files=${files.length} verify=${asString(verification?.status) ?? "NO_VERIFY"}`
          : "NO_RESEARCH_OS_EXPORT_BUNDLE",
      },
    ],
    [blockers.length, degraded.length, files.length, latest, root, verification, warnings.length],
  );
  useTerminalPageBind(tape, []);

  const cols: DenseColumn<FileRow>[] = [
    { key: "label", header: "Artifact", cell: (r) => <code>{asString(r.label) ?? "—"}</code> },
    { key: "present", header: "Present", cell: (r) => (r.present ? "yes" : "no") },
    { key: "required", header: "Req", cell: (r) => (r.required ? "yes" : "no") },
    { key: "warnings", header: "Warn", cell: (r) => String(asStringArray(r.warnings).length) },
    { key: "blockers", header: "Block", cell: (r) => String(asStringArray(r.blockers).length) },
    { key: "sha", header: "SHA", cell: (r) => (asString(r.file_sha256) ?? "—").slice(0, 16) },
  ];

  if (!config.ok) {
    return <div className="term-page cockpit-page"><div className="term-page__banner">{config.error.message}</div></div>;
  }

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Research Export</h1>
          <p className="muted">Portable Research OS evidence bundle · read-plane only · no live trading · no broker orders</p>
        </div>
      </div>

      <div className="readiness" role="status">
        <strong>Export is audit evidence, not approval</strong>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          The bundle copies existing artifacts and verifies their digests. It does not authorize execution or profitability claims.
        </p>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Export summary" dense onInspect={() => openInspector({ title: "Research export", rawJson: q.data ?? {} })}>
          {q.isError && <p className="term-page__banner">Could not load /ui/research-os/export/latest</p>}
          {!latest ? (
            <p className="muted">No export bundle — run <code className="json-preview">strategy-validator-research-os-export build --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "export_id", v: asString(latest.export_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(latest.status) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(latest.trust_banner) ?? "—"} /> },
                { k: "verification", v: <StatusBadge raw={asString(verification?.status) ?? "NO_VERIFY"} /> },
                { k: "files", v: String(files.length) },
                { k: "archive_sha256", v: (asString(latest.archive_sha256) ?? "—").slice(0, 24) },
                { k: "manifest_sha256", v: (asString(latest.manifest_sha256) ?? "—").slice(0, 24) },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-research-os-export build --overwrite --json
          </pre>
        </Pane>

        <Pane title="Warnings / blockers" dense>
          {warnings.length ? <JsonDetails summary="warnings" data={warnings} /> : <p className="muted">No export warnings indexed.</p>}
          {blockers.length ? <JsonDetails summary="blockers" data={blockers} /> : <p className="muted">No export blockers indexed.</p>}
        </Pane>

        <Pane title="Exported files" dense>
          <DenseTable
            columns={cols}
            rows={files}
            rowKey={(r) => r.__id}
            onRowClick={(r) => openInspector({ title: `Export file · ${asString(r.label) ?? "file"}`, rawJson: r })}
          />
        </Pane>
      </div>
    </main>
  );
}
