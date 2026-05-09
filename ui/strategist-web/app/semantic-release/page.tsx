"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiSemanticRelease, type UiSemanticReleaseQuery } from "@/hooks/useUiSemanticRelease";
import type { UiSemanticReleaseArtifact } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type ArtifactMode = "all" | "release_index" | "release_capsule" | "decision_record";
type ReadyMode = "all" | "ready" | "blocked";
type VerifiedMode = "all" | "verified" | "failed";
type BlockerMode = "all" | "blockers" | "clear";
type ArtifactRow = UiSemanticReleaseArtifact & { __id: string };

const ARTIFACT_MODES: ArtifactMode[] = ["all", "release_index", "release_capsule", "decision_record"];
const READY_MODES: ReadyMode[] = ["all", "ready", "blocked"];
const VERIFIED_MODES: VerifiedMode[] = ["all", "verified", "failed"];
const BLOCKER_MODES: BlockerMode[] = ["all", "blockers", "clear"];

function text(value: unknown, fallback = "—"): string {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function shortDigest(value: string | null | undefined): string {
  if (!value) return "—";
  return value.length > 18 ? `${value.slice(0, 10)}…${value.slice(-6)}` : value;
}

function countRows(counts: Record<string, number> | undefined): { k: string; v: string }[] {
  return Object.entries(counts ?? {})
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, 10)
    .map(([k, v]) => ({ k, v: String(v) }));
}

function readyParam(mode: ReadyMode): boolean | null {
  if (mode === "ready") return true;
  if (mode === "blocked") return false;
  return null;
}

function verifiedParam(mode: VerifiedMode): boolean | null {
  if (mode === "verified") return true;
  if (mode === "failed") return false;
  return null;
}

function blockerParam(mode: BlockerMode): boolean | null {
  if (mode === "blockers") return true;
  if (mode === "clear") return false;
  return null;
}

