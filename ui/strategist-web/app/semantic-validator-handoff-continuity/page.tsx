"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiSemanticValidatorHandoffContinuity, type UiSemanticValidatorHandoffContinuityQuery } from "@/hooks/useUiSemanticValidatorHandoffContinuity";
import type { UiSemanticValidatorHandoffContinuityRow, UiSemanticValidatorHandoffContinuityStage } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type StageMode = "all" | "decision" | "signoff" | "custody" | "archive" | "closure";
type OpenMode = "all" | "open" | "closed";
type ContinuityRow = UiSemanticValidatorHandoffContinuityRow & { __id: string };

const STAGE_MODES: StageMode[] = ["all", "decision", "signoff", "custody", "archive", "closure"];
const OPEN_MODES: OpenMode[] = ["all", "open", "closed"];

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

function openParam(mode: OpenMode): boolean | null {
  if (mode === "open") return true;
  if (mode === "closed") return false;
  return null;
}

export default function SemanticValidatorHandoffContinuityPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [stageMode, setStageMode] = useState<StageMode>("all");
  const [openMode, setOpenMode] = useState<OpenMode>("all");
  const [experimentNeedle, setExperimentNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiSemanticValidatorHandoffContinuityQuery = useMemo(
    () => ({
      currentStage: stageMode === "all" ? null : stageMode,
      openAction: openParam(openMode),
      experimentIdContains: experimentNeedle.trim() || null,
      issueContains: issueNeedle.trim() || null,
      limit: 300,
    }),
    [experimentNeedle, issueNeedle, openMode, stageMode],
  );

  const continuity = useUiSemanticValidatorHandoffContinuity(query);
  const summary = continuity.data?.summary ?? {};
  const rows = useMemo<ContinuityRow[]>(
    () => (continuity.data?.continuity_rows ?? []).map((row, i) => ({ ...row, __id: `${row.continuity_id}:${i}` })),
    [continuity.data?.continuity_rows],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(continuity.data?.degraded);
  const sourceDegraded = asStringArray(continuity.data?.source_degraded);
  const guardrails = asStringArray(continuity.data?.guardrails);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "semantic-validator-handoff-continuity-counts",
        severity: Number(summary.open_action_count ?? 0) > 0 ? "warn" : "ok",
        text: `continuity=${summary.continuity_count_returned ?? 0}/${summary.continuity_count_total ?? 0} open=${summary.open_action_count ?? 0} external=${summary.external_artifact_required_count ?? 0}`,
      },
      {
        id: "semantic-validator-handoff-continuity-boundary",
        severity: "info",
        text: "continuity read-plane only · chain visibility only · no write/submit/adjudicate/promote/execute authority",
      },
    ],
    [summary],
  );
  const ticker = useMemo(
    () => [
      { severity: Number(summary.open_action_count ?? 0) > 0 ? ("warn" as const) : ("ok" as const), text: `OPEN ${summary.open_action_count ?? 0}` },
      { severity: Number(summary.closed_chain_count ?? 0) > 0 ? ("ok" as const) : ("neutral" as const), text: `CLOSED ${summary.closed_chain_count ?? 0}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<ContinuityRow>[] = useMemo(
    () => [
      { key: "sev", header: "sev", width: "7%", cell: (row) => <StatusBadge raw={row.severity} /> },
      { key: "experiment", header: "experiment", width: "14%", cell: (row) => <code>{text(row.experiment_id)}</code> },
      { key: "terminal", header: "terminal", width: "28%", cell: (row) => <StatusBadge raw={row.terminal_status} /> },
      { key: "stage", header: "stage", width: "10%", cell: (row) => <code>{row.current_stage}</code> },
      { key: "ready", header: "ready", width: "8%", cell: (row) => <code>{row.ready_stage_count}/{row.stage_count_expected}</code> },
      { key: "external", header: "external", width: "10%", cell: (row) => <StatusBadge raw={row.external_artifact_required ? "REQUIRED" : "NO"} /> },
      { key: "closure", header: "closure", cell: (row) => <StatusBadge raw={text(row.closure_status)} /> },
    ],
    [],
  );

  const stageColumns: DenseColumn<UiSemanticValidatorHandoffContinuityStage>[] = useMemo(
    () => [
      { key: "stage", header: "stage", width: "16%", cell: (row) => <code>{row.stage}</code> },
      { key: "status", header: "status", width: "30%", cell: (row) => <StatusBadge raw={text(row.status)} /> },
      { key: "record", header: "record", width: "24%", cell: (row) => <code>{text(row.record_id)}</code> },
      { key: "ready", header: "ready", cell: (row) => <StatusBadge raw={row.ready ? "READY" : "ATTENTION"} /> },
    ],
    [],
  );

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CONTINUITY</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CONTINUITY</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/continuity · read-only chain timeline from decision through closure</p>
      {continuity.isLoading && <p className="muted">Loading…</p>}
      {continuity.isError && <p className="term-error">{continuity.error.message}</p>}

      {continuity.data && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Continuity inventory" badge={<StatusBadge raw={degraded.length ? "DEGRADED" : "OK"} />} onInspect={() => openInspector({ title: "/ui/semantic-validator-handoff/continuity", rawJson: continuity.data })}>
              <TermKV rows={[{ k: "schema", v: continuity.data.schema_version }, { k: "total", v: String(summary.continuity_count_total ?? 0) }, { k: "returned", v: String(summary.continuity_count_returned ?? 0) }, { k: "open", v: String(summary.open_action_count ?? 0) }, { k: "closed", v: String(summary.closed_chain_count ?? 0) }]} />
            </Pane>
            <Pane title="Authority posture">
              <TermKV rows={[{ k: "read_plane_only", v: String(continuity.data.read_plane_only) }, { k: "mutation", v: continuity.data.mutation_authority }, { k: "submission", v: continuity.data.validator_submission_authority }, { k: "promotion", v: continuity.data.promotion_authority }, { k: "execution", v: continuity.data.execution_authority }]} />
            </Pane>
            <Pane title="Selected chain" onInspect={selectedRow ? () => openInspector({ title: "Selected semantic-validator handoff continuity", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "experiment", v: text(selectedRow?.experiment_id) }, { k: "terminal", v: text(selectedRow?.terminal_status) }, { k: "stage", v: text(selectedRow?.current_stage) }, { k: "digest", v: shortDigest(selectedRow?.closure_packet_digest) }, { k: "action", v: text(selectedRow?.recommended_action) }]} />
            </Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-filter-row">
              <label>Stage <select value={stageMode} onChange={(e) => setStageMode(e.target.value as StageMode)}>{STAGE_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Open <select value={openMode} onChange={(e) => setOpenMode(e.target.value as OpenMode)}>{OPEN_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Experiment <input value={experimentNeedle} onChange={(e) => setExperimentNeedle(e.target.value)} placeholder="contains…" /></label>
              <label>Issue <input value={issueNeedle} onChange={(e) => setIssueNeedle(e.target.value)} placeholder="digest, missing…" /></label>
            </div>
          </Pane>

          <Pane title="Continuity rows" badge={<StatusBadge raw={`${rows.length} rows`} />}>
            <DenseTable columns={columns} rows={rows} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => { setSelected(row.__id); setLastDigest(row.closure_packet_digest ?? null); }} empty="No continuity rows matched the current filters." />
          </Pane>

          <Pane title="Selected stage path">
            <DenseTable columns={stageColumns} rows={selectedRow?.stage_path ?? []} rowKey={(row) => row.stage} empty="No stage path is available for the selected continuity row." />
          </Pane>

          <PaneGrid cols={4}>
            <Pane title="Terminal"><TermKV rows={countRows(continuity.data.terminal_status_counts)} /></Pane>
            <Pane title="Stage"><TermKV rows={countRows(continuity.data.current_stage_counts)} /></Pane>
            <Pane title="Closure"><TermKV rows={countRows(continuity.data.closure_status_counts)} /></Pane>
            <Pane title="Severity"><TermKV rows={countRows(continuity.data.severity_counts)} /></Pane>
          </PaneGrid>

          <PaneGrid cols={3}>
            <Pane title="Guardrails"><ul className="term-list">{guardrails.map((item) => <li key={item}><code>{item}</code></li>)}</ul></Pane>
            <Pane title="Degraded"><ul className="term-list">{degraded.length ? degraded.map((item) => <li key={item}><code>{item}</code></li>) : <li>—</li>}</ul></Pane>
            <Pane title="Source degraded"><ul className="term-list">{sourceDegraded.length ? sourceDegraded.map((item) => <li key={item}><code>{item}</code></li>) : <li>—</li>}</ul></Pane>
          </PaneGrid>

          <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/continuity JSON" data={continuity.data} />
        </>
      )}
    </div>
  );
}
