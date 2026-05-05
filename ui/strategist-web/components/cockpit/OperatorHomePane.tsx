"use client";

import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import type { OperatorHomeSummary } from "@/lib/operator/operator-home-summary-model";
import type { OperatorModeId } from "@/lib/operator/operator-modes";
import { OperatorFlowStrip } from "./OperatorFlowStrip";

type Props = { summary: OperatorHomeSummary; onShowAdvanced: () => void; onOpenDetail: (mode: OperatorModeId) => void };
const v = (n: number | null) => (n == null ? "UNKNOWN" : String(n));

export function OperatorHomePane({ summary, onShowAdvanced, onOpenDetail }: Props) {
  return (
    <section className="cockpit-home" data-testid="cockpit-operator-home">
      <Pane title="Operator Home" dense badge={<StatusBadge raw={summary.overall_status} />}>
        <p className="cockpit-home__intro" data-testid="cockpit-home-safety">
          Paper/research only. No live trading, no broker orders, no production deployment approval, no operator signoff,
          and no profitability claim. Missing data remains UNKNOWN or NO_PAPER_DATA; evidence/replay verifies integrity,
          not strategy quality.
        </p>
        <OperatorFlowStrip onOpenDetail={onOpenDetail} />
        <div className="cockpit-home__cards">
          <article className="cockpit-home__card"><span>Strategies</span><strong>{v(summary.strategy_count)}</strong></article>
          <article className="cockpit-home__card"><span>Candidates</span><strong>{v(summary.active_candidate_count)}</strong></article>
          <article className="cockpit-home__card"><span>Paper Wins</span><strong>{summary.paper_win_count}</strong></article>
          <article className="cockpit-home__card"><span>Paper Losses</span><strong>{summary.paper_loss_count}</strong></article>
          <article className="cockpit-home__card"><span>Paper Unknown</span><strong>{summary.paper_unknown_count}</strong></article>
          <article className="cockpit-home__card"><span>Blocked</span><strong>{summary.blocked_count}</strong></article>
          <article className="cockpit-home__card"><span>Needs Review</span><strong>{summary.warning_count}</strong></article>
          <article className="cockpit-home__card"><span>Replay Issues</span><strong>{summary.replay_problem_count}</strong></article>
          <article className="cockpit-home__card"><span>Provider Health</span><strong>OK:{summary.provider_ok_count} · Pending:{summary.provider_pending_key_count}</strong></article>
        </div>
        <div className="cockpit-home__split">
          <div>
            <h3>What needs attention first?</h3>
            <ul data-testid="cockpit-home-attention">
              {summary.top_attention_items.length > 0 ? summary.top_attention_items.map((item) => <li key={item}>{item}</li>) : <li>No urgent blockers from current read-plane payloads. Continue with Candidate Workbench before making operator decisions.</li>}
            </ul>
          </div>
          <div>
            <h3>Where to click next?</h3>
            <p data-testid="cockpit-home-next-action"><StatusBadge raw={summary.next_action} /> {summary.next_action_reason}</p>
            <p className="cockpit-home__meta">Generated: {summary.generated_at_utc}</p>
          </div>
        </div>
        <div className="cockpit-home__table-wrap">
          <table className="term-dense-table" data-testid="cockpit-home-scoreboard">
            <thead><tr><th>Strategy</th><th>Paper result</th><th>Evidence</th><th>Replay</th><th>Data health</th><th>Status</th><th>Next action</th><th>Details</th></tr></thead>
            <tbody>
              {summary.strategy_rows.length > 0 ? summary.strategy_rows.map((row) => (
                <tr key={row.strategy_id}>
                  <td>{row.label}</td><td>{row.paper_result_label}</td><td>{row.evidence_status}</td><td>{row.replay_status}</td><td>{row.provider_status}</td><td><StatusBadge raw={row.status} /></td><td>{row.next_action}</td>
                  <td><button type="button" className="linkish" aria-label={`Open ${row.label} details in ${row.detail_target.replace(/_/g, " ")}`} onClick={() => onOpenDetail((row.detail_target as OperatorModeId) || "DAILY_OPS")}>Open {row.detail_target.replace(/_/g, " ").toLowerCase()}</button></td>
                </tr>
              )) : <tr><td colSpan={8}>UNKNOWN · no strategy rows available from read-plane payloads.</td></tr>}
            </tbody>
          </table>
        </div>
        <div className="cockpit-home__actions" data-testid="cockpit-home-links">
          <button type="button" className="term-btn term-btn--sm" data-testid="cockpit-open-candidate-workbench" onClick={() => onOpenDetail("RESEARCH_REVIEW")}>Open Candidate Workbench</button>
          <button type="button" className="term-btn term-btn--sm" onClick={() => onOpenDetail("FORENSIC_AUDIT")}>Evidence / Replay</button>
          <button type="button" className="term-btn term-btn--sm" onClick={() => onOpenDetail("CAPITAL_FIREWALL")}>Capital Firewall</button>
          <button type="button" className="term-btn term-btn--sm" onClick={() => onOpenDetail("RELEASE_CONTROL")}>Release Control</button>
          <button type="button" className="term-btn term-btn--sm" onClick={() => onOpenDetail("SYSTEM_TOPOLOGY")}>System Topology</button>
          <button type="button" className="term-btn term-btn--sm" onClick={() => onOpenDetail("FIRST_RUN")}>Provider Setup / First Run</button>
          <button type="button" className="term-btn term-btn--sm" data-testid="cockpit-show-advanced" onClick={onShowAdvanced}>Show advanced cockpit details</button>
        </div>
      </Pane>
    </section>
  );
}
