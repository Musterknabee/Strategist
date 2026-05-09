"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useUiSemanticValidatorHandoffClearanceVerificationBoard } from "@/hooks/useUiSemanticValidatorHandoffClearanceVerificationBoard";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";

function text(value: unknown): string { return value === null || value === undefined || value === "" ? "—" : String(value); }
function countRows(counts?: Record<string, number>) { return Object.entries(counts ?? {}).map(([k, v]) => ({ k, v: String(v) })); }

export default function SemanticValidatorHandoffClearanceVerificationBoardPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const q = useUiSemanticValidatorHandoffClearanceVerificationBoard({ limit: 200 });
  const summary = q.data?.summary ?? {};
  if (!config.ok) return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CLEARANCE VERIFICATION BOARD</h1><p className="muted">{config.error.message}</p></div>;
  return <div className="term-page">
    <h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CLEARANCE VERIFICATION BOARD</h1>
    <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/clearance-verification-board · read-only verification observations derived from the clearance resolution plan</p>
    {q.isLoading && <p className="muted">Loading…</p>}
    {q.isError && <p className="term-error">{q.error.message}</p>}
    {q.data && <>
      <PaneGrid cols={3}>
        <Pane title="Verification board" badge={<StatusBadge raw={q.data.degraded.length ? "DEGRADED" : "OK"} />}><TermKV rows={[{ k: "schema", v: q.data.schema_version }, { k: "cards", v: text(summary.verification_card_count_returned) }, { k: "fail_closed", v: text(summary.fail_closed_count) }, { k: "waiting", v: text(summary.waiting_count) }]} /></Pane>
        <Pane title="Authority firewall"><TermKV rows={[{ k: "read_plane", v: String(q.data.read_plane_only) }, { k: "verify_write", v: q.data.verification_write_authority }, { k: "completion", v: q.data.completion_assertion_authority }, { k: "approval", v: q.data.operator_approval_authority }, { k: "signoff", v: q.data.signoff_authority }]} /></Pane>
        <Pane title="Latest card"><TermKV rows={[{ k: "card", v: text(q.data.latest?.verification_card_id) }, { k: "lane", v: text(q.data.latest?.evidence_lane) }, { k: "status", v: text(q.data.latest?.verification_status) }, { k: "result", v: text(q.data.latest?.verification_result) }]} /></Pane>
      </PaneGrid>
      <Pane title="Verification cards"><table className="term-table"><thead><tr><th>#</th><th>lane</th><th>status</th><th>result</th><th>priority</th><th>gate</th><th>verification note</th></tr></thead><tbody>{q.data.verification_cards.map((r, i) => <tr key={`${r.verification_card_id}:${i}`}><td><code>{r.ordinal}</code></td><td><code>{r.evidence_lane}</code></td><td><StatusBadge raw={r.verification_status} /></td><td><StatusBadge raw={r.verification_result} /></td><td><StatusBadge raw={r.priority} /></td><td><code>{r.verification_gate}</code></td><td>{r.verification_note}</td></tr>)}</tbody></table></Pane>
      <PaneGrid cols={3}><Pane title="Statuses"><TermKV rows={countRows(q.data.verification_status_counts)} /></Pane><Pane title="Results"><TermKV rows={countRows(q.data.verification_result_counts)} /></Pane><Pane title="Phases"><TermKV rows={countRows(q.data.phase_counts)} /></Pane></PaneGrid>
      {q.data.degraded.length > 0 && <Pane title="Degraded signals" badge={<StatusBadge raw="DEGRADED" />}><ul className="term-list">{q.data.degraded.map((line) => <li key={line}>{line}</li>)}</ul></Pane>}
      <Pane title="Guardrails"><ul className="term-list">{q.data.guardrails.map((line) => <li key={line}>{line}</li>)}</ul></Pane>
      <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/clearance-verification-board JSON" data={q.data} />
    </>}
  </div>;
}
