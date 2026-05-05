"use client";

import { useMemo } from "react";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { StatusBadge } from "@/components/operator/StatusBadge";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import { buildPromotionDossierModel, type DossierEvidenceItem, type DossierGateRow, type PromotionDossierModel } from "@/lib/operator/promotion-dossier-model";
import { inspectBody } from "./cockpit-utils";

export type PromotionEvidenceDossierPaneProps = {
  readyzBody: Record<string, unknown> | null;
  strategyIntakeLatest: unknown;
  strategyThesisLatest: unknown;
  strategyThesisGenerationLatest: unknown;
  paperTrackingLatest: unknown;
  strategyBatchLatest: unknown;
  backtestForensicsLatest: unknown;
  evidenceChain: unknown;
  operatorActions: unknown;
  workboard: unknown;
  evidence: unknown;
  paperExecution: unknown;
  queryFailed: boolean;
  openInspector: (payload: InspectorPayload) => void;
  setLastDigest?: (digest: string) => void;
};

const gateColumns: DenseColumn<DossierGateRow>[] = [
  { key: "n", header: "Gate", width: "180px", cell: (r) => r.gate_name },
  { key: "st", header: "Status", width: "88px", cell: (r) => <StatusBadge raw={r.status} /> },
  { key: "cat", header: "Category", width: "120px", cell: (r) => r.category },
  { key: "sev", header: "Sev", width: "72px", cell: (r) => <StatusBadge raw={r.severity} /> },
  { key: "src", header: "Source", width: "160px", cell: (r) => r.source_evidence },
  { key: "reason", header: "Reason", cell: (r) => r.reason ?? "—" },
];

const evColumns: DenseColumn<DossierEvidenceItem>[] = [
  { key: "l", header: "Evidence", width: "200px", cell: (r) => r.label },
  { key: "d", header: "Digest prefix", width: "120px", cell: (r) => r.digest_prefix },
  { key: "src", header: "Endpoint", width: "200px", cell: (r) => r.source_endpoint },
  { key: "st", header: "State", width: "100px", cell: (r) => <StatusBadge raw={r.status} /> },
];

function paneBadge(m: PromotionDossierModel, queryFailed: boolean): string {
  if (queryFailed) return "DEGRADED";
  if (m.chain_status === "DEGRADED") return "DEGRADED";
  return m.current_state !== "UNKNOWN" ? "LINKED" : "PENDING";
}

