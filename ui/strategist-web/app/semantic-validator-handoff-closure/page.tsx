"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiSemanticValidatorHandoffClosure, type UiSemanticValidatorHandoffClosureQuery } from "@/hooks/useUiSemanticValidatorHandoffClosure";
import type { UiSemanticValidatorHandoffClosureAttestation, UiSemanticValidatorHandoffClosureRecord } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type ClosureStatusMode = "all" | "CLOSURE_ATTESTATION_RECORDED" | "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION" | "CLOSURE_ATTESTATION_INVALID" | "CLOSURE_ATTESTATION_DIGEST_MISMATCH" | "BLOCKED_ARCHIVE_NOT_VERIFIED";
type TrustMode = "all" | "TRUSTED" | "TRUST_RESTRICTED" | "UNTRUSTED";
type BoolMode = "all" | "yes" | "no";
type ClosureRow = UiSemanticValidatorHandoffClosureRecord & { __id: string };

const CLOSURE_STATUS_MODES: ClosureStatusMode[] = ["all", "CLOSURE_ATTESTATION_RECORDED", "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION", "CLOSURE_ATTESTATION_INVALID", "CLOSURE_ATTESTATION_DIGEST_MISMATCH", "BLOCKED_ARCHIVE_NOT_VERIFIED"];
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
  const t = text(value);
  return t === "—" ? t : `${t.slice(0, 12)}…`;
}

function countRows(counts: Record<string, number> | undefined) {
  return Object.entries(counts ?? {}).map(([k, v]) => ({ k, v: String(v) }));
}

function selectedAttestations(row: ClosureRow | null): UiSemanticValidatorHandoffClosureAttestation[] {
  return row?.matched_closure_attestations ?? [];
}

