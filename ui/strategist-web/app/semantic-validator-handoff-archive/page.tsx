"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiSemanticValidatorHandoffArchive, type UiSemanticValidatorHandoffArchiveQuery } from "@/hooks/useUiSemanticValidatorHandoffArchive";
import type { UiSemanticValidatorHandoffArchiveManifest, UiSemanticValidatorHandoffArchiveRecord } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type ArchiveStatusMode = "all" | "ARCHIVE_MANIFEST_VERIFIED" | "READY_FOR_EXTERNAL_ARCHIVE_MANIFEST" | "ARCHIVE_MANIFEST_INVALID" | "ARCHIVE_MANIFEST_DIGEST_MISMATCH" | "BLOCKED_CUSTODY_NOT_SEALED";
type TrustMode = "all" | "TRUSTED" | "TRUST_RESTRICTED" | "UNTRUSTED";
type BoolMode = "all" | "yes" | "no";
type ArchiveRow = UiSemanticValidatorHandoffArchiveRecord & { __id: string };

const ARCHIVE_STATUS_MODES: ArchiveStatusMode[] = ["all", "ARCHIVE_MANIFEST_VERIFIED", "READY_FOR_EXTERNAL_ARCHIVE_MANIFEST", "ARCHIVE_MANIFEST_INVALID", "ARCHIVE_MANIFEST_DIGEST_MISMATCH", "BLOCKED_CUSTODY_NOT_SEALED"];
const TRUST_MODES: TrustMode[] = ["all", "TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"];
const BOOL_MODES: BoolMode[] = ["all", "yes", "no"];

function boolParam(mode: BoolMode): boolean | null {
  if (mode === "yes") return true;
  if (mode === "no") return false;
  return null;
}

