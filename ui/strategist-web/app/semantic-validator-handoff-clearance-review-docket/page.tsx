"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useUiSemanticValidatorHandoffClearanceReviewDocket } from "@/hooks/useUiSemanticValidatorHandoffClearanceReviewDocket";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";

function text(value: unknown): string { return value === null || value === undefined || value === "" ? "—" : String(value); }
function countRows(counts?: Record<string, number>) { return Object.entries(counts ?? {}).map(([k, v]) => ({ k, v: String(v) })); }

export default function SemanticValidatorHandoffClearanceReviewDocketPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const q = useUiSemanticValidatorHandoffClearanceReviewDocket({ limit: 200 });
  const summary = q.data?.summary ?? {};
  if (!config.ok) return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CLEARANCE REVIEW DOCKET</h1><p className="muted">{config.error.message}</p></div>;
  return <div className="term-page">
    <h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CLEARANCE REVIEW DOCKET</h1>
    <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/clearance-review-docket · read-only authorized-review routing observations derived from clearance closeout cards</p>
    {q.isLoading && <p className="muted">Loading…</p>}
    {q.isError && <p className="term-error">{q.error.message}</p>}
    {q.data && <>
      <PaneGrid cols={3}>
        <Pane title="Review docket" badge={<StatusBadge raw={q.data.degraded.length ? "DEGRADED" : "OK"} />}><TermKV rows={[{ k: "schema", v: q.data.schema_version }, { k: "dockets", v: text(summary.review_docket_count_returned) }, { k: "fail_closed", v: text(summary.fail_closed_count) }, { k: "authorized_ready", v: text(summary.authorized_review_observation_count) }]} /></Pane>
        <Pane title="Authority firewall"><TermKV rows={[{ k: "read_plane", v: String(q.data.read_plane_only) }, { k: "review_write", v: q.data.review_record_write_authority }, { k: "authorization", v: q.data.review_authorization_authority }, { k: "approval", v: q.data.operator_approval_authority }, { k: "signoff", v: q.data.signoff_authority }]} /></Pane>
        <Pane title="Latest docket"><TermKV rows={[{ k: "docket", v: text(q.data.latest?.review_docket_id) }, { k: "lane", v: text(q.data.latest?.evidence_lane) }, { k: "status", v: text(q.data.latest?.docket_status) }, { k: "readiness", v: text(q.data.latest?.docket_readiness) }]} /></Pane>
      </PaneGrid>
      <Pane title="Review dockets"><table className="term-table"><thead><tr><th>#</th><th>lane</th><th>docket status</th><th>readiness</th><th>closeout</th><th>priority</th><th>gate</th><th>instruction</th></tr></thead><tbody>{q.data.review_dockets.map((r, i) => <tr key={`${r.review_docket_id}:${i}`}><td><code>{r.ordinal}</code></td><td><code>{r.evidence_lane}</code></td><td><StatusBadge raw={r.docket_status} /></td><td><StatusBadge raw={r.docket_readiness} /></td><td><StatusBadge raw={r.source_closeout_status} /></td><td><StatusBadge raw={r.priority} /></td><td><code>{r.review_gate}</code></td><td>{r.review_instruction}</td></tr>)}</tbody></table></Pane>
      <PaneGrid cols={3}><Pane title="Docket statuses"><TermKV rows={countRows(q.data.docket_status_counts)} /></Pane><Pane title="Readiness"><TermKV rows={countRows(q.data.docket_readiness_counts)} /></Pane><Pane title="Closeout source"><TermKV rows={countRows(q.data.source_closeout_status_counts)} /></Pane></PaneGrid>
      {q.data.degraded.length > 0 && <Pane title="Degraded signals" badge={<StatusBadge raw="DEGRADED" />}><ul className="term-list">{q.data.degraded.map((line) => <li key={line}>{line}</li>)}</ul></Pane>}
      <Pane title="Guardrails"><ul className="term-list">{q.data.guardrails.map((line) => <li key={line}>{line}</li>)}</ul></Pane>
      <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/clearance-review-docket JSON" data={q.data} />
    </>}
  </div>;
}
