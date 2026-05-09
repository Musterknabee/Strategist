"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiSemanticValidatorHandoffDecision, type UiSemanticValidatorHandoffDecisionQuery } from "@/hooks/useUiSemanticValidatorHandoffDecision";
import type { UiSemanticValidatorHandoffDecisionOption, UiSemanticValidatorHandoffDecisionPrecondition, UiSemanticValidatorHandoffDecisionRecord } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type DecisionStatusMode = "all" | "READY_FOR_OPERATOR_DECISION_DRAFT" | "BLOCKED_REMEDIATION_REQUIRED" | "BLOCKED_EVIDENCE_REPAIR_REQUIRED" | "BLOCKED_LINEAGE_RECONSTRUCTION_REQUIRED" | "BLOCKED_UNTRUSTED_EVIDENCE";
type TrustMode = "all" | "TRUSTED" | "TRUST_RESTRICTED" | "UNTRUSTED";
type BoolMode = "all" | "yes" | "no";
type DecisionRow = UiSemanticValidatorHandoffDecisionRecord & { __id: string };

const DECISION_STATUS_MODES: DecisionStatusMode[] = ["all", "READY_FOR_OPERATOR_DECISION_DRAFT", "BLOCKED_REMEDIATION_REQUIRED", "BLOCKED_EVIDENCE_REPAIR_REQUIRED", "BLOCKED_LINEAGE_RECONSTRUCTION_REQUIRED", "BLOCKED_UNTRUSTED_EVIDENCE"];
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

function selectedPreconditions(row: DecisionRow | null): UiSemanticValidatorHandoffDecisionPrecondition[] {
  return row?.decision_preconditions ?? [];
}

function selectedOptions(row: DecisionRow | null): UiSemanticValidatorHandoffDecisionOption[] {
  return row?.decision_options ?? [];
}

function packetDigest(row: DecisionRow | null): string {
  const packet = row?.decision_packet;
  const value = packet && typeof packet === "object" ? (packet as { packet_digest?: unknown }).packet_digest : undefined;
  return typeof value === "string" ? value : "";
}

export default function SemanticValidatorHandoffDecisionPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [decisionStatusMode, setDecisionStatusMode] = useState<DecisionStatusMode>("all");
  const [trustMode, setTrustMode] = useState<TrustMode>("all");
  const [decisionReadyMode, setDecisionReadyMode] = useState<BoolMode>("all");
  const [experimentNeedle, setExperimentNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiSemanticValidatorHandoffDecisionQuery = useMemo(
    () => ({
      decisionStatus: decisionStatusMode === "all" ? null : decisionStatusMode,
      trustBanner: trustMode === "all" ? null : trustMode,
      decisionReady: boolParam(decisionReadyMode),
      experimentIdContains: experimentNeedle.trim() || null,
      issueContains: issueNeedle.trim() || null,
      limit: 300,
    }),
    [decisionReadyMode, decisionStatusMode, experimentNeedle, issueNeedle, trustMode],
  );

  const decision = useUiSemanticValidatorHandoffDecision(query);
  const summary = decision.data?.summary;
  const rows = useMemo<DecisionRow[]>(
    () => (decision.data?.decisions ?? []).map((row, i) => ({ ...row, __id: `${row.decision_id}:${i}` })),
    [decision.data?.decisions],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(decision.data?.degraded);
  const guardrails = asStringArray(decision.data?.guardrails);
  const selectedPacketDigest = packetDigest(selectedRow);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "semantic-validator-handoff-decision-counts",
        severity: (summary?.blocked_decision_count ?? 0) > 0 || (summary?.untrusted_count ?? 0) > 0 ? "warn" : "ok",
        text: `decision dossiers=${summary?.decision_count_returned ?? 0}/${summary?.decision_count_total ?? 0} ready=${summary?.ready_decision_count ?? 0} blocked=${summary?.blocked_decision_count ?? 0} signoff_preparable=${summary?.manual_signoff_preparable_count ?? 0}`,
      },
      {
        id: "semantic-validator-handoff-decision-boundary",
        severity: "info",
        text: "decision dossier only · no signoff write, validator submission, promotion, execution, or artifact mutation authority",
      },
    ],
    [summary],
  );
  const ticker = useMemo(
    () => [
      { severity: (summary?.ready_decision_count ?? 0) > 0 ? ("ok" as const) : ("neutral" as const), text: `DEC ${summary?.decision_count_returned ?? 0}` },
      { severity: (summary?.blocked_decision_count ?? 0) > 0 ? ("warn" as const) : ("neutral" as const), text: `BLK ${summary?.blocked_decision_count ?? 0}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<DecisionRow>[] = useMemo(
    () => [
      { key: "trust", header: "trust", width: "9%", cell: (row) => <StatusBadge raw={row.trust_banner ?? "UNKNOWN"} /> },
      { key: "status", header: "decision", width: "25%", cell: (row) => <StatusBadge raw={row.decision_status} /> },
      { key: "experiment", header: "experiment", width: "17%", cell: (row) => <code>{text(row.experiment_id)}</code> },
      { key: "pre", header: "preconditions", width: "11%", cell: (row) => <code>{row.precondition_pass_count}/{row.precondition_count}</code> },
      { key: "signoff", header: "signoff_draft", width: "11%", cell: (row) => <StatusBadge raw={row.manual_operator_signoff_preparable ? "PREPARABLE" : "BLOCKED"} /> },
      { key: "recorded", header: "recorded", width: "9%", cell: (row) => <StatusBadge raw={row.manual_operator_signoff_recorded ? "YES" : "NO"} /> },
      { key: "submit", header: "submit", width: "8%", cell: (row) => <StatusBadge raw={row.validator_submission_allowed ? "ALLOWED" : "NO"} /> },
      { key: "action", header: "recommended", cell: (row) => <code>{row.recommended_action}</code> },
    ],
    [],
  );

  const preconditionColumns: DenseColumn<UiSemanticValidatorHandoffDecisionPrecondition>[] = useMemo(
    () => [
      { key: "status", header: "status", width: "10%", cell: (row) => <StatusBadge raw={row.status} /> },
      { key: "id", header: "precondition", width: "24%", cell: (row) => <code>{row.precondition_id}</code> },
      { key: "label", header: "label", width: "25%", cell: (row) => <span>{row.label}</span> },
      { key: "detail", header: "detail", cell: (row) => <span>{row.detail}</span> },
    ],
    [],
  );

  const optionColumns: DenseColumn<UiSemanticValidatorHandoffDecisionOption>[] = useMemo(
    () => [
      { key: "availability", header: "availability", width: "12%", cell: (row) => <StatusBadge raw={row.availability} /> },
      { key: "option", header: "option", width: "28%", cell: (row) => <code>{row.option_id}</code> },
      { key: "authority", header: "authority", width: "25%", cell: (row) => <code>{row.mutation_authority}</code> },
      { key: "rationale", header: "rationale", cell: (row) => <span>{row.rationale}</span> },
    ],
    [],
  );

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR DECISION</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">SEMANTIC · VALIDATOR DECISION</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/decision · deterministic read-only decision dossiers over semantic validator review gates</p>
      {decision.isLoading && <p className="muted">Loading…</p>}
      {decision.isError && <p className="term-error">{decision.error.message}</p>}

      {decision.data && summary && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Decision inventory" badge={<StatusBadge raw={degraded.length ? "DEGRADED" : "OK"} />} onInspect={() => openInspector({ title: "/ui/semantic-validator-handoff/decision", rawJson: decision.data })}>
              <TermKV rows={[{ k: "schema", v: decision.data.schema_version }, { k: "decisions_total", v: String(summary.decision_count_total) }, { k: "filtered", v: String(summary.decision_count_filtered) }, { k: "returned", v: String(summary.decision_count_returned) }, { k: "source_reviews", v: String(summary.source_review_count_total) }]} />
            </Pane>
            <Pane title="Decision posture">
              <TermKV rows={[{ k: "ready", v: String(summary.ready_decision_count) }, { k: "blocked", v: String(summary.blocked_decision_count) }, { k: "signoff_preparable", v: String(summary.manual_signoff_preparable_count) }, { k: "signoff_recorded", v: String(summary.manual_signoff_recorded_count) }, { k: "validator_submit_allowed", v: String(summary.validator_submission_allowed_count) }]} />
            </Pane>
            <Pane title="Selected dossier" onInspect={selectedRow ? () => openInspector({ title: "Semantic validator handoff decision dossier", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "status", v: selectedRow?.decision_status ?? "—" }, { k: "trust", v: selectedRow?.trust_banner ?? "—" }, { k: "chain", v: selectedRow?.chain_id ?? "—" }, { k: "chain_digest", v: shortDigest(selectedRow?.chain_digest) }, { k: "packet", v: shortDigest(selectedPacketDigest) }]} />
              {selectedPacketDigest && <button type="button" className="term-button" style={{ marginTop: "6px" }} onClick={() => setLastDigest(selectedPacketDigest)}>Copy packet digest</button>}
            </Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-toolbar">
              <select className="term-input" value={decisionStatusMode} onChange={(e) => setDecisionStatusMode(e.target.value as DecisionStatusMode)} aria-label="decision status filter" style={{ width: "330px" }}>{DECISION_STATUS_MODES.map((m) => <option key={m} value={m}>decision:{m}</option>)}</select>
              <select className="term-input" value={trustMode} onChange={(e) => setTrustMode(e.target.value as TrustMode)} aria-label="trust banner filter" style={{ width: "185px" }}>{TRUST_MODES.map((m) => <option key={m} value={m}>trust:{m}</option>)}</select>
              <select className="term-input" value={decisionReadyMode} onChange={(e) => setDecisionReadyMode(e.target.value as BoolMode)} aria-label="decision ready filter" style={{ width: "170px" }}>{BOOL_MODES.map((m) => <option key={m} value={m}>ready:{m}</option>)}</select>
              <label className="term-field"><span>experiment</span><input className="term-input" value={experimentNeedle} onChange={(e) => setExperimentNeedle(e.target.value)} placeholder="contains" style={{ width: "200px" }} /></label>
              <label className="term-field"><span>issue</span><input className="term-input" value={issueNeedle} onChange={(e) => setIssueNeedle(e.target.value)} placeholder="checksum/missing/untrusted" style={{ width: "240px" }} /></label>
            </div>
          </Pane>

          <Pane title="Semantic validator handoff decision dossiers" badge={<StatusBadge raw={(summary.blocked_decision_count ?? 0) > 0 ? "BLOCKED" : "READY"} />}>
            <DenseTable columns={columns} rows={rows} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => setSelected(row.__id)} empty="No semantic validator handoff decision dossiers matched the current filters." />
          </Pane>

          <PaneGrid cols={3}>
            <Pane title="Decision statuses"><TermKV rows={countRows(decision.data.decision_status_counts)} /></Pane>
            <Pane title="Trust banners"><TermKV rows={countRows(decision.data.trust_banner_counts)} /></Pane>
            <Pane title="Authority gates"><TermKV rows={[{ k: "signoff_write", v: "always false" }, { k: "validator_submission", v: "always false" }, { k: "promotion", v: "always false" }, { k: "execution", v: "always false" }]} /></Pane>
          </PaneGrid>

          <Pane title="Selected decision preconditions" badge={<StatusBadge raw={(selectedRow?.precondition_block_count ?? 0) > 0 ? "BLOCKED" : "PASS"} />} onInspect={selectedRow ? () => openInspector({ title: "Semantic validator handoff decision preconditions", rawJson: { decision_id: selectedRow.decision_id, decision_preconditions: selectedRow.decision_preconditions } }) : undefined}>
            <DenseTable columns={preconditionColumns} rows={selectedPreconditions(selectedRow)} rowKey={(row) => row.precondition_id} empty="No decision preconditions available." />
          </Pane>

          <Pane title="Selected decision options" onInspect={selectedRow ? () => openInspector({ title: "Semantic validator handoff decision options", rawJson: { decision_id: selectedRow.decision_id, decision_options: selectedRow.decision_options } }) : undefined}>
            <DenseTable columns={optionColumns} rows={selectedOptions(selectedRow)} rowKey={(row) => row.option_id} empty="No decision options available." />
          </Pane>

          {selectedRow && selectedRow.decision_blocker_codes.length > 0 && <Pane title="Selected decision blockers" badge={<StatusBadge raw="BLOCKED" />}><ul className="term-list">{selectedRow.decision_blocker_codes.slice(0, 20).map((line) => <li key={line}>{line}</li>)}</ul></Pane>}
          {degraded.length > 0 && <Pane title="Degraded signals" badge={<StatusBadge raw="DEGRADED" />} onInspect={() => openInspector({ title: "Semantic validator decision degraded", rawJson: { degraded, source_degraded: decision.data?.source_degraded } })}><ul className="term-list">{degraded.map((line) => <li key={line}>{line}</li>)}</ul></Pane>}
          <Pane title="Guardrails"><ul className="term-list">{guardrails.map((line) => <li key={line}>{line}</li>)}</ul></Pane>
          <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/decision JSON" data={decision.data} />
        </>
      )}
    </div>
  );
}
