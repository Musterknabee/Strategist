"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiSemanticValidatorHandoff, type UiSemanticValidatorHandoffQuery } from "@/hooks/useUiSemanticValidatorHandoff";
import type { UiSemanticValidatorHandoffArtifact } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type ArtifactMode = "all" | "decision_ledger" | "handoff_certificate" | "validator_packet" | "ingress_certificate";
type BoolMode = "all" | "yes" | "no";
type ArtifactRow = UiSemanticValidatorHandoffArtifact & { __id: string };

const ARTIFACT_MODES: ArtifactMode[] = ["all", "decision_ledger", "handoff_certificate", "validator_packet", "ingress_certificate"];
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

export default function SemanticValidatorHandoffPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [artifactMode, setArtifactMode] = useState<ArtifactMode>("all");
  const [verifiedMode, setVerifiedMode] = useState<BoolMode>("all");
  const [handoffMode, setHandoffMode] = useState<BoolMode>("all");
  const [ingressMode, setIngressMode] = useState<BoolMode>("all");
  const [blockerMode, setBlockerMode] = useState<BoolMode>("all");
  const [experimentNeedle, setExperimentNeedle] = useState("");
  const [certificateNeedle, setCertificateNeedle] = useState("");
  const [packetNeedle, setPacketNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiSemanticValidatorHandoffQuery = useMemo(
    () => ({
      artifactKind: artifactMode === "all" ? null : artifactMode,
      verified: boolParam(verifiedMode),
      handoffAllowed: boolParam(handoffMode),
      readyForValidatorIngress: boolParam(ingressMode),
      requireBlockers: boolParam(blockerMode),
      experimentIdContains: experimentNeedle.trim() || null,
      certificateIdContains: certificateNeedle.trim() || null,
      packetIdContains: packetNeedle.trim() || null,
      issueContains: issueNeedle.trim() || null,
      limit: 300,
    }),
    [artifactMode, blockerMode, certificateNeedle, experimentNeedle, handoffMode, ingressMode, issueNeedle, packetNeedle, verifiedMode],
  );

  const handoff = useUiSemanticValidatorHandoff(query);
  const summary = handoff.data?.summary;
  const rows = useMemo<ArtifactRow[]>(
    () => (handoff.data?.artifacts ?? []).map((artifact, i) => ({ ...artifact, __id: `${artifact.artifact_kind}:${artifact.artifact_id}:${i}` })),
    [handoff.data?.artifacts],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(handoff.data?.degraded);
  const guardrails = asStringArray(handoff.data?.guardrails);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "semantic-validator-handoff-counts",
        severity: (summary?.blocked_artifact_count ?? 0) > 0 || (summary?.invalid_artifact_count ?? 0) > 0 ? "warn" : "ok",
        text: `validator_handoff artifacts=${summary?.artifact_count_returned ?? 0}/${summary?.artifact_count_total ?? 0} verified=${summary?.verified_artifact_count ?? 0} allowed=${summary?.handoff_allowed_count ?? 0} ingress_ready=${summary?.validator_ingress_ready_count ?? 0} blocked=${summary?.blocked_artifact_count ?? 0}`,
      },
      {
        id: "semantic-validator-handoff-boundary",
        severity: "info",
        text: "read-plane only · no validator submission, adjudication, promotion, ledger mutation, or execution authority",
      },
    ],
    [summary],
  );
  const ticker = useMemo(
    () => [
      { severity: (summary?.validator_ingress_ready_count ?? 0) > 0 ? ("ok" as const) : ("neutral" as const), text: `V-HAND ${summary?.artifact_count_returned ?? 0}` },
      { severity: (summary?.blocked_artifact_count ?? 0) > 0 ? ("warn" as const) : ("neutral" as const), text: `BLK ${summary?.blocked_artifact_count ?? 0}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<ArtifactRow>[] = useMemo(
    () => [
      { key: "kind", header: "kind", width: "16%", cell: (row) => <StatusBadge raw={row.artifact_kind} /> },
      { key: "experiment", header: "experiment", width: "18%", cell: (row) => <code>{row.experiment_id}</code> },
      { key: "artifact", header: "artifact", width: "18%", cell: (row) => <code>{row.artifact_id}</code> },
      { key: "verified", header: "verified", width: "10%", cell: (row) => <StatusBadge raw={row.verified ? "VERIFIED" : "FAILED"} /> },
      { key: "handoff", header: "handoff", width: "10%", cell: (row) => <StatusBadge raw={row.handoff_allowed ? "ALLOWED" : "BLOCKED"} /> },
      { key: "ingress", header: "ingress", width: "10%", cell: (row) => <StatusBadge raw={row.ready_for_validator_ingress ? "READY" : "—"} /> },
      { key: "action", header: "recommended", cell: (row) => <code>{row.recommended_action}</code> },
    ],
    [],
  );

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff · release ledgers, handoff certificates, validator packets, and ingress certificates</p>
      {handoff.isLoading && <p className="muted">Loading…</p>}
      {handoff.isError && <p className="term-error">{handoff.error.message}</p>}

      {handoff.data && summary && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Validator handoff inventory" badge={<StatusBadge raw={degraded.length ? "DEGRADED" : "OK"} />} onInspect={() => openInspector({ title: "/ui/semantic-validator-handoff", rawJson: handoff.data })}>
              <TermKV rows={[{ k: "schema", v: handoff.data.schema_version }, { k: "total", v: String(summary.artifact_count_total) }, { k: "filtered", v: String(summary.artifact_count_filtered) }, { k: "returned", v: String(summary.artifact_count_returned) }, { k: "invalid", v: String(summary.invalid_artifact_count) }]} />
            </Pane>
            <Pane title="Handoff posture">
              <TermKV rows={[{ k: "verified", v: String(summary.verified_artifact_count) }, { k: "handoff_allowed", v: String(summary.handoff_allowed_count) }, { k: "ingress_ready", v: String(summary.validator_ingress_ready_count) }, { k: "blocked", v: String(summary.blocked_artifact_count) }, { k: "latest_experiment", v: text(summary.latest_experiment_id) }]} />
            </Pane>
            <Pane title="Selected artifact" onInspect={selectedRow ? () => openInspector({ title: "Semantic validator handoff artifact", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "kind", v: selectedRow?.artifact_kind ?? "—" }, { k: "artifact", v: selectedRow?.artifact_id ?? "—" }, { k: "ledger", v: selectedRow?.ledger_id ?? "—" }, { k: "certificate", v: selectedRow?.certificate_id ?? "—" }, { k: "packet", v: selectedRow?.packet_id ?? "—" }, { k: "payload", v: shortDigest(selectedRow?.payload_checksum) }, { k: "file_sha", v: shortDigest(selectedRow?.artifact_sha256) }]} />
              {(selectedRow?.payload_checksum || selectedRow?.artifact_sha256) && <button type="button" className="term-button" style={{ marginTop: "6px" }} onClick={() => setLastDigest(selectedRow.payload_checksum ?? selectedRow.artifact_sha256 ?? null)}>Copy digest target</button>}
            </Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-toolbar">
              {ARTIFACT_MODES.map((mode) => <button key={mode} type="button" className={artifactMode === mode ? "term-chip active" : "term-chip"} onClick={() => setArtifactMode(mode)}>{mode}</button>)}
              <select className="term-input" value={verifiedMode} onChange={(e) => setVerifiedMode(e.target.value as BoolMode)} aria-label="verified filter" style={{ width: "130px" }}>{BOOL_MODES.map((m) => <option key={m} value={m}>verified:{m}</option>)}</select>
              <select className="term-input" value={handoffMode} onChange={(e) => setHandoffMode(e.target.value as BoolMode)} aria-label="handoff filter" style={{ width: "140px" }}>{BOOL_MODES.map((m) => <option key={m} value={m}>handoff:{m}</option>)}</select>
              <select className="term-input" value={ingressMode} onChange={(e) => setIngressMode(e.target.value as BoolMode)} aria-label="ingress filter" style={{ width: "135px" }}>{BOOL_MODES.map((m) => <option key={m} value={m}>ingress:{m}</option>)}</select>
              <select className="term-input" value={blockerMode} onChange={(e) => setBlockerMode(e.target.value as BoolMode)} aria-label="blocker filter" style={{ width: "135px" }}>{BOOL_MODES.map((m) => <option key={m} value={m}>blocker:{m}</option>)}</select>
              <label className="term-field"><span>experiment</span><input className="term-input" value={experimentNeedle} onChange={(e) => setExperimentNeedle(e.target.value)} placeholder="contains" style={{ width: "185px" }} /></label>
              <label className="term-field"><span>certificate</span><input className="term-input" value={certificateNeedle} onChange={(e) => setCertificateNeedle(e.target.value)} placeholder="contains" style={{ width: "185px" }} /></label>
              <label className="term-field"><span>packet</span><input className="term-input" value={packetNeedle} onChange={(e) => setPacketNeedle(e.target.value)} placeholder="contains" style={{ width: "165px" }} /></label>
              <label className="term-field"><span>issue</span><input className="term-input" value={issueNeedle} onChange={(e) => setIssueNeedle(e.target.value)} placeholder="checksum/blocker" style={{ width: "180px" }} /></label>
            </div>
          </Pane>

          <Pane title="Semantic validator handoff artifacts">
            <DenseTable<ArtifactRow> rows={rows} columns={columns} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => setSelected(row.__id)} empty="No semantic validator handoff artifacts matched the current filters." />
          </Pane>

          <PaneGrid cols={3}>
            <Pane title="Artifact kinds"><TermKV rows={countRows(handoff.data.artifact_kind_counts)} /></Pane>
            <Pane title="Recommended actions"><TermKV rows={countRows(handoff.data.recommended_action_counts)} /></Pane>
            <Pane title="Terminal decisions"><TermKV rows={countRows(handoff.data.terminal_decision_counts)} /></Pane>
          </PaneGrid>

          {selectedRow && (selectedRow.blocker_codes.length > 0 || selectedRow.warning_codes.length > 0 || selectedRow.issue_codes.length > 0) && (
            <Pane title="Selected artifact issues" onInspect={() => openInspector({ title: "Semantic validator handoff issues", rawJson: { blocker_codes: selectedRow.blocker_codes, warning_codes: selectedRow.warning_codes, issue_codes: selectedRow.issue_codes, verification: selectedRow.verification } })}>
              <ul className="term-list">{[...selectedRow.blocker_codes.map((x) => `BLOCKER · ${x}`), ...selectedRow.warning_codes.map((x) => `WARNING · ${x}`), ...selectedRow.issue_codes.map((x) => `ISSUE · ${x}`)].slice(0, 14).map((line) => <li key={line}>{line}</li>)}</ul>
            </Pane>
          )}

          {degraded.length > 0 && <Pane title="Degraded signals" badge={<StatusBadge raw="DEGRADED" />} onInspect={() => openInspector({ title: "Semantic validator handoff degraded", rawJson: { degraded, invalid_artifacts: handoff.data?.invalid_artifacts } })}><ul className="term-list">{degraded.map((line) => <li key={line}>{line}</li>)}</ul></Pane>}

          <Pane title="Guardrails"><ul className="term-list">{guardrails.map((line) => <li key={line}>{line}</li>)}</ul></Pane>
          <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff JSON" data={handoff.data} />
        </>
      )}
    </div>
  );
}
