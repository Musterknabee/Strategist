"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useUiSemanticValidatorHandoffClearanceSignoffPacket } from "@/hooks/useUiSemanticValidatorHandoffClearanceSignoffPacket";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";

function text(value: unknown): string { return value === null || value === undefined || value === "" ? "—" : String(value); }
function countRows(counts?: Record<string, number>) { return Object.entries(counts ?? {}).map(([k, v]) => ({ k, v: String(v) })); }

export default function SemanticValidatorHandoffClearanceSignoffPacketPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const q = useUiSemanticValidatorHandoffClearanceSignoffPacket({ limit: 200 });
  const summary = q.data?.summary ?? {};
  if (!config.ok) return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CLEARANCE SIGNOFF PACKET</h1><p className="muted">{config.error.message}</p></div>;
  return <div className="term-page">
    <h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CLEARANCE SIGNOFF PACKET</h1>
    <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/clearance-signoff-packet · read-only human-signoff packet observations derived from clearance review dockets</p>
    {q.isLoading && <p className="muted">Loading…</p>}
    {q.isError && <p className="term-error">{q.error.message}</p>}
    {q.data && <>
      <PaneGrid cols={3}>
        <Pane title="Signoff packets" badge={<StatusBadge raw={q.data.degraded.length ? "DEGRADED" : "OK"} />}><TermKV rows={[{ k: "schema", v: q.data.schema_version }, { k: "packets", v: text(summary.signoff_packet_count_returned) }, { k: "fail_closed", v: text(summary.fail_closed_count) }, { k: "signoff_ready", v: text(summary.signoff_ready_observation_count) }]} /></Pane>
        <Pane title="Authority firewall"><TermKV rows={[{ k: "read_plane", v: String(q.data.read_plane_only) }, { k: "packet_write", v: q.data.signoff_packet_write_authority }, { k: "record_write", v: q.data.signoff_record_write_authority }, { k: "operator_signoff", v: q.data.operator_signoff_authority }, { k: "approval", v: q.data.operator_approval_authority }]} /></Pane>
        <Pane title="Latest packet"><TermKV rows={[{ k: "packet", v: text(q.data.latest?.signoff_packet_id) }, { k: "lane", v: text(q.data.latest?.evidence_lane) }, { k: "status", v: text(q.data.latest?.signoff_status) }, { k: "readiness", v: text(q.data.latest?.signoff_readiness) }]} /></Pane>
      </PaneGrid>
      <Pane title="Signoff packet rows"><table className="term-table"><thead><tr><th>#</th><th>lane</th><th>signoff status</th><th>readiness</th><th>docket</th><th>priority</th><th>gate</th><th>instruction</th></tr></thead><tbody>{q.data.signoff_packets.map((r, i) => <tr key={`${r.signoff_packet_id}:${i}`}><td><code>{r.ordinal}</code></td><td><code>{r.evidence_lane}</code></td><td><StatusBadge raw={r.signoff_status} /></td><td><StatusBadge raw={r.signoff_readiness} /></td><td><StatusBadge raw={r.source_docket_status} /></td><td><StatusBadge raw={r.priority} /></td><td><code>{r.signoff_gate}</code></td><td>{r.signoff_instruction}</td></tr>)}</tbody></table></Pane>
      <PaneGrid cols={3}><Pane title="Signoff statuses"><TermKV rows={countRows(q.data.signoff_status_counts)} /></Pane><Pane title="Readiness"><TermKV rows={countRows(q.data.signoff_readiness_counts)} /></Pane><Pane title="Review source"><TermKV rows={countRows(q.data.source_docket_status_counts)} /></Pane></PaneGrid>
      {q.data.degraded.length > 0 && <Pane title="Degraded signals" badge={<StatusBadge raw="DEGRADED" />}><ul className="term-list">{q.data.degraded.map((line) => <li key={line}>{line}</li>)}</ul></Pane>}
      <Pane title="Guardrails"><ul className="term-list">{q.data.guardrails.map((line) => <li key={line}>{line}</li>)}</ul></Pane>
      <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/clearance-signoff-packet JSON" data={q.data} />
    </>}
  </div>;
}
