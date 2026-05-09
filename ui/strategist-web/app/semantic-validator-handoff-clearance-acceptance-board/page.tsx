"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useUiSemanticValidatorHandoffClearanceAcceptanceBoard } from "@/hooks/useUiSemanticValidatorHandoffClearanceAcceptanceBoard";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";

function text(value: unknown): string { return value === null || value === undefined || value === "" ? "—" : String(value); }
function countRows(counts?: Record<string, number>) { return Object.entries(counts ?? {}).map(([k, v]) => ({ k, v: String(v) })); }

export default function SemanticValidatorHandoffClearanceAcceptanceBoardPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const q = useUiSemanticValidatorHandoffClearanceAcceptanceBoard({ limit: 200 });
  const summary = q.data?.summary ?? {};
  if (!config.ok) return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CLEARANCE ACCEPTANCE BOARD</h1><p className="muted">{config.error.message}</p></div>;
  return <div className="term-page">
    <h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CLEARANCE ACCEPTANCE BOARD</h1>
    <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/clearance-acceptance-board · read-only clearance-acceptance observations derived from signoff packets</p>
    {q.isLoading && <p className="muted">Loading…</p>}
    {q.isError && <p className="term-error">{q.error.message}</p>}
    {q.data && <>
      <PaneGrid cols={3}>
        <Pane title="Acceptance cards" badge={<StatusBadge raw={q.data.degraded.length ? "DEGRADED" : "OK"} />}><TermKV rows={[{ k: "schema", v: q.data.schema_version }, { k: "cards", v: text(summary.acceptance_card_count_returned) }, { k: "fail_closed", v: text(summary.fail_closed_count) }, { k: "acceptance_ready", v: text(summary.acceptance_ready_observation_count) }]} /></Pane>
        <Pane title="Authority firewall"><TermKV rows={[{ k: "read_plane", v: String(q.data.read_plane_only) }, { k: "acceptance_write", v: q.data.acceptance_record_write_authority }, { k: "acceptance_assert", v: q.data.acceptance_assertion_authority }, { k: "operator_signoff", v: q.data.operator_signoff_authority }, { k: "approval", v: q.data.operator_approval_authority }]} /></Pane>
        <Pane title="Latest card"><TermKV rows={[{ k: "card", v: text(q.data.latest?.acceptance_card_id) }, { k: "lane", v: text(q.data.latest?.evidence_lane) }, { k: "status", v: text(q.data.latest?.acceptance_status) }, { k: "readiness", v: text(q.data.latest?.acceptance_readiness) }]} /></Pane>
      </PaneGrid>
      <Pane title="Acceptance board rows"><table className="term-table"><thead><tr><th>#</th><th>lane</th><th>acceptance status</th><th>readiness</th><th>signoff source</th><th>priority</th><th>gate</th><th>instruction</th></tr></thead><tbody>{q.data.acceptance_cards.map((r, i) => <tr key={`${r.acceptance_card_id}:${i}`}><td><code>{r.ordinal}</code></td><td><code>{r.evidence_lane}</code></td><td><StatusBadge raw={r.acceptance_status} /></td><td><StatusBadge raw={r.acceptance_readiness} /></td><td><StatusBadge raw={r.source_signoff_status} /></td><td><StatusBadge raw={r.priority} /></td><td><code>{r.acceptance_gate}</code></td><td>{r.acceptance_instruction}</td></tr>)}</tbody></table></Pane>
      <PaneGrid cols={3}><Pane title="Acceptance statuses"><TermKV rows={countRows(q.data.acceptance_status_counts)} /></Pane><Pane title="Readiness"><TermKV rows={countRows(q.data.acceptance_readiness_counts)} /></Pane><Pane title="Signoff source"><TermKV rows={countRows(q.data.source_signoff_status_counts)} /></Pane></PaneGrid>
      {q.data.degraded.length > 0 && <Pane title="Degraded signals" badge={<StatusBadge raw="DEGRADED" />}><ul className="term-list">{q.data.degraded.map((line) => <li key={line}>{line}</li>)}</ul></Pane>}
      <Pane title="Guardrails"><ul className="term-list">{q.data.guardrails.map((line) => <li key={line}>{line}</li>)}</ul></Pane>
      <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/clearance-acceptance-board JSON" data={q.data} />
    </>}
  </div>;
}
