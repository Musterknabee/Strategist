"use client";

import { useCallback, useMemo, useState, type MouseEvent } from "react";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { StatusBadge } from "@/components/operator/StatusBadge";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import type { OperatorModeId } from "@/lib/operator/operator-modes";
import { buildCandidateWorkbenchModel, type CandidateWorkbenchRow } from "@/lib/operator/candidate-workbench-model";

type Props = {
  strategyMemoryLatest: unknown;
  strategyGraveyardLatest: unknown;
  backtestForensicsLatest: unknown;
  paperTrackingLatest: unknown;
  providerSetup: unknown;
  providerHealth: unknown;
  evidenceChain: unknown;
  openInspector: (payload: InspectorPayload) => void;
  onOpenMode: (mode: OperatorModeId) => void;
};

type Filter =
  | "ALL"
  | "BLOCKED"
  | "NEEDS_REVIEW"
  | "NO_DATA"
  | "PAPER_WINS"
  | "PAPER_LOSSES"
  | "DUPLICATE_OR_GRAVEYARD"
  | "EVIDENCE_DEGRADED";

const FILTERS: { value: Filter; label: string; aria: string }[] = [
  { value: "ALL", label: "All", aria: "Show all candidates" },
  { value: "BLOCKED", label: "Blocked", aria: "Show blocked candidates" },
  { value: "NEEDS_REVIEW", label: "Needs review", aria: "Show candidates needing review" },
  { value: "NO_DATA", label: "No paper data", aria: "Show candidates with no paper data" },
  { value: "PAPER_WINS", label: "Paper wins", aria: "Show paper wins candidates" },
  { value: "PAPER_LOSSES", label: "Paper losses", aria: "Show paper losses candidates" },
  { value: "DUPLICATE_OR_GRAVEYARD", label: "Duplicate/graveyard", aria: "Show duplicate or graveyard warnings" },
  { value: "EVIDENCE_DEGRADED", label: "Evidence degraded", aria: "Show candidates with degraded evidence or replay" },
];

