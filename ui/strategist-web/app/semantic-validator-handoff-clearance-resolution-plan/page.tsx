"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useUiSemanticValidatorHandoffClearanceResolutionPlan } from "@/hooks/useUiSemanticValidatorHandoffClearanceResolutionPlan";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";

function text(value: unknown): string { return value === null || value === undefined || value === "" ? "—" : String(value); }
function countRows(counts?: Record<string, number>) { return Object.entries(counts ?? {}).map(([k, v]) => ({ k, v: String(v) })); }

export default function SemanticValidatorHandoffClearanceResolutionPlanPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const q = useUiSemanticValidatorHandoffClearanceResolutionPlan({ limit: 200 });
  const summary = q.data?.summary ?? {};
  if (!config.ok) return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CLEARANCE RESOLUTION PLAN</h1><p className="muted">{config.error.message}</p></div>;
  return <div className="term-page">
    <h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CLEARANCE RESOLUTION PLAN</h1>
    <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/clearance-resolution-plan · read-only steps derived from clearance actions</p>
    {q.isLoading && <p className="muted">Loading…</p>}
    {q.isError && <p className="term-error">{q.error.message}</p>}
    {q.data && <>
      <PaneGrid cols={3}>
        <Pane title="Resolution plan" badge={<StatusBadge raw={q.data.degraded.length ? "DEGRADED" : "OK"} />}><TermKV rows={[{ k: "schema", v: q.data.schema_version }, { k: "steps", v: text(summary.resolution_step_count_returned) }, { k: "blockers", v: text(summary.blocker_triage_count) }, { k: "external", v: text(summary.external_artifact_collection_count) }]} /></Pane>
        <Pane title="Authority firewall"><TermKV rows={[{ k: "read_plane", v: String(q.data.read_plane_only) }, { k: "plan", v: q.data.plan_materialization_authority }, { k: "ack", v: q.data.step_acknowledgment_authority }, { k: "repair", v: q.data.repair_execution_authority }, { k: "signoff", v: q.data.signoff_authority }]} /></Pane>
        <Pane title="Latest step"><TermKV rows={[{ k: "step", v: text(q.data.latest?.resolution_step_id) }, { k: "lane", v: text(q.data.latest?.evidence_lane) }, { k: "phase", v: text(q.data.latest?.phase) }, { k: "state", v: text(q.data.latest?.step_state) }]} /></Pane>
      </PaneGrid>
      <Pane title="Resolution steps"><table className="term-table"><thead><tr><th>#</th><th>lane</th><th>phase</th><th>state</th><th>priority</th><th>gate</th><th>safe instruction</th></tr></thead><tbody>{q.data.resolution_steps.map((r, i) => <tr key={`${r.resolution_step_id}:${i}`}><td><code>{r.ordinal}</code></td><td><code>{r.evidence_lane}</code></td><td><StatusBadge raw={r.phase} /></td><td><StatusBadge raw={r.step_state} /></td><td><StatusBadge raw={r.priority} /></td><td><code>{r.completion_gate}</code></td><td>{r.safe_instruction}</td></tr>)}</tbody></table></Pane>
      <PaneGrid cols={3}><Pane title="Phases"><TermKV rows={countRows(q.data.phase_counts)} /></Pane><Pane title="Step states"><TermKV rows={countRows(q.data.step_state_counts)} /></Pane><Pane title="Action states"><TermKV rows={countRows(q.data.action_state_counts)} /></Pane></PaneGrid>
      {q.data.degraded.length > 0 && <Pane title="Degraded signals" badge={<StatusBadge raw="DEGRADED" />}><ul className="term-list">{q.data.degraded.map((line) => <li key={line}>{line}</li>)}</ul></Pane>}
      <Pane title="Guardrails"><ul className="term-list">{q.data.guardrails.map((line) => <li key={line}>{line}</li>)}</ul></Pane>
      <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/clearance-resolution-plan JSON" data={q.data} />
    </>}
  </div>;
}