function text(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

function shortDigest(value: unknown): string {
  const s = typeof value === "string" ? value : "";
  if (!s) return "—";
  return s.length > 16 ? `${s.slice(0, 10)}…${s.slice(-6)}` : s;
}

function countRows(counts?: Record<string, number>) {
  return Object.entries(counts ?? {}).map(([k, v]) => ({ k, v: String(v) }));
}

function selectedManifests(row: ArchiveRow | null): UiSemanticValidatorHandoffArchiveManifest[] {
  return row?.matched_archive_manifests ?? [];
}

export default function SemanticValidatorHandoffArchivePage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [archiveStatusMode, setArchiveStatusMode] = useState<ArchiveStatusMode>("all");
  const [trustMode, setTrustMode] = useState<TrustMode>("all");
  const [verifiedMode, setVerifiedMode] = useState<BoolMode>("all");
  const [experimentNeedle, setExperimentNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiSemanticValidatorHandoffArchiveQuery = useMemo(
    () => ({
      archiveStatus: archiveStatusMode === "all" ? null : archiveStatusMode,
      trustBanner: trustMode === "all" ? null : trustMode,
      archiveManifestVerified: boolParam(verifiedMode),
      experimentIdContains: experimentNeedle.trim() || null,
      issueContains: issueNeedle.trim() || null,
      limit: 300,
    }),
    [archiveStatusMode, experimentNeedle, issueNeedle, trustMode, verifiedMode],
  );

  const archive = useUiSemanticValidatorHandoffArchive(query);
  const summary = archive.data?.summary ?? {};
  const rows = useMemo<ArchiveRow[]>(
    () => (archive.data?.archive_gates ?? []).map((row, i) => ({ ...row, __id: `${row.archive_gate_id}:${i}` })),
    [archive.data?.archive_gates],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(archive.data?.degraded);
  const guardrails = asStringArray(archive.data?.guardrails);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "semantic-validator-handoff-archive-counts",
        severity: Number(summary.invalid_archive_manifest_count ?? 0) > 0 || Number(summary.blocked_custody_count ?? 0) > 0 ? "warn" : "ok",
        text: `archive gates=${summary.archive_gate_count_returned ?? 0}/${summary.archive_gate_count_total ?? 0} verified=${summary.verified_archive_manifest_count ?? 0} ready=${summary.ready_for_archive_manifest_count ?? 0} invalid=${summary.invalid_archive_manifest_count ?? 0}`,
      },
      {
        id: "semantic-validator-handoff-archive-boundary",
        severity: "info",
        text: "archive manifest verification only · no archive write, artifact mutation, submission, adjudication, promotion, or execution authority",
      },
    ],
    [summary],
  );
  const ticker = useMemo(
    () => [
      { severity: Number(summary.verified_archive_manifest_count ?? 0) > 0 ? ("ok" as const) : ("neutral" as const), text: `ARCH ${summary.verified_archive_manifest_count ?? 0}` },
      { severity: Number(summary.ready_for_archive_manifest_count ?? 0) > 0 ? ("warn" as const) : ("neutral" as const), text: `READY ${summary.ready_for_archive_manifest_count ?? 0}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<ArchiveRow>[] = useMemo(
    () => [
      { key: "trust", header: "trust", width: "9%", cell: (row) => <StatusBadge raw={row.trust_banner ?? "UNKNOWN"} /> },
      { key: "status", header: "archive", width: "26%", cell: (row) => <StatusBadge raw={row.archive_status} /> },
      { key: "experiment", header: "experiment", width: "17%", cell: (row) => <code>{text(row.experiment_id)}</code> },
      { key: "manifests", header: "manifests", width: "9%", cell: (row) => <code>{row.archive_manifest_count}</code> },
      { key: "verified", header: "verified", width: "9%", cell: (row) => <StatusBadge raw={row.archive_manifest_verified ? "YES" : "NO"} /> },
      { key: "promote", header: "promote", width: "8%", cell: (row) => <StatusBadge raw={row.promotion_allowed ? "ALLOWED" : "NO"} /> },
      { key: "digest", header: "archive_digest", width: "14%", cell: (row) => <code>{shortDigest(row.archive_packet_digest)}</code> },
      { key: "action", header: "recommended", cell: (row) => <code>{row.recommended_action}</code> },
    ],
    [],
  );

  const manifestColumns: DenseColumn<UiSemanticValidatorHandoffArchiveManifest>[] = useMemo(
    () => [
      { key: "verified", header: "verified", width: "10%", cell: (row) => <StatusBadge raw={row.verified ? "VERIFIED" : "INVALID"} /> },
      { key: "id", header: "manifest", width: "25%", cell: (row) => <code>{text(row.archive_manifest_id)}</code> },
      { key: "root", header: "archive_root", width: "25%", cell: (row) => <code>{text(row.archive_root)}</code> },
      { key: "count", header: "artifacts", width: "10%", cell: (row) => <code>{text(row.manifest_artifact_count)}</code> },
      { key: "issues", header: "issues", cell: (row) => <span>{row.issue_codes?.join(", ") || "—"}</span> },
    ],
    [],
  );

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR ARCHIVE</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">SEMANTIC · VALIDATOR ARCHIVE</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/archive · read-only verification of external archive manifests against post-custody archive packet digests</p>
      {archive.isLoading && <p className="muted">Loading…</p>}
      {archive.isError && <p className="term-error">{archive.error.message}</p>}

      {archive.data && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Archive inventory" badge={<StatusBadge raw={degraded.length ? "DEGRADED" : "OK"} />} onInspect={() => openInspector({ title: "/ui/semantic-validator-handoff/archive", rawJson: archive.data })}>
              <TermKV rows={[{ k: "schema", v: archive.data.schema_version }, { k: "gates_total", v: String(summary.archive_gate_count_total ?? 0) }, { k: "returned", v: String(summary.archive_gate_count_returned ?? 0) }, { k: "external_manifests", v: String(summary.external_archive_manifest_artifact_count ?? 0) }, { k: "source_custody", v: String(summary.source_custody_gate_count_total ?? 0) }]} />
            </Pane>
            <Pane title="Archive posture">
              <TermKV rows={[{ k: "verified", v: String(summary.verified_archive_manifest_count ?? 0) }, { k: "ready", v: String(summary.ready_for_archive_manifest_count ?? 0) }, { k: "invalid", v: String(summary.invalid_archive_manifest_count ?? 0) }, { k: "blocked_custody", v: String(summary.blocked_custody_count ?? 0) }, { k: "promotion_allowed", v: String(summary.promotion_allowed_count ?? 0) }]} />
            </Pane>
            <Pane title="Selected gate" onInspect={selectedRow ? () => openInspector({ title: "Selected archive gate", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "status", v: text(selectedRow?.archive_status) }, { k: "custody", v: text(selectedRow?.custody_seal_id) }, { k: "manifest", v: text(selectedRow?.archive_manifest_id) }, { k: "root", v: text(selectedRow?.archive_root) }, { k: "packet_digest", v: shortDigest(selectedRow?.archive_packet_digest) }]} />
            </Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-filter-row">
              <label>Status <select value={archiveStatusMode} onChange={(e) => setArchiveStatusMode(e.target.value as ArchiveStatusMode)}>{ARCHIVE_STATUS_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Trust <select value={trustMode} onChange={(e) => setTrustMode(e.target.value as TrustMode)}>{TRUST_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Verified <select value={verifiedMode} onChange={(e) => setVerifiedMode(e.target.value as BoolMode)}>{BOOL_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Experiment <input value={experimentNeedle} onChange={(e) => setExperimentNeedle(e.target.value)} placeholder="contains…" /></label>
              <label>Issue <input value={issueNeedle} onChange={(e) => setIssueNeedle(e.target.value)} placeholder="digest, missing…" /></label>
            </div>
          </Pane>

          <Pane title="Archive gates" badge={<StatusBadge raw={`${rows.length} rows`} />}>
            <DenseTable columns={columns} rows={rows} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => { setSelected(row.__id); setLastDigest(row.archive_packet_digest ?? null); }} empty="No archive gates matched the current filters." />
          </Pane>

          <PaneGrid cols={2}>
            <Pane title="Matched external archive manifests" onInspect={selectedRow ? () => openInspector({ title: "Matched archive manifests", rawJson: selectedManifests(selectedRow) }) : undefined}>
              <DenseTable columns={manifestColumns} rows={selectedManifests(selectedRow)} rowKey={(row, i) => `${row.archive_manifest_id}:${i}`} empty="No external archive manifest matched this custody gate yet." />
            </Pane>
            <Pane title="Archive manifest template" onInspect={selectedRow ? () => openInspector({ title: "External archive manifest template", rawJson: selectedRow.archive_template }) : undefined}>
              <JsonDetails summary="External JSON template" data={selectedRow?.archive_template ?? {}} />
            </Pane>
          </PaneGrid>

          <PaneGrid cols={3}>
            <Pane title="Archive status counts"><TermKV rows={countRows(archive.data.archive_status_counts)} /></Pane>
            <Pane title="Guardrails"><ul className="term-list">{guardrails.map((item) => <li key={item}><code>{item}</code></li>)}</ul></Pane>
            <Pane title="Degraded"><ul className="term-list">{degraded.length ? degraded.map((item) => <li key={item}><code>{item}</code></li>) : <li>—</li>}</ul></Pane>
          </PaneGrid>

          <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/archive JSON" data={archive.data} />
        </>
      )}
    </div>
  );
}
