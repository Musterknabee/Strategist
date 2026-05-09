"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiSemanticValidatorHandoffLineage, type UiSemanticValidatorHandoffLineageQuery } from "@/hooks/useUiSemanticValidatorHandoffLineage";
import type { UiSemanticValidatorHandoffLineageChain } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type ChainStatusMode = "all" | "READY" | "BROKEN" | "INCOMPLETE";
type BoolMode = "all" | "yes" | "no";
type ChainRow = UiSemanticValidatorHandoffLineageChain & { __id: string };

const STATUS_MODES: ChainStatusMode[] = ["all", "READY", "BROKEN", "INCOMPLETE"];
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

function componentRows(chain: ChainRow | null) {
  const components = chain?.components ?? {};
  return [
    { k: "decision_ledger", v: text(components.decision_ledger?.artifact_id ?? chain?.decision_ledger_id) },
    { k: "handoff_certificate", v: text(components.handoff_certificate?.artifact_id ?? chain?.handoff_certificate_id) },
    { k: "validator_packet", v: text(components.validator_packet?.artifact_id ?? chain?.validator_packet_id) },
    { k: "ingress_certificate", v: text(components.ingress_certificate?.artifact_id ?? chain?.ingress_certificate_id) },
  ];
}

export default function SemanticValidatorHandoffLineagePage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [statusMode, setStatusMode] = useState<ChainStatusMode>("all");
  const [reviewMode, setReviewMode] = useState<BoolMode>("all");
  const [brokenLinkMode, setBrokenLinkMode] = useState<BoolMode>("all");
  const [experimentNeedle, setExperimentNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiSemanticValidatorHandoffLineageQuery = useMemo(
    () => ({
      chainStatus: statusMode === "all" ? null : statusMode,
      readyForOperatorReview: boolParam(reviewMode),
      requireBrokenLinks: boolParam(brokenLinkMode),
      experimentIdContains: experimentNeedle.trim() || null,
      issueContains: issueNeedle.trim() || null,
      limit: 300,
    }),
    [brokenLinkMode, experimentNeedle, issueNeedle, reviewMode, statusMode],
  );

  const lineage = useUiSemanticValidatorHandoffLineage(query);
  const summary = lineage.data?.summary;
  const rows = useMemo<ChainRow[]>(
    () => (lineage.data?.chains ?? []).map((chain, i) => ({ ...chain, __id: `${chain.chain_id}:${i}` })),
    [lineage.data?.chains],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(lineage.data?.degraded);
  const guardrails = asStringArray(lineage.data?.guardrails);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "semantic-validator-handoff-lineage-counts",
        severity: (summary?.broken_chain_count ?? 0) > 0 || (summary?.incomplete_chain_count ?? 0) > 0 ? "warn" : "ok",
        text: `lineage chains=${summary?.chain_count_returned ?? 0}/${summary?.chain_count_total ?? 0} ready=${summary?.ready_chain_count ?? 0} broken=${summary?.broken_chain_count ?? 0} incomplete=${summary?.incomplete_chain_count ?? 0}`,
      },
      {
        id: "semantic-validator-handoff-lineage-boundary",
        severity: "info",
        text: "read-plane only · validates ids/checksums; does not submit to validator or mutate evidence",
      },
    ],
    [summary],
  );
  const ticker = useMemo(
    () => [
      { severity: (summary?.ready_chain_count ?? 0) > 0 ? ("ok" as const) : ("neutral" as const), text: `LIN ${summary?.chain_count_returned ?? 0}` },
      { severity: (summary?.broken_chain_count ?? 0) > 0 ? ("warn" as const) : ("neutral" as const), text: `BRK ${summary?.broken_chain_count ?? 0}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<ChainRow>[] = useMemo(
    () => [
      { key: "status", header: "status", width: "11%", cell: (row) => <StatusBadge raw={row.status} /> },
      { key: "experiment", header: "experiment", width: "19%", cell: (row) => <code>{row.experiment_id}</code> },
      { key: "components", header: "components", width: "10%", cell: (row) => <code>{row.component_count_present}/{row.component_count_expected}</code> },
      { key: "link", header: "link", width: "10%", cell: (row) => <StatusBadge raw={row.link_integrity_ok ? "OK" : "BROKEN"} /> },
      { key: "review", header: "review", width: "10%", cell: (row) => <StatusBadge raw={row.ready_for_operator_review ? "READY" : "BLOCKED"} /> },
      { key: "issues", header: "issues", width: "8%", cell: (row) => <code>{row.issue_count}</code> },
      { key: "digest", header: "chain_digest", width: "16%", cell: (row) => <code>{shortDigest(row.chain_digest)}</code> },
      { key: "action", header: "recommended", cell: (row) => <code>{row.recommended_action}</code> },
    ],
    [],
  );

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR LINEAGE</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">SEMANTIC · VALIDATOR LINEAGE</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/lineage · id/checksum continuity across ledger → certificate → packet → ingress certificate</p>
      {lineage.isLoading && <p className="muted">Loading…</p>}
      {lineage.isError && <p className="term-error">{lineage.error.message}</p>}

      {lineage.data && summary && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Lineage inventory" badge={<StatusBadge raw={degraded.length ? "DEGRADED" : "OK"} />} onInspect={() => openInspector({ title: "/ui/semantic-validator-handoff/lineage", rawJson: lineage.data })}>
              <TermKV rows={[{ k: "schema", v: lineage.data.schema_version }, { k: "chains_total", v: String(summary.chain_count_total) }, { k: "filtered", v: String(summary.chain_count_filtered) }, { k: "returned", v: String(summary.chain_count_returned) }, { k: "source_artifacts", v: String(summary.source_artifact_count_total) }]} />
            </Pane>
            <Pane title="Continuity posture">
              <TermKV rows={[{ k: "ready", v: String(summary.ready_chain_count) }, { k: "broken", v: String(summary.broken_chain_count) }, { k: "incomplete", v: String(summary.incomplete_chain_count) }, { k: "operator_review_ready", v: String(summary.operator_review_ready_count) }, { k: "latest_experiment", v: text(summary.latest_experiment_id) }]} />
            </Pane>
            <Pane title="Selected chain" onInspect={selectedRow ? () => openInspector({ title: "Semantic validator handoff lineage", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "status", v: selectedRow?.status ?? "—" }, { k: "chain", v: selectedRow?.chain_id ?? "—" }, { k: "digest", v: shortDigest(selectedRow?.chain_digest) }, { k: "components", v: selectedRow ? `${selectedRow.component_count_present}/${selectedRow.component_count_expected}` : "—" }, { k: "issues", v: String(selectedRow?.issue_count ?? "—") }]} />
              {selectedRow?.chain_digest && <button type="button" className="term-button" style={{ marginTop: "6px" }} onClick={() => setLastDigest(selectedRow.chain_digest)}>Copy chain digest</button>}
            </Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-toolbar">
              {STATUS_MODES.map((mode) => <button key={mode} type="button" className={statusMode === mode ? "term-chip active" : "term-chip"} onClick={() => setStatusMode(mode)}>{mode}</button>)}
              <select className="term-input" value={reviewMode} onChange={(e) => setReviewMode(e.target.value as BoolMode)} aria-label="operator review filter" style={{ width: "155px" }}>{BOOL_MODES.map((m) => <option key={m} value={m}>review:{m}</option>)}</select>
              <select className="term-input" value={brokenLinkMode} onChange={(e) => setBrokenLinkMode(e.target.value as BoolMode)} aria-label="broken link filter" style={{ width: "155px" }}>{BOOL_MODES.map((m) => <option key={m} value={m}>broken:{m}</option>)}</select>
              <label className="term-field"><span>experiment</span><input className="term-input" value={experimentNeedle} onChange={(e) => setExperimentNeedle(e.target.value)} placeholder="contains" style={{ width: "200px" }} /></label>
              <label className="term-field"><span>issue</span><input className="term-input" value={issueNeedle} onChange={(e) => setIssueNeedle(e.target.value)} placeholder="checksum/missing/link" style={{ width: "210px" }} /></label>
            </div>
          </Pane>

          <Pane title="Semantic validator handoff lineage chains">
            <DenseTable<ChainRow> rows={rows} columns={columns} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => setSelected(row.__id)} empty="No semantic validator handoff lineage chains matched the current filters." />
          </Pane>

          <PaneGrid cols={3}>
            <Pane title="Chain statuses"><TermKV rows={countRows(lineage.data.chain_status_counts)} /></Pane>
            <Pane title="Recommended actions"><TermKV rows={countRows(lineage.data.recommended_action_counts)} /></Pane>
            <Pane title="Selected components"><TermKV rows={componentRows(selectedRow)} /></Pane>
          </PaneGrid>

          {selectedRow && selectedRow.issue_codes.length > 0 && (
            <Pane title="Selected lineage issues" badge={<StatusBadge raw="BLOCKED" />} onInspect={() => openInspector({ title: "Semantic validator lineage issues", rawJson: { issue_codes: selectedRow.issue_codes, warning_codes: selectedRow.warning_codes, link_checks: selectedRow.link_checks } })}>
              <ul className="term-list">{selectedRow.issue_codes.slice(0, 16).map((line) => <li key={line}>{line}</li>)}</ul>
            </Pane>
          )}

          {degraded.length > 0 && <Pane title="Degraded signals" badge={<StatusBadge raw="DEGRADED" />} onInspect={() => openInspector({ title: "Semantic validator lineage degraded", rawJson: { degraded, source_degraded: lineage.data?.source_degraded } })}><ul className="term-list">{degraded.map((line) => <li key={line}>{line}</li>)}</ul></Pane>}
          <Pane title="Guardrails"><ul className="term-list">{guardrails.map((line) => <li key={line}>{line}</li>)}</ul></Pane>
          <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/lineage JSON" data={lineage.data} />
        </>
      )}
    </div>
  );
}
