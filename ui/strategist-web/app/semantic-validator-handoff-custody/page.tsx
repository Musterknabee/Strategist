"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiSemanticValidatorHandoffCustody, type UiSemanticValidatorHandoffCustodyQuery } from "@/hooks/useUiSemanticValidatorHandoffCustody";
import type { UiSemanticValidatorHandoffCustodyRecord, UiSemanticValidatorHandoffCustodySeal } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type CustodyStatusMode = "all" | "CUSTODY_SEAL_RECORDED" | "READY_FOR_EXTERNAL_CUSTODY_SEAL" | "CUSTODY_SEAL_INVALID" | "CUSTODY_SEAL_DIGEST_MISMATCH" | "BLOCKED_SIGNOFF_NOT_RECORDED";
type TrustMode = "all" | "TRUSTED" | "TRUST_RESTRICTED" | "UNTRUSTED";
type BoolMode = "all" | "yes" | "no";
type CustodyRow = UiSemanticValidatorHandoffCustodyRecord & { __id: string };

const CUSTODY_STATUS_MODES: CustodyStatusMode[] = ["all", "CUSTODY_SEAL_RECORDED", "READY_FOR_EXTERNAL_CUSTODY_SEAL", "CUSTODY_SEAL_INVALID", "CUSTODY_SEAL_DIGEST_MISMATCH", "BLOCKED_SIGNOFF_NOT_RECORDED"];
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

function selectedSeals(row: CustodyRow | null): UiSemanticValidatorHandoffCustodySeal[] {
  return row?.matched_custody_seals ?? [];
}

export default function SemanticValidatorHandoffCustodyPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [custodyStatusMode, setCustodyStatusMode] = useState<CustodyStatusMode>("all");
  const [trustMode, setTrustMode] = useState<TrustMode>("all");
  const [recordedMode, setRecordedMode] = useState<BoolMode>("all");
  const [experimentNeedle, setExperimentNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiSemanticValidatorHandoffCustodyQuery = useMemo(
    () => ({
      custodyStatus: custodyStatusMode === "all" ? null : custodyStatusMode,
      trustBanner: trustMode === "all" ? null : trustMode,
      custodySealRecorded: boolParam(recordedMode),
      experimentIdContains: experimentNeedle.trim() || null,
      issueContains: issueNeedle.trim() || null,
      limit: 300,
    }),
    [custodyStatusMode, experimentNeedle, issueNeedle, recordedMode, trustMode],
  );

  const custody = useUiSemanticValidatorHandoffCustody(query);
  const summary = custody.data?.summary ?? {};
  const rows = useMemo<CustodyRow[]>(
    () => (custody.data?.custody_gates ?? []).map((row, i) => ({ ...row, __id: `${row.custody_gate_id}:${i}` })),
    [custody.data?.custody_gates],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(custody.data?.degraded);
  const guardrails = asStringArray(custody.data?.guardrails);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "semantic-validator-handoff-custody-counts",
        severity: Number(summary.invalid_custody_seal_count ?? 0) > 0 || Number(summary.blocked_signoff_count ?? 0) > 0 ? "warn" : "ok",
        text: `custody gates=${summary.custody_gate_count_returned ?? 0}/${summary.custody_gate_count_total ?? 0} recorded=${summary.recorded_custody_seal_count ?? 0} ready=${summary.ready_for_custody_seal_count ?? 0} invalid=${summary.invalid_custody_seal_count ?? 0}`,
      },
      {
        id: "semantic-validator-handoff-custody-boundary",
        severity: "info",
        text: "custody seal verification only · no seal write, archive write, artifact mutation, submission, promotion, or execution authority",
      },
    ],
    [summary],
  );
  const ticker = useMemo(
    () => [
      { severity: Number(summary.recorded_custody_seal_count ?? 0) > 0 ? ("ok" as const) : ("neutral" as const), text: `CUST ${summary.recorded_custody_seal_count ?? 0}` },
      { severity: Number(summary.ready_for_custody_seal_count ?? 0) > 0 ? ("warn" as const) : ("neutral" as const), text: `READY ${summary.ready_for_custody_seal_count ?? 0}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<CustodyRow>[] = useMemo(
    () => [
      { key: "trust", header: "trust", width: "9%", cell: (row) => <StatusBadge raw={row.trust_banner ?? "UNKNOWN"} /> },
      { key: "status", header: "custody", width: "24%", cell: (row) => <StatusBadge raw={row.custody_status} /> },
      { key: "experiment", header: "experiment", width: "17%", cell: (row) => <code>{text(row.experiment_id)}</code> },
      { key: "seals", header: "seals", width: "8%", cell: (row) => <code>{row.custody_seal_count}</code> },
      { key: "recorded", header: "recorded", width: "9%", cell: (row) => <StatusBadge raw={row.custody_seal_recorded ? "YES" : "NO"} /> },
      { key: "archive", header: "archive", width: "8%", cell: (row) => <StatusBadge raw={row.archive_write_allowed ? "ALLOWED" : "NO"} /> },
      { key: "digest", header: "custody_digest", width: "14%", cell: (row) => <code>{shortDigest(row.custody_packet_digest)}</code> },
      { key: "action", header: "recommended", cell: (row) => <code>{row.recommended_action}</code> },
    ],
    [],
  );

  const sealColumns: DenseColumn<UiSemanticValidatorHandoffCustodySeal>[] = useMemo(
    () => [
      { key: "verified", header: "verified", width: "10%", cell: (row) => <StatusBadge raw={row.verified ? "VERIFIED" : "INVALID"} /> },
      { key: "id", header: "seal", width: "24%", cell: (row) => <code>{text(row.custody_seal_id)}</code> },
      { key: "custodian", header: "custodian", width: "20%", cell: (row) => <code>{text(row.human_custodian_id)}</code> },
      { key: "sealed", header: "sealed_at", width: "22%", cell: (row) => <code>{text(row.sealed_at_utc)}</code> },
      { key: "issues", header: "issues", cell: (row) => <span>{row.issue_codes?.join(", ") || "—"}</span> },
    ],
    [],
  );

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR CUSTODY</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">SEMANTIC · VALIDATOR CUSTODY</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/custody · read-only verification of external custody seals against signoff custody packet digests</p>
      {custody.isLoading && <p className="muted">Loading…</p>}
      {custody.isError && <p className="term-error">{custody.error.message}</p>}

      {custody.data && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Custody inventory" badge={<StatusBadge raw={degraded.length ? "DEGRADED" : "OK"} />} onInspect={() => openInspector({ title: "/ui/semantic-validator-handoff/custody", rawJson: custody.data })}>
              <TermKV rows={[{ k: "schema", v: custody.data.schema_version }, { k: "gates_total", v: String(summary.custody_gate_count_total ?? 0) }, { k: "returned", v: String(summary.custody_gate_count_returned ?? 0) }, { k: "external_seals", v: String(summary.external_custody_seal_artifact_count ?? 0) }, { k: "source_signoffs", v: String(summary.source_signoff_gate_count_total ?? 0) }]} />
            </Pane>
            <Pane title="Custody posture">
              <TermKV rows={[{ k: "recorded", v: String(summary.recorded_custody_seal_count ?? 0) }, { k: "ready", v: String(summary.ready_for_custody_seal_count ?? 0) }, { k: "invalid", v: String(summary.invalid_custody_seal_count ?? 0) }, { k: "blocked_signoff", v: String(summary.blocked_signoff_count ?? 0) }, { k: "archive_write_allowed", v: String(summary.archive_write_allowed_count ?? 0) }]} />
            </Pane>
            <Pane title="Selected gate" onInspect={selectedRow ? () => openInspector({ title: "Selected custody gate", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "status", v: text(selectedRow?.custody_status) }, { k: "signoff", v: text(selectedRow?.signoff_id) }, { k: "seal", v: text(selectedRow?.custody_seal_id) }, { k: "custodian", v: text(selectedRow?.human_custodian_id) }, { k: "packet_digest", v: shortDigest(selectedRow?.custody_packet_digest) }]} />
            </Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-filter-row">
              <label>Status <select value={custodyStatusMode} onChange={(e) => setCustodyStatusMode(e.target.value as CustodyStatusMode)}>{CUSTODY_STATUS_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Trust <select value={trustMode} onChange={(e) => setTrustMode(e.target.value as TrustMode)}>{TRUST_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Recorded <select value={recordedMode} onChange={(e) => setRecordedMode(e.target.value as BoolMode)}>{BOOL_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Experiment <input value={experimentNeedle} onChange={(e) => setExperimentNeedle(e.target.value)} placeholder="contains…" /></label>
              <label>Issue <input value={issueNeedle} onChange={(e) => setIssueNeedle(e.target.value)} placeholder="digest, missing…" /></label>
            </div>
          </Pane>

          <Pane title="Custody gates" badge={<StatusBadge raw={`${rows.length} rows`} />}>
            <DenseTable columns={columns} rows={rows} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => { setSelected(row.__id); setLastDigest(row.custody_packet_digest ?? null); }} empty="No custody gates matched the current filters." />
          </Pane>

          <PaneGrid cols={2}>
            <Pane title="Matched external custody seals" onInspect={selectedRow ? () => openInspector({ title: "Matched custody seals", rawJson: selectedSeals(selectedRow) }) : undefined}>
              <DenseTable columns={sealColumns} rows={selectedSeals(selectedRow)} rowKey={(row, i) => `${row.custody_seal_id}:${i}`} empty="No external custody seal matched this signoff yet." />
            </Pane>
            <Pane title="Custody seal template" onInspect={selectedRow ? () => openInspector({ title: "External custody seal template", rawJson: selectedRow.custody_template }) : undefined}>
              <JsonDetails summary="External JSON template" data={selectedRow?.custody_template ?? {}} />
            </Pane>
          </PaneGrid>

          <PaneGrid cols={3}>
            <Pane title="Custody status counts"><TermKV rows={countRows(custody.data.custody_status_counts)} /></Pane>
            <Pane title="Guardrails"><ul className="term-list">{guardrails.map((item) => <li key={item}><code>{item}</code></li>)}</ul></Pane>
            <Pane title="Degraded"><ul className="term-list">{degraded.length ? degraded.map((item) => <li key={item}><code>{item}</code></li>) : <li>—</li>}</ul></Pane>
          </PaneGrid>

          <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/custody JSON" data={custody.data} />
        </>
      )}
    </div>
  );
}
