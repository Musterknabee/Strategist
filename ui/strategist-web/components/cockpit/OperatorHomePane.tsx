"use client";

import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import type { OperatorHomeSummary } from "@/lib/operator/operator-home-summary-model";
import {
  getOperatorModeDefinition,
  type OperatorModeId,
} from "@/lib/operator/operator-modes";
import { OperatorFlowStrip } from "./OperatorFlowStrip";

export type OperatorReadPlaneStatus = {
  label: string;
  tone: "OK" | "NEEDS_REVIEW" | "DEGRADED" | "UNKNOWN";
  api: string;
  readiness: string;
  facade: string;
  hint: string;
};

type Props = {
  summary: OperatorHomeSummary;
  readPlaneStatus: OperatorReadPlaneStatus;
  onShowAdvanced: () => void;
  onOpenDetail: (mode: OperatorModeId) => void;
};

const v = (n: number | null, empty = "No data yet") => (n == null ? empty : String(n));
const primaryModes: OperatorModeId[] = ["DAILY_OPS", "RESEARCH_REVIEW", "CAPITAL_FIREWALL", "FORENSIC_AUDIT", "RELEASE_CONTROL", "FIRST_RUN"];
type GuidedStep = { id: string; label: string; status: string; detail: string; mode: OperatorModeId };

function guidedSteps(
  summary: OperatorHomeSummary,
  readPlaneStatus: OperatorReadPlaneStatus,
  evidenceState: string,
  providerState: string,
): GuidedStep[] {
  const backendOk = readPlaneStatus.tone === "OK";
  const readinessOk = readPlaneStatus.readiness === "READY";
  const providerOk = providerState === "OK";
  const hasCandidateData = summary.active_candidate_count != null;
  const evidenceOk = evidenceState === "INSPECTABLE" && summary.replay_problem_count === 0;
  const paperReady = summary.paper_unknown_count === 0;
  const releaseClear = summary.blocked_count === 0 && summary.warning_count === 0 && evidenceOk;
  return [
    {
      id: "connect",
      label: "Connect read-plane",
      status: backendOk ? "OK" : "CHECK",
      detail: backendOk ? "API and facade are reachable." : readPlaneStatus.hint,
      mode: "FIRST_RUN",
    },
    {
      id: "setup",
      label: "Confirm readiness and providers",
      status: readinessOk && providerOk ? "OK" : "REVIEW",
      detail: readinessOk && providerOk ? "Readiness and provider posture look usable." : "Open setup before trusting downstream evidence.",
      mode: "FIRST_RUN",
    },
    {
      id: "research",
      label: "Review candidate research",
      status: hasCandidateData ? "OK" : "PENDING",
      detail: hasCandidateData ? "Candidate/workboard data is present." : "Run or import strategy batch data before ranking candidates.",
      mode: "RESEARCH_REVIEW",
    },
    {
      id: "evidence",
      label: "Inspect evidence chain",
      status: evidenceOk ? "OK" : "CHECK",
      detail: evidenceOk ? "Replay evidence is inspectable with no reported replay issue." : "Open evidence/replay to distinguish missing artifacts from integrity issues.",
      mode: "FORENSIC_AUDIT",
    },
    {
      id: "paper",
      label: "Check paper-only firewall",
      status: paperReady ? "OK" : "PENDING",
      detail: paperReady ? "Paper result data exists; still research-only." : "No paper result yet; capital and broker actions remain blocked.",
      mode: "CAPITAL_FIREWALL",
    },
    {
      id: "release",
      label: "Prepare release evidence",
      status: releaseClear ? "READY_TO_REVIEW" : "NOT_READY",
      detail: releaseClear ? "Evidence can be reviewed; this is not deployment approval." : "Resolve blockers, missing paper data, or evidence gaps first.",
      mode: "RELEASE_CONTROL",
    },
  ];
}