export default function SemanticValidatorHandoffClosurePage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [closureStatusMode, setClosureStatusMode] = useState<ClosureStatusMode>("all");
  const [trustMode, setTrustMode] = useState<TrustMode>("all");
  const [recordedMode, setRecordedMode] = useState<BoolMode>("all");
  const [experimentNeedle, setExperimentNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiSemanticValidatorHandoffClosureQuery = useMemo(
    () => ({
      closureStatus: closureStatusMode === "all" ? null : closureStatusMode,
      trustBanner: trustMode === "all" ? null : trustMode,
      closureAttestationRecorded: boolParam(recordedMode),
      experimentIdContains: experimentNeedle.trim() || null,
      issueContains: issueNeedle.trim() || null,
      limit: 300,
    }),
    [closureStatusMode, experimentNeedle, issueNeedle, recordedMode, trustMode],
  );

  const closure = useUiSemanticValidatorHandoffClosure(query);
  const summary = closure.data?.summary ?? {};
  const rows = useMemo<ClosureRow[]>(
    () => (closure.data?.closure_gates ?? []).map((row, i) => ({ ...row, __id: `${row.closure_gate_id}:${i}` })),
    [closure.data?.closure_gates],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(closure.data?.degraded);
  const guardrails = asStringArray(closure.data?.guardrails);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "semantic-validator-handoff-closure-counts",
        severity: Number(summary.invalid_closure_attestation_count ?? 0) > 0 || Number(summary.blocked_archive_count ?? 0) > 0 ? "warn" : "ok",
        text: `closure gates=${summary.closure_gate_count_returned ?? 0}/${summary.closure_gate_count_total ?? 0} recorded=${summary.recorded_closure_attestation_count ?? 0} ready=${summary.ready_for_closure_attestation_count ?? 0} invalid=${summary.invalid_closure_attestation_count ?? 0}`,
      },
      {
        id: "semantic-validator-handoff-closure-boundary",
        severity: "info",
        text: "closure attestation verification only · no closure write, archive write, artifact mutation, submission, adjudication, promotion, or execution authority",
      },
    ],
    [summary],
  );
  const ticker = useMemo(
    () => [
      { severity: Number(summary.recorded_closure_attestation_count ?? 0) > 0 ? ("ok" as const) : ("neutral" as const), text: `CLOSE ${summary.recorded_closure_attestation_count ?? 0}` },
      { severity: Number(summary.ready_for_closure_attestation_count ?? 0) > 0 ? ("warn" as const) : ("neutral" as const), text: `READY ${summary.ready_for_closure_attestation_count ?? 0}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<ClosureRow>[] = useMemo(
    () => [
      { key: "trust", header: "trust", width: "9%", cell: (row) => <StatusBadge raw={row.trust_banner ?? "UNKNOWN"} /> },
      { key: "status", header: "closure", width: "27%", cell: (row) => <StatusBadge raw={row.closure_status} /> },
      { key: "experiment", header: "experiment", width: "17%", cell: (row) => <code>{text(row.experiment_id)}</code> },
      { key: "attest", header: "attest", width: "9%", cell: (row) => <code>{row.closure_attestation_count}</code> },
      { key: "recorded", header: "recorded", width: "9%", cell: (row) => <StatusBadge raw={row.closure_attestation_recorded ? "YES" : "NO"} /> },
      { key: "execute", header: "execute", width: "8%", cell: (row) => <StatusBadge raw={row.execution_allowed ? "ALLOWED" : "NO"} /> },
      { key: "digest", header: "closure_digest", width: "14%", cell: (row) => <code>{shortDigest(row.closure_packet_digest)}</code> },
      { key: "action", header: "recommended", cell: (row) => <code>{row.recommended_action}</code> },
    ],
    [],
  );

  const attestationColumns: DenseColumn<UiSemanticValidatorHandoffClosureAttestation>[] = useMemo(
    () => [
      { key: "verified", header: "verified", width: "10%", cell: (row) => <StatusBadge raw={row.verified ? "VERIFIED" : "INVALID"} /> },
      { key: "id", header: "attestation", width: "25%", cell: (row) => <code>{text(row.closure_attestation_id)}</code> },
      { key: "by", header: "closed_by", width: "18%", cell: (row) => <code>{text(row.closed_by)}</code> },
      { key: "disp", header: "disposition", width: "22%", cell: (row) => <code>{text(row.final_disposition)}</code> },
      { key: "issues", header: "issues", cell: (row) => <span>{row.issue_codes?.join(", ") || "—"}</span> },
    ],
    [],
  );

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR CLOSURE</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">SEMANTIC · VALIDATOR CLOSURE</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/closure · read-only verification of external closure attestations against verified archive packet digests</p>
      {closure.isLoading && <p className="muted">Loading…</p>}
      {closure.isError && <p className="term-error">{closure.error.message}</p>}

      {closure.data && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Closure inventory" badge={<StatusBadge raw={degraded.length ? "DEGRADED" : "OK"} />} onInspect={() => openInspector({ title: "/ui/semantic-validator-handoff/closure", rawJson: closure.data })}>
              <TermKV rows={[{ k: "schema", v: closure.data.schema_version }, { k: "gates_total", v: String(summary.closure_gate_count_total ?? 0) }, { k: "returned", v: String(summary.closure_gate_count_returned ?? 0) }, { k: "external_attestations", v: String(summary.external_closure_attestation_artifact_count ?? 0) }, { k: "source_archive", v: String(summary.source_archive_gate_count_total ?? 0) }]} />
            </Pane>
            <Pane title="Closure posture">
              <TermKV rows={[{ k: "recorded", v: String(summary.recorded_closure_attestation_count ?? 0) }, { k: "ready", v: String(summary.ready_for_closure_attestation_count ?? 0) }, { k: "invalid", v: String(summary.invalid_closure_attestation_count ?? 0) }, { k: "blocked_archive", v: String(summary.blocked_archive_count ?? 0) }, { k: "execution_allowed", v: String(summary.execution_allowed_count ?? 0) }]} />
            </Pane>
            <Pane title="Selected gate" onInspect={selectedRow ? () => openInspector({ title: "Selected closure gate", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "status", v: text(selectedRow?.closure_status) }, { k: "archive", v: text(selectedRow?.archive_manifest_id) }, { k: "attestation", v: text(selectedRow?.closure_attestation_id) }, { k: "closed_by", v: text(selectedRow?.closed_by) }, { k: "packet_digest", v: shortDigest(selectedRow?.closure_packet_digest) }]} />
            </Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-filter-row">
              <label>Status <select value={closureStatusMode} onChange={(e) => setClosureStatusMode(e.target.value as ClosureStatusMode)}>{CLOSURE_STATUS_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Trust <select value={trustMode} onChange={(e) => setTrustMode(e.target.value as TrustMode)}>{TRUST_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Recorded <select value={recordedMode} onChange={(e) => setRecordedMode(e.target.value as BoolMode)}>{BOOL_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Experiment <input value={experimentNeedle} onChange={(e) => setExperimentNeedle(e.target.value)} placeholder="contains…" /></label>
              <label>Issue <input value={issueNeedle} onChange={(e) => setIssueNeedle(e.target.value)} placeholder="digest, missing…" /></label>
            </div>
          </Pane>

          <Pane title="Closure gates" badge={<StatusBadge raw={`${rows.length} rows`} />}>
            <DenseTable columns={columns} rows={rows} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => { setSelected(row.__id); setLastDigest(row.closure_packet_digest ?? null); }} empty="No closure gates matched the current filters." />
          </Pane>

          <PaneGrid cols={2}>
            <Pane title="Matched external closure attestations" onInspect={selectedRow ? () => openInspector({ title: "Matched closure attestations", rawJson: selectedAttestations(selectedRow) }) : undefined}>
              <DenseTable columns={attestationColumns} rows={selectedAttestations(selectedRow)} rowKey={(row, i) => `${row.closure_attestation_id}:${i}`} empty="No external closure attestation matched this archive gate yet." />
            </Pane>
            <Pane title="Closure attestation template" onInspect={selectedRow ? () => openInspector({ title: "External closure attestation template", rawJson: selectedRow.closure_template }) : undefined}>
              <JsonDetails summary="External JSON template" data={selectedRow?.closure_template ?? {}} />
            </Pane>
          </PaneGrid>

          <PaneGrid cols={3}>
            <Pane title="Closure status counts"><TermKV rows={countRows(closure.data.closure_status_counts)} /></Pane>
            <Pane title="Guardrails"><ul className="term-list">{guardrails.map((item) => <li key={item}><code>{item}</code></li>)}</ul></Pane>
            <Pane title="Degraded"><ul className="term-list">{degraded.length ? degraded.map((item) => <li key={item}><code>{item}</code></li>) : <li>—</li>}</ul></Pane>
          </PaneGrid>

          <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/closure JSON" data={closure.data} />
        </>
      )}
    </div>
  );
}
