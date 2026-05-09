"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiSemanticValidatorHandoffExceptions, type UiSemanticValidatorHandoffExceptionsQuery } from "@/hooks/useUiSemanticValidatorHandoffExceptions";
import type { UiSemanticValidatorHandoffExceptionRow } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type StateMode = "all" | "BLOCKED" | "AWAITING_EXTERNAL_ARTIFACT" | "OPEN_REVIEW" | "RESOLVED_AUDIT_RETENTION";
type PriorityMode = "all" | "P0" | "P1" | "P2" | "P3" | "P4";
type ResolvedMode = "open" | "include";
type ExceptionRow = UiSemanticValidatorHandoffExceptionRow & { __id: string };

const STATE_MODES: StateMode[] = ["all", "BLOCKED", "AWAITING_EXTERNAL_ARTIFACT", "OPEN_REVIEW", "RESOLVED_AUDIT_RETENTION"];
const PRIORITY_MODES: PriorityMode[] = ["all", "P0", "P1", "P2", "P3", "P4"];

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

export default function SemanticValidatorHandoffExceptionsPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [stateMode, setStateMode] = useState<StateMode>("all");
  const [priorityMode, setPriorityMode] = useState<PriorityMode>("all");
  const [resolvedMode, setResolvedMode] = useState<ResolvedMode>("open");
  const [experimentNeedle, setExperimentNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiSemanticValidatorHandoffExceptionsQuery = useMemo(
    () => ({
      exceptionState: stateMode === "all" ? null : stateMode,
      priority: priorityMode === "all" ? null : priorityMode,
      includeResolved: resolvedMode === "include",
      experimentIdContains: experimentNeedle.trim() || null,
      issueContains: issueNeedle.trim() || null,
      limit: 300,
    }),
    [experimentNeedle, issueNeedle, priorityMode, resolvedMode, stateMode],
  );

  const exceptions = useUiSemanticValidatorHandoffExceptions(query);
  const summary = exceptions.data?.summary ?? {};
  const rows = useMemo<ExceptionRow[]>(
    () => (exceptions.data?.exception_rows ?? []).map((row, i) => ({ ...row, __id: `${row.exception_id}:${i}` })),
    [exceptions.data?.exception_rows],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(exceptions.data?.degraded);
  const sourceDegraded = asStringArray(exceptions.data?.source_degraded);
  const guardrails = asStringArray(exceptions.data?.guardrails);
  const checklist = asStringArray(selectedRow?.checklist);
  const templateFields = asStringArray(selectedRow?.required_template_fields);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "semantic-validator-handoff-exceptions-counts",
        severity: Number(summary.blocked_exception_count ?? 0) > 0 ? "bad" : Number(summary.open_exception_count ?? 0) > 0 ? "warn" : "ok",
        text: `exceptions=${summary.exception_count_returned ?? 0}/${summary.exception_count_total ?? 0} open=${summary.open_exception_count ?? 0} blocked=${summary.blocked_exception_count ?? 0}`,
      },
      {
        id: "semantic-validator-handoff-exceptions-boundary",
        severity: "info",
        text: "exception queue read-plane only · no write/submit/adjudicate/promote/execute authority",
      },
    ],
    [summary],
  );
  const ticker = useMemo(
    () => [
      { severity: Number(summary.p0_exception_count ?? 0) > 0 ? ("bad" as const) : ("neutral" as const), text: `P0 ${summary.p0_exception_count ?? 0}` },
      { severity: Number(summary.external_artifact_required_count ?? 0) > 0 ? ("warn" as const) : ("ok" as const), text: `EXT ${summary.external_artifact_required_count ?? 0}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<ExceptionRow>[] = useMemo(
    () => [
      { key: "state", header: "state", width: "16%", cell: (row) => <StatusBadge raw={row.exception_state} /> },
      { key: "priority", header: "prio", width: "7%", cell: (row) => <StatusBadge raw={text(row.priority)} /> },
      { key: "severity", header: "sev", width: "8%", cell: (row) => <StatusBadge raw={text(row.severity)} /> },
      { key: "experiment", header: "experiment", width: "13%", cell: (row) => <code>{text(row.experiment_id)}</code> },
      { key: "kind", header: "kind", width: "25%", cell: (row) => <code>{row.exception_kind}</code> },
      { key: "lane", header: "lane", width: "15%", cell: (row) => <code>{row.escalation_lane}</code> },
      { key: "issue", header: "first issue", cell: (row) => <code>{text(row.first_issue_code)}</code> },
    ],
    [],
  );

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF EXCEPTIONS</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF EXCEPTIONS</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/exceptions · unresolved exception queue derived from runbook cards</p>
      {exceptions.isLoading && <p className="muted">Loading…</p>}
      {exceptions.isError && <p className="term-error">{exceptions.error.message}</p>}

      {exceptions.data && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Exception inventory" badge={<StatusBadge raw={degraded.length ? "DEGRADED" : "OK"} />} onInspect={() => openInspector({ title: "/ui/semantic-validator-handoff/exceptions", rawJson: exceptions.data })}>
              <TermKV rows={[{ k: "schema", v: exceptions.data.schema_version }, { k: "total", v: String(summary.exception_count_total ?? 0) }, { k: "returned", v: String(summary.exception_count_returned ?? 0) }, { k: "open", v: String(summary.open_exception_count ?? 0) }, { k: "blocked", v: String(summary.blocked_exception_count ?? 0) }]} />
            </Pane>
            <Pane title="Authority posture">
              <TermKV rows={[{ k: "read_plane_only", v: String(exceptions.data.read_plane_only) }, { k: "mutation", v: exceptions.data.mutation_authority }, { k: "external_write", v: exceptions.data.external_artifact_write_authority }, { k: "submission", v: exceptions.data.validator_submission_authority }, { k: "execution", v: exceptions.data.execution_authority }]} />
            </Pane>
            <Pane title="Selected exception" onInspect={selectedRow ? () => openInspector({ title: "Selected semantic-validator handoff exception", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "experiment", v: text(selectedRow?.experiment_id) }, { k: "state", v: text(selectedRow?.exception_state) }, { k: "kind", v: text(selectedRow?.exception_kind) }, { k: "digest", v: shortDigest(selectedRow?.closure_packet_digest) }, { k: "route", v: text(selectedRow?.next_route) }]} />
            </Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-filter-row">
              <label>State <select value={stateMode} onChange={(e) => setStateMode(e.target.value as StateMode)}>{STATE_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Priority <select value={priorityMode} onChange={(e) => setPriorityMode(e.target.value as PriorityMode)}>{PRIORITY_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Resolved <select value={resolvedMode} onChange={(e) => setResolvedMode(e.target.value as ResolvedMode)}><option value="open">exclude</option><option value="include">include</option></select></label>
              <label>Experiment <input value={experimentNeedle} onChange={(e) => setExperimentNeedle(e.target.value)} placeholder="contains…" /></label>
              <label>Issue <input value={issueNeedle} onChange={(e) => setIssueNeedle(e.target.value)} placeholder="digest, missing…" /></label>
            </div>
          </Pane>

          <Pane title="Exception queue" badge={<StatusBadge raw={`${rows.length} rows`} />}>
            <DenseTable columns={columns} rows={rows} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => { setSelected(row.__id); setLastDigest(row.closure_packet_digest ?? null); }} empty="No exception rows matched the current filters." />
          </Pane>

          <PaneGrid cols={2}>
            <Pane title="Selected checklist"><ol className="term-list">{checklist.length ? checklist.map((item) => <li key={item}>{item}</li>) : <li>—</li>}</ol></Pane>
            <Pane title="Required external fields"><ul className="term-list">{templateFields.length ? templateFields.map((item) => <li key={item}><code>{item}</code></li>) : <li>—</li>}</ul></Pane>
          </PaneGrid>

          <PaneGrid cols={5}>
            <Pane title="State"><TermKV rows={countRows(exceptions.data.exception_state_counts)} /></Pane>
            <Pane title="Kind"><TermKV rows={countRows(exceptions.data.exception_kind_counts)} /></Pane>
            <Pane title="Priority"><TermKV rows={countRows(exceptions.data.priority_counts)} /></Pane>
            <Pane title="Severity"><TermKV rows={countRows(exceptions.data.severity_counts)} /></Pane>
            <Pane title="Lane"><TermKV rows={countRows(exceptions.data.escalation_lane_counts)} /></Pane>
          </PaneGrid>

          <PaneGrid cols={3}>
            <Pane title="Guardrails"><ul className="term-list">{guardrails.map((item) => <li key={item}><code>{item}</code></li>)}</ul></Pane>
            <Pane title="Degraded"><ul className="term-list">{degraded.length ? degraded.map((item) => <li key={item}><code>{item}</code></li>) : <li>—</li>}</ul></Pane>
            <Pane title="Source degraded"><ul className="term-list">{sourceDegraded.length ? sourceDegraded.map((item) => <li key={item}><code>{item}</code></li>) : <li>—</li>}</ul></Pane>
          </PaneGrid>

          <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/exceptions JSON" data={exceptions.data} />
        </>
      )}
    </div>
  );
}
