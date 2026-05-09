"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useUiSemanticValidatorHandoffClearanceActionRegister } from "@/hooks/useUiSemanticValidatorHandoffClearanceActionRegister";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";

function text(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

function countRows(counts?: Record<string, number>) {
  return Object.entries(counts ?? {}).map(([k, v]) => ({ k, v: String(v) }));
}

export default function SemanticValidatorHandoffClearanceActionRegisterPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const q = useUiSemanticValidatorHandoffClearanceActionRegister({ limit: 200 });
  const summary = q.data?.summary ?? {};

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CLEARANCE ACTION REGISTER</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF CLEARANCE ACTION REGISTER</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/clearance-action-register · read-only action register derived from clearance operations</p>
      {q.isLoading && <p className="muted">Loading…</p>}
      {q.isError && <p className="term-error">{q.error.message}</p>}

      {q.data && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Action register" badge={<StatusBadge raw={q.data.degraded.length ? "DEGRADED" : "OK"} />}>
              <TermKV rows={[{ k: "schema", v: q.data.schema_version }, { k: "actions", v: text(summary.action_count_returned) }, { k: "blocked", v: text(summary.blocked_action_count) }, { k: "review", v: text(summary.human_review_action_count) }]} />
            </Pane>
            <Pane title="Authority firewall">
              <TermKV rows={[{ k: "read_plane", v: String(q.data.read_plane_only) }, { k: "ack", v: q.data.action_acknowledgment_authority }, { k: "execute", v: q.data.action_execution_authority }, { k: "approve", v: q.data.operator_approval_authority }, { k: "signoff", v: q.data.signoff_authority }]} />
            </Pane>
            <Pane title="Latest action">
              <TermKV rows={[{ k: "action", v: text(q.data.latest?.action_id) }, { k: "lane", v: text(q.data.latest?.evidence_lane) }, { k: "state", v: text(q.data.latest?.action_state) }, { k: "type", v: text(q.data.latest?.action_type) }]} />
            </Pane>
          </PaneGrid>

          <Pane title="Clearance actions">
            <table className="term-table">
              <thead><tr><th>#</th><th>lane</th><th>state</th><th>type</th><th>priority</th><th>gate</th><th>operator action</th></tr></thead>
              <tbody>{q.data.action_rows.map((r, i) => <tr key={`${r.action_id}:${i}`}><td><code>{r.ordinal}</code></td><td><code>{r.evidence_lane}</code></td><td><StatusBadge raw={r.action_state} /></td><td><StatusBadge raw={r.action_type} /></td><td><StatusBadge raw={r.priority} /></td><td><code>{r.completion_gate}</code></td><td>{r.operator_action}</td></tr>)}</tbody>
            </table>
          </Pane>

          <PaneGrid cols={3}>
            <Pane title="Action states"><TermKV rows={countRows(q.data.action_state_counts)} /></Pane>
            <Pane title="Action types"><TermKV rows={countRows(q.data.action_type_counts)} /></Pane>
            <Pane title="Operation states"><TermKV rows={countRows(q.data.operation_state_counts)} /></Pane>
          </PaneGrid>

          {q.data.degraded.length > 0 && <Pane title="Degraded signals" badge={<StatusBadge raw="DEGRADED" />}><ul className="term-list">{q.data.degraded.map((line) => <li key={line}>{line}</li>)}</ul></Pane>}
          <Pane title="Guardrails"><ul className="term-list">{q.data.guardrails.map((line) => <li key={line}>{line}</li>)}</ul></Pane>
          <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/clearance-action-register JSON" data={q.data} />
        </>
      )}
    </div>
  );
}
