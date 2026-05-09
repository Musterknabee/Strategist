"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useUiSemanticValidatorHandoffClearanceOperationsBoard } from "@/hooks/useUiSemanticValidatorHandoffClearanceOperationsBoard";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";

function text(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

function countRows(counts?: Record<string, number>) {
  return Object.entries(counts ?? {}).map(([k, v]) => ({ k, v: String(v) }));
}

export default function SemanticValidatorHandoffClearanceOperationsBoardPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const q = useUiSemanticValidatorHandoffClearanceOperationsBoard({ limit: 200 });
  const summary = q.data?.summary ?? {};

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CLEARANCE OPERATIONS BOARD</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CLEARANCE OPERATIONS BOARD</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/clearance-operations-board · read-only clearance triage derived from coverage cards</p>
      {q.isLoading && <p className="muted">Loading…</p>}
      {q.isError && <p className="term-error">{q.error.message}</p>}

      {q.data && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Operations board" badge={<StatusBadge raw={q.data.degraded.length ? "DEGRADED" : "OK"} />}>
              <TermKV rows={[{ k: "schema", v: q.data.schema_version }, { k: "cards", v: text(summary.operation_card_count_returned) }, { k: "attention", v: text(summary.operator_attention_required_count) }, { k: "ready", v: text(summary.ready_for_review_operation_count) }]} />
            </Pane>
            <Pane title="Authority firewall">
              <TermKV rows={[{ k: "read_plane", v: String(q.data.read_plane_only) }, { k: "ack", v: q.data.operation_acknowledgment_authority }, { k: "approve", v: q.data.operator_approval_authority }, { k: "signoff", v: q.data.signoff_authority }, { k: "execute", v: q.data.execution_authority }]} />
            </Pane>
            <Pane title="Latest operation">
              <TermKV rows={[{ k: "card", v: text(q.data.latest?.operation_card_id) }, { k: "lane", v: text(q.data.latest?.evidence_lane) }, { k: "state", v: text(q.data.latest?.operation_state) }, { k: "action", v: text(q.data.latest?.action_group) }]} />
            </Pane>
          </PaneGrid>

          <Pane title="Clearance operations">
            <table className="term-table">
              <thead><tr><th>#</th><th>lane</th><th>state</th><th>action</th><th>coverage</th><th>rows</th><th>priority</th><th>safe next action</th></tr></thead>
              <tbody>{q.data.operation_cards.map((r, i) => <tr key={`${r.operation_card_id}:${i}`}><td><code>{r.ordinal}</code></td><td><code>{r.evidence_lane}</code></td><td><StatusBadge raw={r.operation_state} /></td><td><StatusBadge raw={r.action_group} /></td><td><code>{r.coverage_percent}%</code></td><td><code>{r.row_count}</code></td><td><StatusBadge raw={r.highest_priority} /></td><td>{r.next_safe_action}</td></tr>)}</tbody>
            </table>
          </Pane>

          <PaneGrid cols={3}>
            <Pane title="Operation states"><TermKV rows={countRows(q.data.operation_state_counts)} /></Pane>
            <Pane title="Action groups"><TermKV rows={countRows(q.data.action_group_counts)} /></Pane>
            <Pane title="Coverage status"><TermKV rows={countRows(q.data.coverage_status_counts)} /></Pane>
          </PaneGrid>

          {q.data.degraded.length > 0 && <Pane title="Degraded signals" badge={<StatusBadge raw="DEGRADED" />}><ul className="term-list">{q.data.degraded.map((line) => <li key={line}>{line}</li>)}</ul></Pane>}
          <Pane title="Guardrails"><ul className="term-list">{q.data.guardrails.map((line) => <li key={line}>{line}</li>)}</ul></Pane>
          <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/clearance-operations-board JSON" data={q.data} />
        </>
      )}
    </div>
  );
}