export default function SemanticReleasePage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [artifactMode, setArtifactMode] = useState<ArtifactMode>("all");
  const [readyMode, setReadyMode] = useState<ReadyMode>("all");
  const [verifiedMode, setVerifiedMode] = useState<VerifiedMode>("all");
  const [blockerMode, setBlockerMode] = useState<BlockerMode>("all");
  const [experimentNeedle, setExperimentNeedle] = useState("");
  const [bundleNeedle, setBundleNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiSemanticReleaseQuery = useMemo(
    () => ({
      artifactKind: artifactMode === "all" ? null : artifactMode,
      readyForAdjudication: readyParam(readyMode),
      verified: verifiedParam(verifiedMode),
      requireBlockers: blockerParam(blockerMode),
      experimentIdContains: experimentNeedle.trim() || null,
      bundleIdContains: bundleNeedle.trim() || null,
      issueContains: issueNeedle.trim() || null,
      limit: 300,
    }),
    [artifactMode, blockerMode, bundleNeedle, experimentNeedle, issueNeedle, readyMode, verifiedMode],
  );

  const release = useUiSemanticRelease(query);
  const summary = release.data?.summary;
  const rows = useMemo<ArtifactRow[]>(
    () => (release.data?.artifacts ?? []).map((artifact, i) => ({ ...artifact, __id: `${artifact.artifact_kind}:${artifact.artifact_id}:${i}` })),
    [release.data?.artifacts],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(release.data?.degraded);
  const guardrails = asStringArray(release.data?.guardrails);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "semantic-release-counts",
        severity: (summary?.blocked_artifact_count ?? 0) > 0 || (summary?.invalid_artifact_count ?? 0) > 0 ? "warn" : "ok",
        text: `semantic_release artifacts=${summary?.artifact_count_returned ?? 0}/${summary?.artifact_count_total ?? 0} ready=${summary?.ready_for_adjudication_count ?? 0} verified=${summary?.verified_artifact_count ?? 0} blocked=${summary?.blocked_artifact_count ?? 0}`,
      },
      {
        id: "semantic-release-boundary",
        severity: "info",
        text: "read-plane only · verifies archived semantic release handoff artifacts; no adjudication, promotion, or mutation authority",
      },
    ],
    [summary],
  );
  const ticker = useMemo(
    () => [
      { severity: (summary?.decision_allowed_count ?? 0) > 0 ? ("ok" as const) : ("neutral" as const), text: `SEM ${summary?.artifact_count_returned ?? 0}` },
      { severity: (summary?.blocked_artifact_count ?? 0) > 0 ? ("warn" as const) : ("neutral" as const), text: `BLK ${summary?.blocked_artifact_count ?? 0}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<ArtifactRow>[] = useMemo(
    () => [
      { key: "kind", header: "kind", width: "14%", cell: (row) => <StatusBadge raw={row.artifact_kind} /> },
      { key: "experiment", header: "experiment", width: "19%", cell: (row) => <code>{row.experiment_id}</code> },
      { key: "artifact", header: "artifact", width: "18%", cell: (row) => <code>{row.artifact_id}</code> },
      { key: "ready", header: "ready", width: "9%", cell: (row) => <StatusBadge raw={row.ready_for_adjudication ? "READY" : "BLOCKED"} /> },
      { key: "verified", header: "verified", width: "10%", cell: (row) => <StatusBadge raw={row.verified ? "VERIFIED" : "FAILED"} /> },
      { key: "issues", header: "issues", width: "8%", cell: (row) => `${row.blocker_codes.length}B/${row.warning_codes.length}W` },
      { key: "action", header: "recommended", cell: (row) => <code>{row.recommended_action}</code> },
    ],
    [],
  );

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">SEMANTIC · RELEASE HANDOFF</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">SEMANTIC · RELEASE HANDOFF</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-release · semantic bundle release index, capsule, and terminal decision-record evidence</p>
      {release.isLoading && <p className="muted">Loading…</p>}
      {release.isError && <p className="term-error">{release.error.message}</p>}

      {release.data && summary && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Handoff inventory" badge={<StatusBadge raw={degraded.length ? "DEGRADED" : "OK"} />} onInspect={() => openInspector({ title: "/ui/semantic-release", rawJson: release.data })}>
              <TermKV rows={[{ k: "schema", v: release.data.schema_version }, { k: "total", v: String(summary.artifact_count_total) }, { k: "filtered", v: String(summary.artifact_count_filtered) }, { k: "returned", v: String(summary.artifact_count_returned) }, { k: "invalid", v: String(summary.invalid_artifact_count) }]} />
            </Pane>
            <Pane title="Release posture">
              <TermKV rows={[{ k: "ready", v: String(summary.ready_for_adjudication_count) }, { k: "verified", v: String(summary.verified_artifact_count) }, { k: "blocked", v: String(summary.blocked_artifact_count) }, { k: "decision_allowed", v: String(summary.decision_allowed_count) }, { k: "latest_experiment", v: text(summary.latest_experiment_id) }]} />
            </Pane>
            <Pane title="Selected artifact" onInspect={selectedRow ? () => openInspector({ title: "Semantic release artifact", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "kind", v: selectedRow?.artifact_kind ?? "—" }, { k: "artifact", v: selectedRow?.artifact_id ?? "—" }, { k: "bundle", v: selectedRow?.bundle_id ?? "—" }, { k: "payload", v: shortDigest(selectedRow?.payload_checksum) }, { k: "file_sha", v: shortDigest(selectedRow?.artifact_sha256) }]} />
              {(selectedRow?.payload_checksum || selectedRow?.artifact_sha256) && <button type="button" className="term-button" style={{ marginTop: "6px" }} onClick={() => setLastDigest(selectedRow.payload_checksum ?? selectedRow.artifact_sha256 ?? null)}>Copy digest target</button>}
            </Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-toolbar">
              {ARTIFACT_MODES.map((mode) => <button key={mode} type="button" className={artifactMode === mode ? "term-chip active" : "term-chip"} onClick={() => setArtifactMode(mode)}>{mode}</button>)}
              <select className="term-input" value={readyMode} onChange={(e) => setReadyMode(e.target.value as ReadyMode)} aria-label="ready filter" style={{ width: "130px" }}>{READY_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select>
              <select className="term-input" value={verifiedMode} onChange={(e) => setVerifiedMode(e.target.value as VerifiedMode)} aria-label="verified filter" style={{ width: "145px" }}>{VERIFIED_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select>
              <select className="term-input" value={blockerMode} onChange={(e) => setBlockerMode(e.target.value as BlockerMode)} aria-label="blocker filter" style={{ width: "145px" }}>{BLOCKER_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select>
              <label className="term-field"><span>experiment</span><input className="term-input" value={experimentNeedle} onChange={(e) => setExperimentNeedle(e.target.value)} placeholder="contains" style={{ width: "190px" }} /></label>
              <label className="term-field"><span>bundle</span><input className="term-input" value={bundleNeedle} onChange={(e) => setBundleNeedle(e.target.value)} placeholder="contains" style={{ width: "170px" }} /></label>
              <label className="term-field"><span>issue</span><input className="term-input" value={issueNeedle} onChange={(e) => setIssueNeedle(e.target.value)} placeholder="checksum/blocker" style={{ width: "190px" }} /></label>
            </div>
          </Pane>

          <Pane title="Semantic release artifacts">
            <DenseTable<ArtifactRow> rows={rows} columns={columns} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => setSelected(row.__id)} empty="No semantic release artifacts matched the current filters." />
          </Pane>

          <PaneGrid cols={3}>
            <Pane title="Artifact kinds"><TermKV rows={countRows(release.data.artifact_kind_counts)} /></Pane>
            <Pane title="Recommended actions"><TermKV rows={countRows(release.data.recommended_action_counts)} /></Pane>
            <Pane title="Decision counts"><TermKV rows={countRows(release.data.decision_counts)} /></Pane>
          </PaneGrid>

          {selectedRow && (selectedRow.blocker_codes.length > 0 || selectedRow.warning_codes.length > 0 || selectedRow.issue_codes.length > 0) && (
            <Pane title="Selected artifact issues" onInspect={() => openInspector({ title: "Semantic release issues", rawJson: { blocker_codes: selectedRow.blocker_codes, warning_codes: selectedRow.warning_codes, issue_codes: selectedRow.issue_codes, verification: selectedRow.verification } })}>
              <ul className="term-list">{[...selectedRow.blocker_codes.map((x) => `BLOCKER · ${x}`), ...selectedRow.warning_codes.map((x) => `WARNING · ${x}`), ...selectedRow.issue_codes.map((x) => `ISSUE · ${x}`)].slice(0, 14).map((line) => <li key={line}>{line}</li>)}</ul>
            </Pane>
          )}

          {degraded.length > 0 && <Pane title="Degraded signals" badge={<StatusBadge raw="DEGRADED" />} onInspect={() => openInspector({ title: "Semantic release degraded", rawJson: { degraded, invalid_artifacts: release.data?.invalid_artifacts } })}><ul className="term-list">{degraded.map((line) => <li key={line}>{line}</li>)}</ul></Pane>}

          <Pane title="Guardrails"><ul className="term-list">{guardrails.map((line) => <li key={line}>{line}</li>)}</ul></Pane>
          <JsonDetails summary="Drilldown: /ui/semantic-release JSON" data={release.data} />
        </>
      )}
    </div>
  );
}
