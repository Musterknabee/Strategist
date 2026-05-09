"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiSemanticValidatorHandoffRunbook, type UiSemanticValidatorHandoffRunbookQuery } from "@/hooks/useUiSemanticValidatorHandoffRunbook";
import type { UiSemanticValidatorHandoffRunbookCard } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type PriorityMode = "all" | "P0" | "P1" | "P2" | "P3" | "P4";
type ActionMode = "all" | "CREATE_EXTERNAL_CLOSURE_ATTESTATION" | "REPAIR_CLOSURE_ATTESTATION" | "VERIFY_ARCHIVE_MANIFEST" | "RESTORE_MISSING_STAGE_EVIDENCE" | "RETAIN_AUDIT_TRAIL";
type CompletionMode = "all" | "open" | "completed";
type RunbookCard = UiSemanticValidatorHandoffRunbookCard & { __id: string };

const PRIORITY_MODES: PriorityMode[] = ["all", "P0", "P1", "P2", "P3", "P4"];
const ACTION_MODES: ActionMode[] = ["all", "CREATE_EXTERNAL_CLOSURE_ATTESTATION", "REPAIR_CLOSURE_ATTESTATION", "VERIFY_ARCHIVE_MANIFEST", "RESTORE_MISSING_STAGE_EVIDENCE", "RETAIN_AUDIT_TRAIL"];
const COMPLETION_MODES: CompletionMode[] = ["all", "open", "completed"];

