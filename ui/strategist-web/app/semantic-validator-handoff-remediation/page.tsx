"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiSemanticValidatorHandoffRemediation, type UiSemanticValidatorHandoffRemediationQuery } from "@/hooks/useUiSemanticValidatorHandoffRemediation";
import type { UiSemanticValidatorHandoffRemediationRecord, UiSemanticValidatorHandoffRemediationStep } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type ChainStatusMode = "all" | "READY" | "BROKEN" | "INCOMPLETE";
type RemediationStatusMode = "all" | "READY_NO_ACTION" | "ACTION_REQUIRED" | "EVIDENCE_REPAIR_REQUIRED" | "LINEAGE_RECONSTRUCTION_REQUIRED";
type SeverityMode = "all" | "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "NONE";
type BoolMode = "all" | "yes" | "no";
type RemediationRow = UiSemanticValidatorHandoffRemediationRecord & { __id: string };

const CHAIN_STATUS_MODES: ChainStatusMode[] = ["all", "READY", "BROKEN", "INCOMPLETE"];
const REMEDIATION_STATUS_MODES: RemediationStatusMode[] = ["all", "READY_NO_ACTION", "ACTION_REQUIRED", "EVIDENCE_REPAIR_REQUIRED", "LINEAGE_RECONSTRUCTION_REQUIRED"];
const SEVERITY_MODES: SeverityMode[] = ["all", "CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"];
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

function stepRows(row: RemediationRow | null): UiSemanticValidatorHandoffRemediationStep[] {
  return row?.remediation_steps ?? [];
}

export default function SemanticValidatorHandoffRemediationPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [chainStatusMode, setChainStatusMode] = useState<ChainStatusMode>("all");
  const [remediationStatusMode, setRemediationStatusMode] = useState<RemediationStatusMode>("all");
  const [severityMode, setSeverityMode] = useState<SeverityMode>("all");
  const [operatorActionMode, setOperatorActionMode] = useState<BoolMode>("all");
  const [experimentNeedle, setExperimentNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiSemanticValidatorHandoffRemediationQuery = useMemo(
    () => ({
      chainStatus: chainStatusMode === "all" ? null : chainStatusMode,
      remediationStatus: remediationStatusMode === "all" ? null : remediationStatusMode,
      severity: severityMode === "all" ? null : severityMode,
      requireOperatorAction: boolParam(operatorActionMode),
      experimentIdContains: experimentNeedle.trim() || null,
      issueContains: issueNeedle.trim() || null,
      limit: 300,
    }),
    [chainStatusMode, experimentNeedle, issueNeedle, operatorActionMode, remediationStatusMode, severityMode],
  );

  const remediation = useUiSemanticValidatorHandoffRemediation(query);
  const summary = remediation.data?.summary;
  const rows = useMemo<RemediationRow[]>(
    () => (remediation.data?.remediations ?? []).map((row, i) => ({ ...row, __id: `${row.remediation_id}:${i}` })),
    [remediation.data?.remediations],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(remediation.data?.degraded);
  const guardrails = asStringArray(remediation.data?.guardrails);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "semantic-validator-handoff-remediation-counts",
        severity: (summary?.critical_count ?? 0) > 0 || (summary?.action_required_count ?? 0) > 0 ? "warn" : "ok",
        text: `remediation records=${summary?.remediation_count_returned ?? 0}/${summary?.remediation_count_total ?? 0} action_required=${summary?.action_required_count ?? 0} critical=${summary?.critical_count ?? 0}`,
      },
      {
        id: "semantic-validator-handoff-remediation-boundary",
        severity: "info",
        text: "read-plane repair guidance only · no artifact regeneration, validator submission, promotion, or execution authority",
      },
    ],
    [summary],
  );
  const ticker = useMemo(
    () => [
      { severity: (summary?.action_required_count ?? 0) > 0 ? ("warn" as const) : ("ok" as const), text: `REM ${summary?.remediation_count_returned ?? 0}` },
      { severity: (summary?.critical_count ?? 0) > 0 ? ("warn" as const) : ("neutral" as const), text: `CRIT ${summary?.critical_count ?? 0}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<RemediationRow>[] = useMemo(
    () => [
      { key: "severity", header: "severity", width: "9%", cell: (row) => <StatusBadge raw={row.severity} /> },
      { key: "status", header: "remediation", width: "18%", cell: (row) => <StatusBadge raw={row.remediation_status} /> },
      { key: "chain", header: "chain", width: "10%", cell: (row) => <StatusBadge raw={row.chain_status ?? "UNKNOWN"} /> },
      { key: "experiment", header: "experiment", width: "18%", cell: (row) => <code>{text(row.experiment_id)}</code> },
      { key: "steps", header: "steps", width: "7%", cell: (row) => <code>{row.remediation_step_count}</code> },
      { key: "priority", header: "priority", width: "7%", cell: (row) => <code>{row.priority_score}</code> },
      { key: "ingress", header: "ingress", width: "9%", cell: (row) => <StatusBadge raw={row.validator_ingress_blocked ? "BLOCKED" : "READY"} /> },
      { key: "action", header: "recommended", cell: (row) => <code>{row.recommended_action}</code> },
    ],
    [],
  );

  const stepColumns: DenseColumn<UiSemanticValidatorHandoffRemediationStep>[] = useMemo(
    () => [
      { key: "severity", header: "severity", width: "10%", cell: (row) => <StatusBadge raw={row.severity} /> },
      { key: "issue", header: "issue", width: "25%", cell: (row) => <code>{row.issue_code}</code> },
      { key: "component", header: "target", width: "15%", cell: (row) => <code>{row.target_component}</code> },
      { key: "action", header: "operator_action", width: "22%", cell: (row) => <code>{row.operator_action}</code> },
      { key: "hint", header: "repair_hint", cell: (row) => <span>{row.repair_hint}</span> },
    ],
    [],
  );

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR REMEDIATION</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">SEMANTIC · VALIDATOR REMEDIATION</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/remediation · deterministic repair queue for lineage continuity blockers</p>
      {remediation.isLoading && <p className="muted">Loading…</p>}
      {remediation.isError && <p className="term-error">{remediation.error.message}</p>}

      {remediation.data && summary && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Remediation inventory" badge={<StatusBadge raw={degraded.length ? "DEGRADED" : "OK"} />} onInspect={() => openInspector({ title: "/ui/semantic-validator-handoff/remediation", rawJson: remediation.data })}>
              <TermKV rows={[{ k: "schema", v: remediation.data.schema_version }, { k: "records_total", v: String(summary.remediation_count_total) }, { k: "filtered", v: String(summary.remediation_count_filtered) }, { k: "returned", v: String(summary.remediation_count_returned) }, { k: "lineage_chains", v: String(summary.lineage_chain_count_total) }]} />
            </Pane>
            <Pane title="Repair posture">
              <TermKV rows={[{ k: "action_required", v: String(summary.action_required_count) }, { k: "ready_no_action", v: String(summary.ready_no_action_count) }, { k: "critical", v: String(summary.critical_count) }, { k: "high", v: String(summary.high_count) }, { k: "ingress_blocked", v: String(summary.blocked_validator_ingress_count) }]} />
            </Pane>
            <Pane title="Selected repair" onInspect={selectedRow ? () => openInspector({ title: "Semantic validator handoff remediation", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "status", v: selectedRow?.remediation_status ?? "—" }, { k: "severity", v: selectedRow?.severity ?? "—" }, { k: "chain", v: selectedRow?.chain_id ?? "—" }, { k: "digest", v: shortDigest(selectedRow?.chain_digest) }, { k: "steps", v: String(selectedRow?.remediation_step_count ?? "—") }]} />
              {selectedRow?.chain_digest && <button type="button" className="term-button" style={{ marginTop: "6px" }} onClick={() => setLastDigest(selectedRow.chain_digest ?? "")}>Copy chain digest</button>}
            </Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-toolbar">
              <select className="term-input" value={chainStatusMode} onChange={(e) => setChainStatusMode(e.target.value as ChainStatusMode)} aria-label="chain status filter" style={{ width: "150px" }}>{CHAIN_STATUS_MODES.map((m) => <option key={m} value={m}>chain:{m}</option>)}</select>
              <select className="term-input" value={remediationStatusMode} onChange={(e) => setRemediationStatusMode(e.target.value as RemediationStatusMode)} aria-label="remediation status filter" style={{ width: "255px" }}>{REMEDIATION_STATUS_MODES.map((m) => <option key={m} value={m}>repair:{m}</option>)}</select>
              <select className="term-input" value={severityMode} onChange={(e) => setSeverityMode(e.target.value as SeverityMode)} aria-label="severity filter" style={{ width: "150px" }}>{SEVERITY_MODES.map((m) => <option key={m} value={m}>sev:{m}</option>)}</select>
              <select className="term-input" value={operatorActionMode} onChange={(e) => setOperatorActionMode(e.target.value as BoolMode)} aria-label="operator action filter" style={{ width: "165px" }}>{BOOL_MODES.map((m) => <option key={m} value={m}>action:{m}</option>)}</select>
              <label className="term-field"><span>experiment</span><input className="term-input" value={experimentNeedle} onChange={(e) => setExperimentNeedle(e.target.value)} placeholder="contains" style={{ width: "200px" }} /></label>
              <label className="term-field"><span>issue</span><input className="term-input" value={issueNeedle} onChange={(e) => setIssueNeedle(e.target.value)} placeholder="checksum/missing" style={{ width: "210px" }} /></label>
            </div>
          </Pane>

          <Pane title="Remediation queue" badge={<StatusBadge raw={summary.action_required_count > 0 ? "ACTION_REQUIRED" : "READY"} />}>
            <DenseTable columns={columns} rows={rows} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => setSelected(row.__id)} empty="No remediation records matched the current filters." />
          </Pane>

          <PaneGrid cols={3}>
            <Pane title="Remediation statuses"><TermKV rows={countRows(remediation.data.remediation_status_counts)} /></Pane>
            <Pane title="Severity"><TermKV rows={countRows(remediation.data.severity_counts)} /></Pane>
            <Pane title="Selected missing components"><ul className="term-list">{(selectedRow?.missing_component_labels ?? []).slice(0, 10).map((line) => <li key={line}>{line}</li>)}{(selectedRow?.missing_component_labels ?? []).length === 0 && <li>—</li>}</ul></Pane>
          </PaneGrid>

          <Pane title="Selected repair steps" badge={<StatusBadge raw={selectedRow?.operator_action_required ? "BLOCKED" : "READY"} />} onInspect={selectedRow ? () => openInspector({ title: "Semantic validator handoff remediation steps", rawJson: { remediation_id: selectedRow.remediation_id, remediation_steps: selectedRow.remediation_steps, issue_codes: selectedRow.issue_codes } }) : undefined}>
            <DenseTable columns={stepColumns} rows={stepRows(selectedRow)} rowKey={(row) => row.step_id} empty="Selected chain is ready; no repair steps required." />
          </Pane>

          {degraded.length > 0 && <Pane title="Degraded signals" badge={<StatusBadge raw="DEGRADED" />} onInspect={() => openInspector({ title: "Semantic validator remediation degraded", rawJson: { degraded, source_degraded: remediation.data?.source_degraded } })}><ul className="term-list">{degraded.map((line) => <li key={line}>{line}</li>)}</ul></Pane>}
          <Pane title="Guardrails"><ul className="term-list">{guardrails.map((line) => <li key={line}>{line}</li>)}</ul></Pane>
          <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/remediation JSON" data={remediation.data} />
        </>
      )}
    </div>
  );
}