export function CandidateWorkbenchPane({
  strategyMemoryLatest,
  strategyGraveyardLatest,
  backtestForensicsLatest,
  paperTrackingLatest,
  providerSetup,
  providerHealth,
  evidenceChain,
  openInspector,
  onOpenMode,
}: Props) {
  const [filter, setFilter] = useState<Filter>("ALL");
  const model = useMemo(
    () =>
      buildCandidateWorkbenchModel({
        strategyMemoryLatest,
        strategyGraveyardLatest,
        backtestForensicsLatest,
        paperTrackingLatest,
        providerSetup,
        providerHealth,
        evidenceChain,
      }),
    [
      strategyMemoryLatest,
      strategyGraveyardLatest,
      backtestForensicsLatest,
      paperTrackingLatest,
      providerSetup,
      providerHealth,
      evidenceChain,
    ],
  );

  const rows = useMemo(() => {
    return model.rows.filter((row) => {
      if (filter === "ALL") return true;
      if (filter === "NEEDS_REVIEW") return row.lifecycle_state === "NEEDS_REVIEW";
      if (filter === "PAPER_WINS") return row.paper_result === "PAPER_WIN";
      if (filter === "PAPER_LOSSES") return row.paper_result === "PAPER_LOSS";
      if (filter === "NO_DATA") return row.paper_result === "NO_PAPER_DATA" || row.paper_result === "UNKNOWN";
      if (filter === "BLOCKED") return row.lifecycle_state === "BLOCKED" || row.lifecycle_state === "GRAVEYARDED";
      if (filter === "DUPLICATE_OR_GRAVEYARD") return row.duplicate_status !== "NO_WARNING" || row.graveyard_status !== "NO_MATCH";
      if (filter === "EVIDENCE_DEGRADED") return row.evidence_status !== "VERIFIED" || row.replay_status !== "VERIFIED";
      return true;
    });
  }, [filter, model.rows]);

  const inspectRow = useCallback((row: CandidateWorkbenchRow) => {
    openInspector({
      title: `${row.strategy_id} · candidate detail`,
      subtitle: `${row.lifecycle_state} · ${row.paper_result}`,
      rawJson: row,
    });
  }, [openInspector]);

  const columns = useMemo<DenseColumn<CandidateWorkbenchRow>[]>(
    () => [
      {
        key: "candidate",
        header: "Candidate / Strategy",
        width: "180px",
        cell: (row) => (
          <span className="candidate-primary">
            <strong>{row.strategy_id}</strong>
            <span>{row.candidate_id}</span>
          </span>
        ),
      },
      { key: "state", header: "State", width: "118px", cell: (row) => <StatusBadge raw={row.lifecycle_state} /> },
      { key: "paper", header: "Paper Result", width: "118px", cell: (row) => <StatusBadge raw={row.paper_result} /> },
      { key: "evidence", header: "Evidence", width: "118px", cell: (row) => <StatusBadge raw={row.evidence_status} /> },
      { key: "replay", header: "Replay", width: "118px", cell: (row) => <StatusBadge raw={row.replay_status} /> },
      { key: "provider", header: "Provider/Data", width: "118px", cell: (row) => <StatusBadge raw={row.provider_status} /> },
      {
        key: "warnings",
        header: "Warnings",
        width: "165px",
        cell: (row) => (
          <span className="candidate-warning-stack">
            <span>{row.duplicate_status}</span>
            <span>{row.graveyard_status}</span>
          </span>
        ),
      },
      { key: "next", header: "Next Safe Review", width: "142px", cell: (row) => <StatusBadge raw={row.next_action} /> },
      {
        key: "detail",
        header: "Inspect",
        width: "90px",
        cell: (row) => (
          <button
            type="button"
            className="linkish candidate-inspect-link"
            aria-label={`Inspect candidate ${row.strategy_id} details`}
            onClick={(event: MouseEvent<HTMLButtonElement>) => {
              event.stopPropagation();
              inspectRow(row);
            }}
          >
            Inspect
          </button>
        ),
      },
    ],
    [inspectRow],
  );

  const paneBadge =
    model.candidate_count === 0
      ? "UNKNOWN"
      : model.blocked_count > 0
        ? "BLOCKED"
        : model.needs_review_count > 0
          ? "NEEDS_REVIEW"
          : model.evidence_problem_count > 0 || model.replay_problem_count > 0
            ? "DEGRADED"
            : "OK";

  return (
    <div className="cockpit-candidate-workbench-row" data-testid="cockpit-candidate-workbench">
      <Pane
        title="Candidate Workbench"
        dense
        badge={<StatusBadge raw={paneBadge} />}
        onInspect={() =>
          openInspector({
            title: "Candidate Workbench · read-plane consolidation",
            subtitle: model.next_action,
            rawJson: {
              strategy_memory_latest: strategyMemoryLatest ?? {},
              strategy_graveyard_latest: strategyGraveyardLatest ?? {},
              backtest_forensics_latest: backtestForensicsLatest ?? {},
              paper_tracking_latest: paperTrackingLatest ?? {},
              provider_setup: providerSetup ?? {},
              provider_health: providerHealth ?? {},
              evidence_chain: evidenceChain ?? {},
              normalized: model,
            },
          })
        }
      >
        <p className="term-page__banner" data-testid="candidate-workbench-safety">
          Paper/research only. No live trading, no broker orders, no production deployment approval, no operator signoff, and no
          profitability claim. Missing paper data stays NO_PAPER_DATA; evidence/replay verifies integrity, not strategy quality.
        </p>
        <div className="candidate-summary-grid" data-testid="candidate-workbench-summary-cards">
          <article className="candidate-summary-card">
            <span>Candidates</span>
            <strong>{model.candidate_count}</strong>
            <em>Total review rows</em>
          </article>
          <article className="candidate-summary-card candidate-summary-card--attention">
            <span>Blocked</span>
            <strong>{model.blocked_count}</strong>
            <em>Inspect before review</em>
          </article>
          <article className="candidate-summary-card">
            <span>Needs review</span>
            <strong>{model.needs_review_count}</strong>
            <em>Requires operator inspection</em>
          </article>
          <article className="candidate-summary-card">
            <span>No paper data</span>
            <strong>{model.no_paper_data_count}</strong>
            <em>Not a win or loss</em>
          </article>
          <article className="candidate-summary-card">
            <span>Evidence/replay degraded</span>
            <strong>{model.evidence_problem_count + model.replay_problem_count}</strong>
            <em>Integrity issue to inspect</em>
          </article>
          <article className="candidate-summary-card">
            <span>Provider pending key</span>
            <strong>{model.provider_pending_key_count}</strong>
            <em>Action-required, not OK</em>
          </article>
        </div>
        <div className="candidate-next-action" data-testid="candidate-workbench-next-action">
          <StatusBadge raw={model.next_action} />
          <span>{model.next_action_reason}</span>
        </div>
        <details className="candidate-raw-summary">
          <summary>Show raw summary values</summary>
          <TermKV
            rows={[
              { k: "paper_wins", v: String(model.paper_win_count) },
              { k: "paper_losses", v: String(model.paper_loss_count) },
              { k: "duplicate_graveyard_warnings", v: String(model.duplicate_warning_count + model.graveyard_warning_count) },
              { k: "evidence_replay_problems", v: `${model.evidence_problem_count}/${model.replay_problem_count}` },
              { k: "next_action", v: <StatusBadge raw={model.next_action} /> },
              { k: "next_action_reason", v: model.next_action_reason },
            ]}
          />
        </details>
        {model.candidate_count === 0 ? <p className="cockpit-candidate-workbench__empty" data-testid="candidate-workbench-empty">UNKNOWN · no candidates are present in strategy memory. This is not an OK state; run or inspect paper/research artifacts before reviewing strategy quality.</p> : null}
        {model.evidence_problem_count > 0 || model.replay_problem_count > 0 ? <p className="cockpit-candidate-workbench__degraded" data-testid="candidate-workbench-evidence-degraded">DEGRADED · evidence or replay is incomplete. Open Evidence / Audit before treating candidate data as reviewable.</p> : null}
        <div className="term-filter-row candidate-filter-row" aria-label="Candidate filters">
          {FILTERS.map((item) => (
            <button
              key={item.value}
              type="button"
              className={filter === item.value ? "is-on" : ""}
              aria-pressed={filter === item.value}
              aria-label={item.aria}
              onClick={() => setFilter(item.value)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <DenseTable
          columns={columns}
          rows={rows}
          rowKey={(row) => row.row_id}
          onRowClick={inspectRow}
          empty={
            model.candidate_count === 0
              ? "UNKNOWN · no candidates returned. Paper/research data is absent, not successful."
              : "No rows match the selected filter."
          }
        />
        <div className="cockpit-candidate-workbench__actions" data-testid="candidate-workbench-links">
          <button type="button" className="term-btn term-btn--sm" onClick={() => onOpenMode("RESEARCH_REVIEW")}>
            Research Review
          </button>
          <button type="button" className="term-btn term-btn--sm" onClick={() => onOpenMode("FORENSIC_AUDIT")}>
            Forensic Audit
          </button>
          <button type="button" className="term-btn term-btn--sm" onClick={() => onOpenMode("FIRST_RUN")}>
            Provider Setup / First Run
          </button>
          <button type="button" className="term-btn term-btn--sm" onClick={() => onOpenMode("CAPITAL_FIREWALL")}>
            Capital Firewall
          </button>
        </div>
      </Pane>
    </div>
  );
}
