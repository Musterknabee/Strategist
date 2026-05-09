"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiSemanticValidatorHandoffTimeline, type UiSemanticValidatorHandoffTimelineQuery } from "@/hooks/useUiSemanticValidatorHandoffTimeline";
import type { UiSemanticValidatorHandoffTimelineEvent } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type EventStateMode = "all" | "RECORDED_READY" | "CURRENT_OPEN_STAGE" | "AWAITING_EXTERNAL_ARTIFACT" | "ATTENTION_REQUIRED" | "MISSING_EVIDENCE" | "BLOCKED";
type StageMode = "all" | "decision" | "signoff" | "custody" | "archive" | "closure";
type TimelineRow = UiSemanticValidatorHandoffTimelineEvent & { __id: string };

const EVENT_STATE_MODES: EventStateMode[] = ["all", "RECORDED_READY", "CURRENT_OPEN_STAGE", "AWAITING_EXTERNAL_ARTIFACT", "ATTENTION_REQUIRED", "MISSING_EVIDENCE", "BLOCKED"];
const STAGE_MODES: StageMode[] = ["all", "decision", "signoff", "custody", "archive", "closure"];

function text(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

function countRows(counts: Record<string, number> | undefined) {
  return Object.entries(counts ?? {}).map(([k, v]) => ({ k, v: String(v) }));
}

export default function SemanticValidatorHandoffTimelinePage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const [eventStateMode, setEventStateMode] = useState<EventStateMode>("all");
  const [stageMode, setStageMode] = useState<StageMode>("all");
  const [experimentNeedle, setExperimentNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [includeReady, setIncludeReady] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiSemanticValidatorHandoffTimelineQuery = useMemo(
    () => ({
      eventState: eventStateMode === "all" ? null : eventStateMode,
      stage: stageMode === "all" ? null : stageMode,
      experimentIdContains: experimentNeedle.trim() || null,
      issueContains: issueNeedle.trim() || null,
      includeReady,
      limit: 500,
    }),
    [eventStateMode, experimentNeedle, includeReady, issueNeedle, stageMode],
  );

  const timeline = useUiSemanticValidatorHandoffTimeline(query);
  const summary = timeline.data?.summary ?? {};
  const rows = useMemo<TimelineRow[]>(
    () => (timeline.data?.timeline_events ?? []).map((row, i) => ({ ...row, __id: `${row.timeline_event_id}:${i}` })),
    [timeline.data?.timeline_events],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(timeline.data?.degraded);
  const sourceDegraded = asStringArray(timeline.data?.source_degraded);
  const guardrails = asStringArray(timeline.data?.guardrails);
  const selectedIssues = asStringArray(selectedRow?.issue_codes);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "semantic-validator-handoff-timeline-status",
        severity: Number(summary.blocked_event_count ?? 0) > 0 ? "bad" : Number(summary.external_artifact_required_count ?? 0) > 0 || degraded.length ? "warn" : "ok",
        text: `handoff timeline events=${summary.timeline_event_count_returned ?? 0} blocked=${summary.blocked_event_count ?? 0} missing=${summary.missing_evidence_event_count ?? 0}`,
      },
      {
        id: "semantic-validator-handoff-timeline-boundary",
        severity: "info",
        text: "timeline cockpit read-plane only · no mutation/write/submit/adjudicate/promote/execute authority",
      },
    ],
    [degraded.length, summary],
  );
  const ticker = useMemo(
    () => [
      { severity: Number(summary.blocked_event_count ?? 0) > 0 ? ("bad" as const) : ("ok" as const), text: `BLOCKED ${summary.blocked_event_count ?? 0}` },
      { severity: Number(summary.external_artifact_required_count ?? 0) > 0 ? ("warn" as const) : ("ok" as const), text: `EXT ${summary.external_artifact_required_count ?? 0}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<TimelineRow>[] = useMemo(
    () => [
      { key: "state", header: "state", width: "18%", cell: (row) => <StatusBadge raw={row.event_state} /> },
      { key: "stage", header: "stage", width: "11%", cell: (row) => <code>{row.stage}</code> },
      { key: "experiment", header: "experiment", width: "14%", cell: (row) => <code>{text(row.experiment_id)}</code> },
      { key: "present", header: "present", width: "8%", cell: (row) => <code>{String(row.present)}</code> },
      { key: "ready", header: "ready", width: "8%", cell: (row) => <code>{String(row.ready)}</code> },
      { key: "focus", header: "operator focus", cell: (row) => <code>{row.operator_focus}</code> },
    ],
    [],
  );

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF TIMELINE</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF TIMELINE</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/timeline · stage-level timeline events derived from handoff continuity</p>
      {timeline.isLoading && <p className="muted">Loading…</p>}
      {timeline.isError && <p className="term-error">{timeline.error.message}</p>}

      {timeline.data && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Timeline state" badge={<StatusBadge raw={`${summary.timeline_event_count_returned ?? 0} events`} />} onInspect={() => openInspector({ title: "/ui/semantic-validator-handoff/timeline", rawJson: timeline.data })}>
              <TermKV rows={[{ k: "schema", v: timeline.data.schema_version }, { k: "events", v: String(summary.timeline_event_count_returned ?? 0) }, { k: "blocked", v: String(summary.blocked_event_count ?? 0) }, { k: "missing", v: String(summary.missing_evidence_event_count ?? 0) }, { k: "external", v: String(summary.external_artifact_required_count ?? 0) }]} />
            </Pane>
            <Pane title="Selected event" onInspect={selectedRow ? () => openInspector({ title: "Selected semantic-validator handoff timeline event", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "event", v: text(selectedRow?.timeline_event_id) }, { k: "stage", v: text(selectedRow?.stage) }, { k: "state", v: text(selectedRow?.event_state) }, { k: "focus", v: text(selectedRow?.operator_focus) }, { k: "route", v: text(selectedRow?.stage_route) }]} />
            </Pane>
            <Pane title="Authority boundary">
              <TermKV rows={[{ k: "read_plane", v: String(timeline.data.read_plane_only) }, { k: "mutation", v: timeline.data.mutation_authority }, { k: "submit", v: timeline.data.validator_submission_authority }, { k: "execute", v: timeline.data.execution_authority }]} />
            </Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-filter-row">
              <label>State <select value={eventStateMode} onChange={(e) => setEventStateMode(e.target.value as EventStateMode)}>{EVENT_STATE_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Stage <select value={stageMode} onChange={(e) => setStageMode(e.target.value as StageMode)}>{STAGE_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Experiment <input value={experimentNeedle} onChange={(e) => setExperimentNeedle(e.target.value)} placeholder="EXP-…" /></label>
              <label>Issue <input value={issueNeedle} onChange={(e) => setIssueNeedle(e.target.value)} placeholder="digest, missing…" /></label>
              <label><input type="checkbox" checked={includeReady} onChange={(e) => setIncludeReady(e.target.checked)} /> ready</label>
            </div>
          </Pane>

          <Pane title="Timeline events" badge={<StatusBadge raw={`${rows.length} rows`} />}>
            <DenseTable columns={columns} rows={rows} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => setSelected(row.__id)} empty="No timeline events matched the current filters." />
          </Pane>

          <PaneGrid cols={3}>
            <Pane title="Event states"><TermKV rows={countRows(timeline.data.event_state_counts)} /></Pane>
            <Pane title="Stages"><TermKV rows={countRows(timeline.data.stage_counts)} /></Pane>
            <Pane title="Selected issues"><ul className="term-list">{selectedIssues.length ? selectedIssues.map((item) => <li key={item}><code>{item}</code></li>) : <li>—</li>}</ul></Pane>
          </PaneGrid>

          <PaneGrid cols={3}>
            <Pane title="Source degraded"><ul className="term-list">{sourceDegraded.length ? sourceDegraded.map((item) => <li key={item}><code>{item}</code></li>) : <li>—</li>}</ul></Pane>
            <Pane title="Timeline degraded"><ul className="term-list">{degraded.length ? degraded.map((item) => <li key={item}><code>{item}</code></li>) : <li>—</li>}</ul></Pane>
            <Pane title="Guardrails"><ul className="term-list">{guardrails.map((item) => <li key={item}><code>{item}</code></li>)}</ul></Pane>
          </PaneGrid>

          <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/timeline JSON" data={timeline.data} />
        </>
      )}
    </div>
  );
}
