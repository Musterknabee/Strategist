"use client";

import { useMemo } from "react";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { StatusBadge } from "@/components/operator/StatusBadge";
import type { UiMutationSafetyStatus } from "@/lib/api/types";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import {
  buildStrategyLifecycleModel,
  type StrategyLifecycleRow,
} from "@/lib/operator/strategy-lifecycle-model";
import { StrategyLifecycleIntakeForm } from "./StrategyLifecycleIntakeForm";

export type StrategyLifecyclePaneProps = {
  strategyIntakeLatest: unknown;
  strategyThesisLatest: unknown;
  strategyThesisGenerationLatest: unknown;
  strategyMemoryLatest: unknown;
  strategyGraveyardLatest: unknown;
  paperTrackingLatest: unknown;
  backtestForensicsLatest: unknown;
  strategyBatchLatest: unknown;
  workboard: unknown;
  evidenceChain: unknown;
  mutationSafety: UiMutationSafetyStatus | null;
  queryFailed: boolean;
  openInspector: (payload: InspectorPayload) => void;
  setLastDigest?: (digest: string) => void;
};

const columns: DenseColumn<StrategyLifecycleRow>[] = [
  { key: "section", header: "Section", width: "150px", cell: (row) => row.section },
  { key: "id", header: "Id", width: "120px", cell: (row) => row.run_or_tracking_id },
  {
    key: "stage",
    header: "Stage",
    width: "130px",
    cell: (row) => <StatusBadge raw={row.stage} />,
  },
  { key: "status", header: "Status", width: "120px", cell: (row) => <StatusBadge raw={row.status} /> },
  {
    key: "review",
    header: "Review",
    width: "120px",
    cell: (row) => <StatusBadge raw={row.review_status} />,
  },
  {
    key: "counts",
    header: "Blockers/Warnings",
    width: "130px",
    cell: (row) => `${row.blocker_count}/${row.warning_count}`,
  },
  { key: "digest", header: "Digest", width: "120px", cell: (row) => row.digest_prefix },
  { key: "time", header: "Generated", cell: (row) => row.generated_at_utc },
];

function paneBadge(model: ReturnType<typeof buildStrategyLifecycleModel>, queryFailed: boolean): string {
  if (queryFailed) return "DEGRADED";
  if (model.current_stage === "GRAVEYARDED") return "GRAVEYARDED";
  if (model.current_stage === "DEGRADED") return "DEGRADED";
  if (model.trust_or_freshness === "STALE_OR_CHAIN_ISSUE") return "DEGRADED";
  if (model.next_review_action !== "NO_IMMEDIATE_ACTION") return "ACTION";
  return "OK";
}

export function StrategyLifecyclePane({
  strategyIntakeLatest,
  strategyThesisLatest,
  strategyThesisGenerationLatest,
  strategyMemoryLatest,
  strategyGraveyardLatest,
  paperTrackingLatest,
  backtestForensicsLatest,
  strategyBatchLatest,
  workboard,
  evidenceChain,
  mutationSafety,
  queryFailed,
  openInspector,
  setLastDigest,
}: StrategyLifecyclePaneProps) {
  const model = useMemo(
    () =>
      buildStrategyLifecycleModel({
        strategyIntakeLatest,
        strategyThesisLatest,
        strategyThesisGenerationLatest,
        strategyMemoryLatest,
        strategyGraveyardLatest,
        paperTrackingLatest,
        backtestForensicsLatest,
        strategyBatchLatest,
        workboard,
        evidenceChain,
      }),
    [
      strategyIntakeLatest,
      strategyThesisLatest,
      strategyThesisGenerationLatest,
      strategyMemoryLatest,
      strategyGraveyardLatest,
      paperTrackingLatest,
      backtestForensicsLatest,
      strategyBatchLatest,
      workboard,
      evidenceChain,
    ],
  );

  const badge = paneBadge(model, queryFailed);

  return (
    <div className="cockpit-strategy-lifecycle-row" data-testid="cockpit-strategy-lifecycle">
      <Pane
        title="Strategy lifecycle (intake → thesis → evidence)"
        dense
        badge={<StatusBadge raw={badge} />}
        onInspect={() =>
          openInspector({
            title: "Strategy lifecycle · read-plane bundle",
            subtitle: model.next_review_action,
            rawJson: {
              strategy_intake_latest: strategyIntakeLatest ?? {},
              strategy_thesis_latest: strategyThesisLatest ?? {},
              strategy_thesis_generation_latest: strategyThesisGenerationLatest ?? {},
              strategy_memory_latest: strategyMemoryLatest ?? {},
              strategy_graveyard_latest: strategyGraveyardLatest ?? {},
              paper_tracking_latest: paperTrackingLatest ?? {},
              backtest_forensics_latest: backtestForensicsLatest ?? {},
              strategy_batch_latest: strategyBatchLatest ?? {},
              normalized: model,
            },
          })
        }
      >
        <TermKV
          rows={[
            { k: "lifecycle_id", v: model.lifecycle_id },
            { k: "strategy_id", v: model.strategy_id },
            { k: "thesis_id", v: model.thesis_id },
            { k: "intake_id", v: model.intake_id },
            { k: "tracking_id", v: model.tracking_id },
            { k: "run_id", v: model.run_id },
            { k: "current_stage", v: <StatusBadge raw={model.current_stage} /> },
            { k: "trust_freshness", v: <StatusBadge raw={model.trust_or_freshness} /> },
            { k: "blockers_total", v: String(model.blocker_count) },
            { k: "warnings_total", v: String(model.warning_count) },
            { k: "digest_prefix", v: model.digest_prefix },
            { k: "next_review_action", v: <StatusBadge raw={model.next_review_action} /> },
          ]}
        />
        <DenseTable
          columns={columns}
          rows={model.rows}
          rowKey={(row) => row.__id}
          onRowClick={(row) => {
            if (row.digest_full) setLastDigest?.(row.digest_full);
            openInspector({
              title: `${row.section} · ${row.run_or_tracking_id}`,
              subtitle: row.review_target,
              rawJson: row.raw,
            });
          }}
          empty="UNKNOWN · lifecycle evidence unavailable"
        />
        <StrategyLifecycleIntakeForm mutationSafety={mutationSafety} />
      </Pane>
    </div>
  );
}
