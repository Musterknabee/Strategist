"use client";

import { useMemo } from "react";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { StatusBadge } from "@/components/operator/StatusBadge";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import {
  buildResearchBatchForensicsModel,
  type ResearchForensicsRow,
} from "@/lib/operator/research-batch-forensics-model";

type ResearchBatchForensicsPaneProps = {
  strategyBatchLatest: unknown;
  strategyBatchesList: unknown;
  backtestForensicsLatest: unknown;
  paperTrackingLatest: unknown;
  strategyGraveyardLatest: unknown;
  strategyMemoryLatest: unknown;
  strategyThesisLatest: unknown;
  shadowBookLatest: unknown;
  openInspector: (payload: InspectorPayload) => void;
};

const columns: DenseColumn<ResearchForensicsRow>[] = [
  { key: "section", header: "Section", width: "160px", cell: (row) => row.section },
  { key: "id", header: "Run/Tracking", width: "140px", cell: (row) => row.run_or_tracking_id },
  { key: "status", header: "Status", width: "120px", cell: (row) => <StatusBadge raw={row.status} /> },
  { key: "review", header: "Review", width: "140px", cell: (row) => <StatusBadge raw={row.review_status} /> },
  { key: "counts", header: "Blockers/Warnings", width: "160px", cell: (row) => `${row.blocker_count}/${row.warning_count}` },
  { key: "digest", header: "Digest", width: "130px", cell: (row) => row.digest_prefix },
  { key: "time", header: "Generated", cell: (row) => row.generated_at_utc },
];

function paneBadge(model: ReturnType<typeof buildResearchBatchForensicsModel>): string {
  if (model.totals.degraded_count > 0) return "DEGRADED";
  if (model.totals.requires_review_count > 0) return "REQUIRES_REVIEW";
  if (model.totals.pending_count > 0) return "PENDING";
  return "OK";
}

export function ResearchBatchForensicsPane({
  strategyBatchLatest,
  strategyBatchesList,
  backtestForensicsLatest,
  paperTrackingLatest,
  strategyGraveyardLatest,
  strategyMemoryLatest,
  strategyThesisLatest,
  shadowBookLatest,
  openInspector,
}: ResearchBatchForensicsPaneProps) {
  const model = useMemo(
    () =>
      buildResearchBatchForensicsModel({
        strategyBatchLatest,
        strategyBatchesList,
        backtestForensicsLatest,
        paperTrackingLatest,
        strategyGraveyardLatest,
        strategyMemoryLatest,
        strategyThesisLatest,
        shadowBookLatest,
      }),
    [
      strategyBatchLatest,
      strategyBatchesList,
      backtestForensicsLatest,
      paperTrackingLatest,
      strategyGraveyardLatest,
      strategyMemoryLatest,
      strategyThesisLatest,
      shadowBookLatest,
    ],
  );

  const next = model.review_next;

  return (
    <div className="cockpit-research-batch-row" data-testid="cockpit-research-batch-forensics">
      <Pane
        title="Research / batch forensics"
        dense
        badge={<StatusBadge raw={paneBadge(model)} />}
        onInspect={() =>
          openInspector({
            title: "Research / batch forensics",
            subtitle: "Read-plane strategy evidence rollup",
            rawJson: {
              strategy_batch_latest: strategyBatchLatest ?? {},
              strategy_batches: strategyBatchesList ?? {},
              backtest_forensics_latest: backtestForensicsLatest ?? {},
              paper_tracking_latest: paperTrackingLatest ?? {},
              strategy_graveyard_latest: strategyGraveyardLatest ?? {},
              strategy_memory_latest: strategyMemoryLatest ?? {},
              strategy_thesis_latest: strategyThesisLatest ?? {},
              shadow_book_latest: shadowBookLatest ?? {},
            },
          })
        }
      >
        <TermKV
          rows={[
            { k: "requires_review_count", v: String(model.totals.requires_review_count) },
            { k: "degraded_count", v: String(model.totals.degraded_count) },
            { k: "pending_count", v: String(model.totals.pending_count) },
            { k: "review_next_section", v: next?.section ?? "PENDING" },
            { k: "review_next_target", v: next?.review_target ?? "PENDING" },
          ]}
        />
        <DenseTable
          columns={columns}
          rows={model.rows}
          rowKey={(row) => row.__id}
          onRowClick={(row) =>
            openInspector({
              title: `${row.section} · ${row.run_or_tracking_id}`,
              subtitle: row.review_target,
              rawJson: row.raw,
            })
          }
          empty="UNKNOWN · research/batch evidence unavailable"
        />
      </Pane>
    </div>
  );
}