export function OperatorHomePane({ summary, readPlaneStatus, onShowAdvanced, onOpenDetail }: Props) {
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
        <div className="cockpit-read-plane-status" data-testid="cockpit-read-plane-status">
          <div className="cockpit-read-plane-status__main">
            <span>Backend / read-plane</span>
            <strong><StatusBadge raw={readPlaneStatus.tone} /> {readPlaneStatus.label}</strong>
            <em>{readPlaneStatus.hint}</em>
          </div>
          <div className="cockpit-read-plane-status__facts" aria-label="Read-plane connection facts">
            <div><span>API</span><strong>{readPlaneStatus.api}</strong></div>
            <div><span>Readiness</span><strong>{readPlaneStatus.readiness}</strong></div>
            <div><span>Facade</span><strong>{readPlaneStatus.facade}</strong></div>
          </div>
        </div>
        <div className="cockpit-guided-flow" data-testid="cockpit-guided-flow">
          <div className="cockpit-guided-flow__head">
            <span>Start here</span>
            <strong>Operator path</strong>
            <em>Move left to right; each step opens the relevant cockpit surface.</em>
          </div>
          <div className="cockpit-guided-flow__steps" aria-label="Guided operator path">
            {guidedSteps(summary, readPlaneStatus, evidenceState, providerState).map((step, index) => (
              <button
                key={step.id}
                type="button"
                className="cockpit-guided-step"
                onClick={() => onOpenDetail(step.mode)}
                data-testid={`cockpit-guided-${step.id}`}
              >
                <span>{String(index + 1).padStart(2, "0")} · {step.label}</span>
                <strong><StatusBadge raw={step.status} /></strong>
                <em>{step.detail}</em>
              </button>
            ))}
          </div>
        </div>
        <p className="cockpit-home__intro">
          Missing data remains UNKNOWN or NO_PAPER_DATA. Evidence/replay verifies artifact integrity, not strategy quality.
        </p>
        <div className="cockpit-ease-layer" data-testid="cockpit-ease-layer" aria-label="Operator ease layer">
          <div className="cockpit-ease-layer__primary">
            <span>Primary action</span>
            <strong><StatusBadge raw={summary.next_action} /> {summary.next_action_reason}</strong>
            <em>{summary.generated_at_utc}</em>
          </div>
          <div className="cockpit-ease-layer__modes" aria-label="Operating surfaces">
            {primaryModes.map((mode) => {
              const definition = getOperatorModeDefinition(mode);
              return (
                <button
                  key={mode}
                  type="button"
                  className="cockpit-ease-mode"
                  onClick={() => onOpenDetail(mode)}
                >
                  <span>{definition.label}</span>
                  <strong>{definition.primary_panes[0]}</strong>
                  <em>{definition.safety === "COMMAND_CAPABLE" ? "Token-gated commands" : "Read-plane only"}</em>
                </button>
              );
            })}
          </div>
          <div className="cockpit-ease-layer__facts" aria-label="Useful operating facts">
            <div><span>Attention</span><strong>{summary.blocked_count} blocked · {summary.warning_count} review</strong></div>
            <div><span>Strategies</span><strong>{v(summary.active_candidate_count)} active · {summary.graveyarded_count} graveyarded</strong></div>
            <div><span>Evidence</span><strong>{evidenceState} · {summary.replay_problem_count} replay issues</strong></div>
            <div><span>Providers</span><strong>{providerState} · {summary.stale_data_count} stale</strong></div>
          </div>
        </div>
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
            <em>{summary.strategy_count == null ? "No workboard strategy count returned yet" : "Review candidates before judging quality"}</em>
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
              {summary.top_attention_items.length > 0 ? summary.top_attention_items.map((item) => <li key={item}>{item}</li>) : <li>No urgent blockers from current read-plane payloads. If this is a new workspace, start with Provider Setup / First Run, then run a strategy batch before judging candidates.</li>}
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
