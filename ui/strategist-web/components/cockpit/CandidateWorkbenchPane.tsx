"use client";

import { useMemo, useState } from "react";
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

type Filter = "ALL" | "NEEDS_REVIEW" | "PAPER_WINS" | "PAPER_LOSSES" | "NO_DATA" | "BLOCKED" | "DUPLICATE" | "GRAVEYARDED";

const columns: DenseColumn<CandidateWorkbenchRow>[] = [
  { key: "candidate", header: "Candidate / Strategy", width: "180px", cell: (row) => `${row.candidate_id} · ${row.strategy_id}` },
  { key: "paper", header: "Paper Result", width: "120px", cell: (row) => <StatusBadge raw={row.paper_result} /> },
  { key: "evidence", header: "Evidence", width: "120px", cell: (row) => <StatusBadge raw={row.evidence_status} /> },
  { key: "replay", header: "Replay", width: "120px", cell: (row) => <StatusBadge raw={row.replay_status} /> },
  { key: "provider", header: "Provider/Data", width: "120px", cell: (row) => <StatusBadge raw={row.provider_status} /> },
  {
    key: "dup-grave",
    header: "Duplicate/Graveyard",
    width: "150px",
    cell: (row) => `${row.duplicate_status} · ${row.graveyard_status}`,
  },
  { key: "next", header: "Next Action", width: "150px", cell: (row) => <StatusBadge raw={row.next_action} /> },
  { key: "detail", header: "Details", cell: (row) => row.detail_targets.join(", ") },
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
      if (filter === "DUPLICATE") return row.duplicate_status !== "NO_WARNING";
      if (filter === "GRAVEYARDED") return row.graveyard_status !== "NO_MATCH";
      return true;
    });
  }, [filter, model.rows]);

  const paneBadge = model.blocked_count > 0 ? "BLOCKED" : model.needs_review_count > 0 ? "NEEDS_REVIEW" : "OK";

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
        <p className="term-page__banner">Paper/research only — no live trading, no promotion approval.</p>
        <TermKV
          rows={[
            { k: "candidates", v: String(model.candidate_count) },
            { k: "paper_wins", v: String(model.paper_win_count) },
            { k: "paper_losses", v: String(model.paper_loss_count) },
            { k: "no_paper_data", v: String(model.no_paper_data_count) },
            { k: "blocked", v: String(model.blocked_count) },
            { k: "duplicate_graveyard_warnings", v: String(model.duplicate_warning_count + model.graveyard_warning_count) },
            { k: "next_action", v: <StatusBadge raw={model.next_action} /> },
            { k: "next_action_reason", v: model.next_action_reason },
          ]}
        />
        <div className="term-filter-row">
          {(["ALL", "NEEDS_REVIEW", "PAPER_WINS", "PAPER_LOSSES", "NO_DATA", "BLOCKED", "DUPLICATE", "GRAVEYARDED"] as Filter[]).map(
            (value) => (
              <button key={value} type="button" className={filter === value ? "is-on" : ""} onClick={() => setFilter(value)}>
                {value}
              </button>
            ),
          )}
        </div>
        <DenseTable
          columns={columns}
          rows={rows}
          rowKey={(row) => row.row_id}
          onRowClick={(row) =>
            openInspector({
              title: `${row.strategy_id} · candidate detail`,
              subtitle: `${row.lifecycle_state} · ${row.paper_result}`,
              rawJson: row,
            })
          }
          empty={
            model.candidate_count === 0
              ? "No candidates yet. Run paper/research workflows and inspect evidence artifacts."
              : "No rows match the selected filter."
          }
        />
        <div style={{ display: "flex", gap: "6px", marginTop: "6px" }}>
          <button type="button" className="term-btn term-btn--sm" onClick={() => onOpenMode("RESEARCH_REVIEW")}>
            Strategy Lifecycle
          </button>
          <button type="button" className="term-btn term-btn--sm" onClick={() => onOpenMode("FORENSIC_AUDIT")}>
            Evidence / Audit
          </button>
          <button type="button" className="term-btn term-btn--sm" onClick={() => onOpenMode("FIRST_RUN")}>
            Provider Setup
          </button>
          <button type="button" className="term-btn term-btn--sm" onClick={() => onOpenMode("CAPITAL_FIREWALL")}>
            Capital Firewall
          </button>
        </div>
      </Pane>
    </div>
  );
}