export function PromotionEvidenceDossierPane({
  readyzBody,
  strategyIntakeLatest,
  strategyThesisLatest,
  strategyThesisGenerationLatest,
  paperTrackingLatest,
  strategyBatchLatest,
  backtestForensicsLatest,
  evidenceChain,
  operatorActions,
  workboard,
  evidence,
  paperExecution,
  queryFailed,
  openInspector,
  setLastDigest,
}: PromotionEvidenceDossierPaneProps) {
  const model = useMemo(
    () =>
      buildPromotionDossierModel({
        readyzBody,
        strategyIntakeLatest,
        strategyThesisLatest,
        strategyThesisGenerationLatest,
        paperTrackingLatest,
        strategyBatchLatest,
        backtestForensicsLatest,
        evidenceChain,
        operatorActions,
        workboard,
        evidence,
        paperExecution,
        queryFailed,
      }),
    [
      backtestForensicsLatest,
      evidence,
      evidenceChain,
      operatorActions,
      paperExecution,
      paperTrackingLatest,
      queryFailed,
      readyzBody,
      strategyBatchLatest,
      strategyIntakeLatest,
      strategyThesisGenerationLatest,
      strategyThesisLatest,
      workboard,
    ],
  );

  const badge = paneBadge(model, queryFailed);

  return (
    <div className="cockpit-promotion-dossier-row" data-testid="cockpit-promotion-dossier">
      <Pane
        title="Promotion evidence dossier"
        dense
        badge={<StatusBadge raw={badge} />}
        onInspect={() =>
          openInspector({
            title: "Promotion dossier · read-plane bundle",
            subtitle: model.dossier_id,
            body: inspectBody({
              status: model.chain_status,
              summary: model.recommended_review_action,
              warnings: model.degraded_flags,
              details: [
                { k: "current_state", v: model.current_state },
                { k: "previous_state", v: model.previous_state },
                { k: "ledger_event_hash", v: model.ledger_event_hash },
              ],
            }),
            rawJson: model.raw_sources,
            digestToCopy: model.ledger_event_hash !== "UNKNOWN" ? model.ledger_event_hash : undefined,
          })
        }
      >
        <div className="pane-footer" style={{ marginBottom: 6 }}>
          Decision summary
        </div>
        <TermKV
          rows={[
            { k: "dossier_id", v: model.dossier_id },
            { k: "strategy_id", v: model.strategy_id },
            { k: "experiment_id", v: model.experiment_id },
            { k: "run_id", v: model.run_id },
            { k: "tracking_id", v: model.tracking_id },
            { k: "current_state", v: <StatusBadge raw={model.current_state} /> },
            { k: "previous_state", v: <StatusBadge raw={model.previous_state} /> },
            { k: "event_type", v: <StatusBadge raw={model.latest_event_type} /> },
            { k: "decision_time_utc", v: model.decision_time_utc },
            { k: "recommended_action", v: <StatusBadge raw={model.recommended_review_action} /> },
            { k: "gate_pass_fail_unknown", v: `${model.gate_pass_count}/${model.gate_fail_count}/${model.gate_unknown_count}` },
            { k: "blockers_warnings", v: `${model.blocker_count}/${model.warning_count}` },
          ]}
        />

        <div className="pane-footer" style={{ margin: "10px 0 6px" }}>
          Gate results (forensics gate_matrix)
        </div>
        <DenseTable
          columns={gateColumns}
          rows={model.gate_rows}
          rowKey={(r) => r.gate_name}
          onRowClick={(row) =>
            openInspector({
              title: `Gate · ${row.gate_name}`,
              subtitle: row.source_evidence,
              body: inspectBody({
                status: row.status,
                summary: row.reason ?? row.gate_name,
                details: [
                  { k: "category", v: row.category },
                  { k: "severity", v: row.severity },
                ],
              }),
              rawJson: row,
            })
          }
          empty="UNKNOWN · no gate_matrix rows for anchored strategy"
        />

        <div className="pane-footer" style={{ margin: "10px 0 6px" }}>
          Benchmark / robustness / execution / market
        </div>
        <TermKV
          rows={[
            { k: "benchmark", v: model.benchmark_lines.join(" · ") },
            { k: "robustness", v: model.robustness_lines.join(" · ") },
            { k: "execution_realism", v: model.execution_realism_lines.join(" · ") },
            { k: "market_data", v: model.market_data_lines.join(" · ") },
          ]}
        />

        <div className="pane-footer" style={{ margin: "10px 0 6px" }}>
          Ledger chain proof
        </div>
        <TermKV
          rows={[
            { k: "chain_status", v: <StatusBadge raw={model.chain_status} /> },
            { k: "decision_ledger_chain_ok", v: String(model.decision_ledger_chain_ok ?? "UNKNOWN") },
            { k: "selected_event_chained", v: String(model.selected_ledger_chained ?? "UNKNOWN") },
            { k: "ledger_event_hash", v: model.ledger_event_hash },
            { k: "previous_event_hash", v: model.ledger_previous_event_hash },
            { k: "manifest_hash", v: model.manifest_hash },
            { k: "payload_digest_prefix", v: model.payload_digest_prefix },
            { k: "writer_identity", v: model.writer_identity },
            { k: "sequence_number", v: model.sequence_number },
            { k: "config_fingerprint", v: model.config_fingerprint },
          ]}
        />
        <ul className="cockpit-risk-blocker-ul" style={{ fontSize: 11, marginTop: 6 }}>
          {model.ledger_proof_lines.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>

        <div className="pane-footer" style={{ margin: "10px 0 6px" }}>
          Evidence items
        </div>
        <DenseTable
          columns={evColumns}
          rows={model.evidence_items}
          rowKey={(r) => r.label}
          onRowClick={(row) => {
            const full = model.ledger_event_hash;
            if (row.label.includes("ledger event") && full && full !== "UNKNOWN") setLastDigest?.(full);
            openInspector({
              title: row.label,
              subtitle: row.source_endpoint,
              body: inspectBody({
                status: row.status,
                summary: row.digest_prefix,
                details: [{ k: "digest_prefix", v: row.digest_prefix }],
              }),
              rawJson: row,
            });
          }}
          empty="UNKNOWN · no digest-linked evidence rows"
        />

        <div className="pane-footer" style={{ margin: "10px 0 6px" }}>
          Operator review / related context
        </div>
        <ul className="cockpit-risk-blocker-ul" style={{ fontSize: 11 }}>
          {model.operator_review_lines.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </Pane>
    </div>
  );
}
