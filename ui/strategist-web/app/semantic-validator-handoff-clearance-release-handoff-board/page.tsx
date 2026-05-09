"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useUiSemanticValidatorHandoffClearanceReleaseHandoffBoard } from "@/hooks/useUiSemanticValidatorHandoffClearanceReleaseHandoffBoard";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";

function text(value: unknown): string { return value === null || value === undefined || value === "" ? "—" : String(value); }
function countRows(counts?: Record<string, number>) { return Object.entries(counts ?? {}).map(([k, v]) => ({ k, v: String(v) })); }

export default function SemanticValidatorHandoffClearanceReleaseHandoffBoardPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const q = useUiSemanticValidatorHandoffClearanceReleaseHandoffBoard({ limit: 200 });
  const summary = q.data?.summary ?? {};
  if (!config.ok) return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CLEARANCE RELEASE HANDOFF BOARD</h1><p className="muted">{config.error.message}</p></div>;
  return <div className="term-page">
    <h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CLEARANCE RELEASE HANDOFF BOARD</h1>
    <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/clearance-release-handoff-board · read-only human-transfer handoff observations derived from release packets</p>
    {q.isLoading && <p className="muted">Loading…</p>}
    {q.isError && <p className="term-error">{q.error.message}</p>}
    {q.data && <>
      <PaneGrid cols={3}>
        <Pane title="Release handoffs" badge={<StatusBadge raw={q.data.degraded.length ? "DEGRADED" : "OK"} />}><TermKV rows={[{ k: "schema", v: q.data.schema_version }, { k: "handoffs", v: text(summary.release_handoff_count_returned) }, { k: "fail_closed", v: text(summary.fail_closed_count) }, { k: "human_transfer_ready", v: text(summary.human_transfer_ready_observation_count) }]} /></Pane>
        <Pane title="Authority firewall"><TermKV rows={[{ k: "read_plane", v: String(q.data.read_plane_only) }, { k: "handoff_write", v: q.data.release_handoff_write_authority }, { k: "packet_write", v: q.data.release_packet_write_authority }, { k: "release_write", v: q.data.release_record_write_authority }, { k: "handoff_release", v: q.data.handoff_release_authority }, { k: "approval", v: q.data.operator_approval_authority }]} /></Pane>
        <Pane title="Latest handoff"><TermKV rows={[{ k: "handoff", v: text(q.data.latest?.release_handoff_id) }, { k: "lane", v: text(q.data.latest?.evidence_lane) }, { k: "status", v: text(q.data.latest?.release_handoff_status) }, { k: "readiness", v: text(q.data.latest?.release_handoff_readiness) }]} /></Pane>
      </PaneGrid>
      <Pane title="Release handoff rows"><table className="term-table"><thead><tr><th>#</th><th>lane</th><th>handoff status</th><th>readiness</th><th>packet source</th><th>priority</th><th>gate</th><th>instruction</th></tr></thead><tbody>{q.data.release_handoffs.map((r, i) => <tr key={`${r.release_handoff_id}:${i}`}><td><code>{r.ordinal}</code></td><td><code>{r.evidence_lane}</code></td><td><StatusBadge raw={r.release_handoff_status} /></td><td><StatusBadge raw={r.release_handoff_readiness} /></td><td><StatusBadge raw={r.source_release_packet_status} /></td><td><StatusBadge raw={r.priority} /></td><td><code>{r.release_handoff_gate}</code></td><td>{r.release_handoff_instruction}</td></tr>)}</tbody></table></Pane>
      <PaneGrid cols={3}><Pane title="Handoff statuses"><TermKV rows={countRows(q.data.release_handoff_status_counts)} /></Pane><Pane title="Handoff readiness"><TermKV rows={countRows(q.data.release_handoff_readiness_counts)} /></Pane><Pane title="Release packet source"><TermKV rows={countRows(q.data.source_release_packet_status_counts)} /></Pane></PaneGrid>
      {q.data.degraded.length > 0 && <Pane title="Degraded signals" badge={<StatusBadge raw="DEGRADED" />}><ul className="term-list">{q.data.degraded.map((line) => <li key={line}>{line}</li>)}</ul></Pane>}
      <Pane title="Guardrails"><ul className="term-list">{q.data.guardrails.map((line) => <li key={line}>{line}</li>)}</ul></Pane>
      <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/clearance-release-handoff-board JSON" data={q.data} />
    </>}
  </div>;
}
