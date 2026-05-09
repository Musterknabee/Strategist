"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiSemanticValidatorHandoffSignoff, type UiSemanticValidatorHandoffSignoffQuery } from "@/hooks/useUiSemanticValidatorHandoffSignoff";
import type { UiSemanticValidatorHandoffSignoffRecord, UiSemanticValidatorHandoffSignoffReceipt } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type SignoffStatusMode = "all" | "OPERATOR_SIGNOFF_RECORDED" | "AWAITING_OPERATOR_SIGNOFF" | "SIGNOFF_INVALID" | "SIGNOFF_DIGEST_MISMATCH" | "BLOCKED_DECISION_NOT_SIGNABLE";
type TrustMode = "all" | "TRUSTED" | "TRUST_RESTRICTED" | "UNTRUSTED";
type BoolMode = "all" | "yes" | "no";
type SignoffRow = UiSemanticValidatorHandoffSignoffRecord & { __id: string };

const SIGNOFF_STATUS_MODES: SignoffStatusMode[] = ["all", "OPERATOR_SIGNOFF_RECORDED", "AWAITING_OPERATOR_SIGNOFF", "SIGNOFF_INVALID", "SIGNOFF_DIGEST_MISMATCH", "BLOCKED_DECISION_NOT_SIGNABLE"];
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

function selectedReceipts(row: SignoffRow | null): UiSemanticValidatorHandoffSignoffReceipt[] {
  return row?.matched_signoffs ?? [];
}

export default function SemanticValidatorHandoffSignoffPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [signoffStatusMode, setSignoffStatusMode] = useState<SignoffStatusMode>("all");
  const [trustMode, setTrustMode] = useState<TrustMode>("all");
  const [recordedMode, setRecordedMode] = useState<BoolMode>("all");
  const [experimentNeedle, setExperimentNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiSemanticValidatorHandoffSignoffQuery = useMemo(
    () => ({
      signoffStatus: signoffStatusMode === "all" ? null : signoffStatusMode,
      trustBanner: trustMode === "all" ? null : trustMode,
      signoffRecorded: boolParam(recordedMode),
      experimentIdContains: experimentNeedle.trim() || null,
      issueContains: issueNeedle.trim() || null,
      limit: 300,
    }),
    [experimentNeedle, issueNeedle, recordedMode, signoffStatusMode, trustMode],
  );

  const signoff = useUiSemanticValidatorHandoffSignoff(query);
  const summary = signoff.data?.summary;
  const rows = useMemo<SignoffRow[]>(
    () => (signoff.data?.signoffs ?? []).map((row, i) => ({ ...row, __id: `${row.signoff_gate_id}:${i}` })),
    [signoff.data?.signoffs],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(signoff.data?.degraded);
  const guardrails = asStringArray(signoff.data?.guardrails);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "semantic-validator-handoff-signoff-counts",
        severity: (summary?.invalid_signoff_count ?? 0) > 0 || (summary?.blocked_decision_count ?? 0) > 0 ? "warn" : "ok",
        text: `signoff gates=${summary?.signoff_gate_count_returned ?? 0}/${summary?.signoff_gate_count_total ?? 0} recorded=${summary?.recorded_signoff_count ?? 0} awaiting=${summary?.awaiting_signoff_count ?? 0} invalid=${summary?.invalid_signoff_count ?? 0}`,
      },
      {
        id: "semantic-validator-handoff-signoff-boundary",
        severity: "info",
        text: "signoff receipt verification only · no signoff write, validator submission, promotion, execution, or artifact mutation authority",
      },
    ],
    [summary],
  );
  const ticker = useMemo(
    () => [
      { severity: (summary?.recorded_signoff_count ?? 0) > 0 ? ("ok" as const) : ("neutral" as const), text: `SIG ${summary?.recorded_signoff_count ?? 0}` },
      { severity: (summary?.awaiting_signoff_count ?? 0) > 0 ? ("warn" as const) : ("neutral" as const), text: `WAIT ${summary?.awaiting_signoff_count ?? 0}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<SignoffRow>[] = useMemo(
    () => [
      { key: "trust", header: "trust", width: "9%", cell: (row) => <StatusBadge raw={row.trust_banner ?? "UNKNOWN"} /> },
      { key: "status", header: "signoff", width: "24%", cell: (row) => <StatusBadge raw={row.signoff_status} /> },
      { key: "experiment", header: "experiment", width: "17%", cell: (row) => <code>{text(row.experiment_id)}</code> },
      { key: "receipts", header: "receipts", width: "8%", cell: (row) => <code>{row.signoff_receipt_count}</code> },
      { key: "recorded", header: "recorded", width: "9%", cell: (row) => <StatusBadge raw={row.signoff_recorded ? "YES" : "NO"} /> },
      { key: "submit", header: "submit", width: "8%", cell: (row) => <StatusBadge raw={row.validator_submission_allowed ? "ALLOWED" : "NO"} /> },
      { key: "digest", header: "packet_digest", width: "14%", cell: (row) => <code>{shortDigest(row.decision_packet_digest)}</code> },
      { key: "action", header: "recommended", cell: (row) => <code>{row.recommended_action}</code> },
    ],
    [],
  );

  const receiptColumns: DenseColumn<UiSemanticValidatorHandoffSignoffReceipt>[] = useMemo(
    () => [
      { key: "verified", header: "verified", width: "10%", cell: (row) => <StatusBadge raw={row.verified ? "VERIFIED" : "INVALID"} /> },
      { key: "id", header: "signoff", width: "22%", cell: (row) => <code>{text(row.signoff_id)}</code> },
      { key: "reviewer", header: "reviewer", width: "20%", cell: (row) => <code>{text(row.human_reviewer_id)}</code> },
      { key: "signed", header: "signed_at", width: "22%", cell: (row) => <code>{text(row.signed_at_utc)}</code> },
      { key: "issues", header: "issues", cell: (row) => <span>{row.issue_codes?.join(", ") || "—"}</span> },
    ],
    [],
  );

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR SIGNOFF</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">SEMANTIC · VALIDATOR SIGNOFF</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/signoff · read-only verification of external operator signoff receipts against decision packet digests</p>
      {signoff.isLoading && <p className="muted">Loading…</p>}
      {signoff.isError && <p className="term-error">{signoff.error.message}</p>}

      {signoff.data && summary && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Signoff inventory" badge={<StatusBadge raw={degraded.length ? "DEGRADED" : "OK"} />} onInspect={() => openInspector({ title: "/ui/semantic-validator-handoff/signoff", rawJson: signoff.data })}>
              <TermKV rows={[{ k: "schema", v: signoff.data.schema_version }, { k: "gates_total", v: String(summary.signoff_gate_count_total) }, { k: "returned", v: String(summary.signoff_gate_count_returned) }, { k: "external_receipts", v: String(summary.external_signoff_artifact_count) }, { k: "source_decisions", v: String(summary.source_decision_count_total) }]} />
            </Pane>
            <Pane title="Signoff posture">
              <TermKV rows={[{ k: "recorded", v: String(summary.recorded_signoff_count) }, { k: "awaiting", v: String(summary.awaiting_signoff_count) }, { k: "invalid", v: String(summary.invalid_signoff_count) }, { k: "blocked_decisions", v: String(summary.blocked_decision_count) }, { k: "validator_submit_allowed", v: String(summary.validator_submission_allowed_count) }]} />
            </Pane>
            <Pane title="Selected gate" onInspect={selectedRow ? () => openInspector({ title: "Selected signoff gate", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "status", v: text(selectedRow?.signoff_status) }, { k: "decision", v: text(selectedRow?.decision_id) }, { k: "signoff", v: text(selectedRow?.signoff_id) }, { k: "reviewer", v: text(selectedRow?.human_reviewer_id) }, { k: "packet_digest", v: shortDigest(selectedRow?.decision_packet_digest) }]} />
            </Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-filter-row">
              <label>Status <select value={signoffStatusMode} onChange={(e) => setSignoffStatusMode(e.target.value as SignoffStatusMode)}>{SIGNOFF_STATUS_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Trust <select value={trustMode} onChange={(e) => setTrustMode(e.target.value as TrustMode)}>{TRUST_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Recorded <select value={recordedMode} onChange={(e) => setRecordedMode(e.target.value as BoolMode)}>{BOOL_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Experiment <input value={experimentNeedle} onChange={(e) => setExperimentNeedle(e.target.value)} placeholder="contains…" /></label>
              <label>Issue <input value={issueNeedle} onChange={(e) => setIssueNeedle(e.target.value)} placeholder="digest, missing…" /></label>
            </div>
          </Pane>

          <Pane title="Signoff gates" badge={<StatusBadge raw={`${rows.length} rows`} />}>
            <DenseTable columns={columns} rows={rows} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => { setSelected(row.__id); setLastDigest(row.decision_packet_digest ?? null); }} empty="No signoff gates matched the current filters." />
          </Pane>

          <PaneGrid cols={2}>
            <Pane title="Matched external receipts" onInspect={selectedRow ? () => openInspector({ title: "Matched signoff receipts", rawJson: selectedReceipts(selectedRow) }) : undefined}>
              <DenseTable columns={receiptColumns} rows={selectedReceipts(selectedRow)} rowKey={(row, i) => `${row.signoff_id}:${i}`} empty="No external signoff receipt matched this decision yet." />
            </Pane>
            <Pane title="Signoff template" onInspect={selectedRow ? () => openInspector({ title: "External signoff template", rawJson: selectedRow.signoff_template }) : undefined}>
              <JsonDetails summary="External JSON template" data={selectedRow?.signoff_template ?? {}} />
            </Pane>
          </PaneGrid>

          <PaneGrid cols={3}>
            <Pane title="Signoff status counts"><TermKV rows={countRows(signoff.data.signoff_status_counts)} /></Pane>
            <Pane title="Guardrails"><ul className="term-list">{guardrails.map((item) => <li key={item}><code>{item}</code></li>)}</ul></Pane>
            <Pane title="Degraded"><ul className="term-list">{degraded.length ? degraded.map((item) => <li key={item}><code>{item}</code></li>) : <li>—</li>}</ul></Pane>
          </PaneGrid>

          <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/signoff JSON" data={signoff.data} />
        </>
      )}
    </div>
  );
}