function text(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

function shortDigest(value: unknown): string {
  const t = text(value);
  return t === "—" ? t : `${t.slice(0, 12)}…`;
}

function completionParam(mode: CompletionMode): boolean | null {
  if (mode === "completed") return true;
  if (mode === "open") return false;
  return null;
}

function countRows(counts: Record<string, number> | undefined) {
  return Object.entries(counts ?? {}).map(([k, v]) => ({ k, v: String(v) }));
}

export default function SemanticValidatorHandoffRunbookPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [priorityMode, setPriorityMode] = useState<PriorityMode>("all");
  const [actionMode, setActionMode] = useState<ActionMode>("all");
  const [completionMode, setCompletionMode] = useState<CompletionMode>("all");
  const [experimentNeedle, setExperimentNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiSemanticValidatorHandoffRunbookQuery = useMemo(
    () => ({
      priority: priorityMode === "all" ? null : priorityMode,
      actionKind: actionMode === "all" ? null : actionMode,
      completed: completionParam(completionMode),
      experimentIdContains: experimentNeedle.trim() || null,
      issueContains: issueNeedle.trim() || null,
      limit: 300,
    }),
    [actionMode, completionMode, experimentNeedle, issueNeedle, priorityMode],
  );

  const runbook = useUiSemanticValidatorHandoffRunbook(query);
  const summary = runbook.data?.summary ?? {};
  const rows = useMemo<RunbookCard[]>(
    () => (runbook.data?.runbook_cards ?? []).map((row, i) => ({ ...row, __id: `${row.runbook_card_id}:${i}` })),
    [runbook.data?.runbook_cards],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(runbook.data?.degraded);
  const sourceDegraded = asStringArray(runbook.data?.source_degraded);
  const guardrails = asStringArray(runbook.data?.guardrails);
  const checklist = asStringArray(selectedRow?.checklist);
  const templateFields = asStringArray(selectedRow?.required_template_fields);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "semantic-validator-handoff-runbook-counts",
        severity: Number(summary.blocked_runbook_card_count ?? 0) > 0 ? "bad" : Number(summary.open_runbook_card_count ?? 0) > 0 ? "warn" : "ok",
        text: `runbook=${summary.runbook_card_count_returned ?? 0}/${summary.runbook_card_count_total ?? 0} open=${summary.open_runbook_card_count ?? 0} blocked=${summary.blocked_runbook_card_count ?? 0}`,
      },
      {
        id: "semantic-validator-handoff-runbook-boundary",
        severity: "info",
        text: "runbook read-plane only · guidance only · no write/submit/adjudicate/promote/execute authority",
      },
    ],
    [summary],
  );
  const ticker = useMemo(
    () => [
      { severity: Number(summary.blocked_runbook_card_count ?? 0) > 0 ? ("bad" as const) : ("neutral" as const), text: `P0 ${summary.blocked_runbook_card_count ?? 0}` },
      { severity: Number(summary.external_artifact_required_count ?? 0) > 0 ? ("warn" as const) : ("ok" as const), text: `EXT ${summary.external_artifact_required_count ?? 0}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<RunbookCard>[] = useMemo(
    () => [
      { key: "priority", header: "prio", width: "7%", cell: (row) => <StatusBadge raw={row.priority} /> },
      { key: "severity", header: "sev", width: "8%", cell: (row) => <StatusBadge raw={row.severity} /> },
      { key: "experiment", header: "experiment", width: "13%", cell: (row) => <code>{text(row.experiment_id)}</code> },
      { key: "action", header: "action", width: "27%", cell: (row) => <code>{row.action_kind}</code> },
      { key: "terminal", header: "terminal", width: "23%", cell: (row) => <StatusBadge raw={text(row.terminal_status)} /> },
      { key: "external", header: "external", width: "9%", cell: (row) => <StatusBadge raw={row.external_artifact_required ? "REQUIRED" : "NO"} /> },
      { key: "issue", header: "first issue", cell: (row) => <code>{text(row.first_issue_code)}</code> },
    ],
    [],
  );

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF RUNBOOK</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF RUNBOOK</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/runbook · deterministic next-action cards derived from continuity rows</p>
      {runbook.isLoading && <p className="muted">Loading…</p>}
      {runbook.isError && <p className="term-error">{runbook.error.message}</p>}

      {runbook.data && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Runbook inventory" badge={<StatusBadge raw={degraded.length ? "DEGRADED" : "OK"} />} onInspect={() => openInspector({ title: "/ui/semantic-validator-handoff/runbook", rawJson: runbook.data })}>
              <TermKV rows={[{ k: "schema", v: runbook.data.schema_version }, { k: "total", v: String(summary.runbook_card_count_total ?? 0) }, { k: "returned", v: String(summary.runbook_card_count_returned ?? 0) }, { k: "open", v: String(summary.open_runbook_card_count ?? 0) }, { k: "blocked", v: String(summary.blocked_runbook_card_count ?? 0) }]} />
            </Pane>
            <Pane title="Authority posture">
              <TermKV rows={[{ k: "read_plane_only", v: String(runbook.data.read_plane_only) }, { k: "mutation", v: runbook.data.mutation_authority }, { k: "external_write", v: runbook.data.external_artifact_write_authority }, { k: "submission", v: runbook.data.validator_submission_authority }, { k: "execution", v: runbook.data.execution_authority }]} />
            </Pane>
            <Pane title="Selected card" onInspect={selectedRow ? () => openInspector({ title: "Selected semantic-validator handoff runbook card", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "experiment", v: text(selectedRow?.experiment_id) }, { k: "priority", v: text(selectedRow?.priority) }, { k: "action", v: text(selectedRow?.action_kind) }, { k: "digest", v: shortDigest(selectedRow?.closure_packet_digest) }, { k: "route", v: text(selectedRow?.next_route) }]} />
            </Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-filter-row">
              <label>Priority <select value={priorityMode} onChange={(e) => setPriorityMode(e.target.value as PriorityMode)}>{PRIORITY_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Action <select value={actionMode} onChange={(e) => setActionMode(e.target.value as ActionMode)}>{ACTION_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>State <select value={completionMode} onChange={(e) => setCompletionMode(e.target.value as CompletionMode)}>{COMPLETION_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Experiment <input value={experimentNeedle} onChange={(e) => setExperimentNeedle(e.target.value)} placeholder="contains…" /></label>
              <label>Issue <input value={issueNeedle} onChange={(e) => setIssueNeedle(e.target.value)} placeholder="digest, missing…" /></label>
            </div>
          </Pane>

          <Pane title="Runbook cards" badge={<StatusBadge raw={`${rows.length} cards`} />}>
            <DenseTable columns={columns} rows={rows} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => { setSelected(row.__id); setLastDigest(row.closure_packet_digest ?? null); }} empty="No runbook cards matched the current filters." />
          </Pane>

          <PaneGrid cols={2}>
            <Pane title="Selected checklist">
              <ol className="term-list">{checklist.length ? checklist.map((item) => <li key={item}>{item}</li>) : <li>—</li>}</ol>
            </Pane>
            <Pane title="External template fields">
              <ul className="term-list">{templateFields.length ? templateFields.map((item) => <li key={item}><code>{item}</code></li>) : <li>—</li>}</ul>
            </Pane>
          </PaneGrid>

          <PaneGrid cols={4}>
            <Pane title="Action"><TermKV rows={countRows(runbook.data.action_kind_counts)} /></Pane>
            <Pane title="Priority"><TermKV rows={countRows(runbook.data.priority_counts)} /></Pane>
            <Pane title="Severity"><TermKV rows={countRows(runbook.data.severity_counts)} /></Pane>
            <Pane title="Terminal"><TermKV rows={countRows(runbook.data.terminal_status_counts)} /></Pane>
          </PaneGrid>

          <PaneGrid cols={3}>
            <Pane title="Guardrails"><ul className="term-list">{guardrails.map((item) => <li key={item}><code>{item}</code></li>)}</ul></Pane>
            <Pane title="Degraded"><ul className="term-list">{degraded.length ? degraded.map((item) => <li key={item}><code>{item}</code></li>) : <li>—</li>}</ul></Pane>
            <Pane title="Source degraded"><ul className="term-list">{sourceDegraded.length ? sourceDegraded.map((item) => <li key={item}><code>{item}</code></li>) : <li>—</li>}</ul></Pane>
          </PaneGrid>

          <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/runbook JSON" data={runbook.data} />
        </>
      )}
    </div>
  );
}
