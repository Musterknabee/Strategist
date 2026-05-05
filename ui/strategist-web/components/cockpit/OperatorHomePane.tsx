"use client";

import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import type { OperatorHomeSummary } from "@/lib/operator/operator-home-summary-model";
import type { OperatorModeId } from "@/lib/operator/operator-modes";
import { OperatorFlowStrip } from "./OperatorFlowStrip";

type Props = { summary: OperatorHomeSummary; onShowAdvanced: () => void; onOpenDetail: (mode: OperatorModeId) => void };
const v = (n: number | null) => (n == null ? "UNKNOWN" : String(n));

export function OperatorHomePane({ summary, onShowAdvanced, onOpenDetail }: Props) {
  const evidenceState = summary.replay_problem_count > 0 ? "DEGRADED" : summary.replay_verified_count > 0 ? "INSPECTABLE" : "UNKNOWN";
  const providerState =
    summary.provider_pending_key_count > 0
      ? "PENDING_KEY"
      : summary.provider_ok_count > 0
        ? "OK"
        : summary.stale_data_count > 0
          ? "STALE"
          : "UNKNOWN";

  return (
    <section className="cockpit-home" data-testid="cockpit-operator-home">
      <Pane title="Operator Home" dense badge={<StatusBadge raw={summary.overall_status} />}>
        <header className="cockpit-home__hero">
          <div>
            <h2>Operator Home</h2>
            <p>Calm triage for current read-plane status, attention items, review paths, and safety boundaries.</p>
          </div>
          <span className="cockpit-safety-chip" data-testid="cockpit-home-safety">
            Paper/research only · No live trading · No broker orders · No production deployment approval · No operator signoff · No profitability claim · Missing data remains UNKNOWN or NO_PAPER_DATA
          </span>
        </header>
        <p className="cockpit-home__intro">
          Missing data remains UNKNOWN or NO_PAPER_DATA. Evidence/replay verifies artifact integrity, not strategy quality.
        </p>
        <OperatorFlowStrip onOpenDetail={onOpenDetail} />
        <div className="cockpit-home__cards" aria-label="Operator status summary">
          <article className="cockpit-home__card cockpit-home__card--primary">
            <span>Overall status</span>
            <strong><StatusBadge raw={summary.overall_status} /></strong>
            <em>{summary.next_action_reason}</em>
          </article>
          <article className="cockpit-home__card">
            <span>Needs attention</span>
            <strong>{summary.blocked_count + summary.warning_count}</strong>
            <em>Blocked {summary.blocked_count} · review {summary.warning_count}</em>
          </article>
          <article className="cockpit-home__card">
            <span>Candidates / strategies</span>
            <strong>{v(summary.active_candidate_count)} / {v(summary.strategy_count)}</strong>
            <em>Review candidates before judging quality</em>
          </article>
          <article className="cockpit-home__card">
            <span>Paper data</span>
            <strong>{summary.paper_unknown_count > 0 ? "NO_PAPER_DATA" : `${summary.paper_win_count}W / ${summary.paper_loss_count}L`}</strong>
            <em>Missing paper data is not success</em>
          </article>
          <article className="cockpit-home__card">
            <span>Evidence / replay</span>
            <strong>{evidenceState}</strong>
            <em>{summary.replay_problem_count} replay issues</em>
          </article>
          <article className="cockpit-home__card">
            <span>Provider / data</span>
            <strong>{providerState}</strong>
            <em>OK {summary.provider_ok_count} · pending key {summary.provider_pending_key_count}</em>
          </article>
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
        <details className="cockpit-home__scoreboard">
          <summary>Show strategy scoreboard detail</summary>
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
        </details>
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
