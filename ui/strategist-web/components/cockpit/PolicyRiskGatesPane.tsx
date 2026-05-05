"use client";

import { useMemo, useState } from "react";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { StatusBadge } from "@/components/operator/StatusBadge";
import type { UiMutationSafetyStatus } from "@/lib/api/types";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import { asString } from "@/lib/operator/payload-utils";
import {
  buildPolicyRiskGatesModel,
  filterPolicyRiskGatesByCategory,
  type PolicyRiskGatesModel,
  type RiskGateCategory,
  type RiskGateEntry,
} from "@/lib/operator/policy-risk-gates-model";
import { inspectBody } from "./cockpit-utils";

export type PolicyRiskGatesPaneProps = {
  readyzBody: Record<string, unknown> | null;
  readyzError: boolean;
  runtimeBody: Record<string, unknown> | null;
  mutationSafety: UiMutationSafetyStatus | null;
  facade: Record<string, unknown> | null;
  evidence: Record<string, unknown> | null;
  operatorActions: Record<string, unknown> | null;
  providerHealth: Record<string, unknown> | null;
  backtestForensics: Record<string, unknown> | null;
  paperExecution: Record<string, unknown> | null;
  paperTracking: Record<string, unknown> | null;
  queryFailed: boolean;
  openInspector: (payload: InspectorPayload) => void;
  setLastDigest?: (digest: string) => void;
};

type CatFilter = "ALL" | RiskGateCategory;

const FILTERS: { id: CatFilter; label: string }[] = [
  { id: "ALL", label: "All" },
  { id: "Readiness", label: "Readiness" },
  { id: "Production Policy", label: "Policy" },
  { id: "Auth Safety", label: "Auth" },
  { id: "Ledger / Evidence", label: "Ledger" },
  { id: "Provider Freshness", label: "Providers" },
  { id: "Market Data Validity", label: "Market" },
  { id: "Execution Realism", label: "Exec realism" },
  { id: "Robustness / Overfit Control", label: "Robustness" },
  { id: "Benchmark Evidence", label: "Benchmark" },
  { id: "Paper / Live Safety", label: "Paper" },
];

function paneBadge(m: PolicyRiskGatesModel, queryFailed: boolean): string {
  if (queryFailed) return "DEGRADED";
  return m.posture;
}

const columns: DenseColumn<RiskGateEntry>[] = [
  { key: "cat", header: "Category", width: "130px", cell: (row) => row.category },
  { key: "label", header: "Gate", width: "200px", cell: (row) => row.label },
  { key: "st", header: "Status", width: "88px", cell: (row) => <StatusBadge raw={row.status} /> },
  { key: "sev", header: "Sev", width: "72px", cell: (row) => <StatusBadge raw={row.severity} /> },
  { key: "src", header: "Source", width: "160px", cell: (row) => row.source_endpoint },
  { key: "dig", header: "Digest", width: "100px", cell: (row) => row.evidence_digest_prefix ?? "—" },
  { key: "bw", header: "B/W", width: "52px", cell: (row) => `${row.blocker_count}/${row.warning_count}` },
];

export function PolicyRiskGatesPane({
  readyzBody,
  readyzError,
  runtimeBody,
  mutationSafety,
  facade,
  evidence,
  operatorActions,
  providerHealth,
  backtestForensics,
  paperExecution,
  paperTracking,
  queryFailed,
  openInspector,
  setLastDigest,
}: PolicyRiskGatesPaneProps) {
  const [cat, setCat] = useState<CatFilter>("ALL");
  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  const model = useMemo(
    () =>
      buildPolicyRiskGatesModel({
        readyzBody,
        readyzError,
        runtimeBody,
        mutationSafety,
        facade,
        evidence,
        operatorActions,
        providerHealth,
        backtestForensics,
        paperExecution,
        paperTracking,
        queryFailed,
      }),
    [
      backtestForensics,
      evidence,
      facade,
      mutationSafety,
      operatorActions,
      paperExecution,
      paperTracking,
      providerHealth,
      queryFailed,
      readyzBody,
      readyzError,
      runtimeBody,
    ],
  );

  const rows = useMemo(() => filterPolicyRiskGatesByCategory(model.gates, cat), [cat, model.gates]);
  const badge = paneBadge(model, queryFailed);

  return (
    <div className="cockpit-policy-risk-row" data-testid="cockpit-policy-risk-gates">
      <Pane
        title="Policy / risk gates"
        dense
        badge={<StatusBadge raw={badge} />}
        onInspect={() =>
          openInspector({
            title: "Policy / risk gates · read-plane bundle",
            subtitle: model.posture_reason,
            body: inspectBody({
              status: model.posture,
              summary: model.next_review_hint,
              warnings: model.blocker_lines.slice(0, 8),
              details: [
                { k: "freshness", v: model.freshness_summary },
                { k: "robustness", v: model.robustness_summary },
                { k: "exec_realism", v: model.execution_realism_summary },
                { k: "benchmark", v: model.benchmark_summary },
                { k: "paper", v: model.paper_safety_summary },
              ],
            }),
            rawJson: {
              posture: model.posture,
              counts: model.counts,
              gates: model.gates,
              blocker_lines: model.blocker_lines,
              warning_lines: model.warning_lines,
            },
          })
        }
      >
        <TermKV
          rows={[
            { k: "posture", v: <StatusBadge raw={model.posture} /> },
            { k: "reason", v: model.posture_reason },
            { k: "next_review", v: model.next_review_hint },
          ]}
        />
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", margin: "10px 0" }} data-testid="cockpit-risk-gate-filters" role="toolbar" aria-label="Risk gate categories">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              type="button"
              className={`term-chip ${cat === f.id ? "term-chip--active" : ""}`}
              data-testid={f.id === "ALL" ? "cockpit-risk-filter-all" : `cockpit-risk-filter-${f.id.replace(/[^a-z0-9]+/gi, "-").toLowerCase()}`}
              onClick={() => setCat(f.id)}
            >
              {f.label}
            </button>
          ))}
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", margin: "0 0 10px" }} data-testid="cockpit-risk-summary-cards">
          <span className="term-chip" data-testid="cockpit-risk-count-pass">
            PASS {model.counts.pass}
          </span>
          <span className="term-chip" data-testid="cockpit-risk-count-warn">
            WARN {model.counts.warn}
          </span>
          <span className="term-chip" data-testid="cockpit-risk-count-fail">
            FAIL {model.counts.fail}
          </span>
          <span className="term-chip" data-testid="cockpit-risk-count-unknown">
            UNKNOWN {model.counts.unknown}
          </span>
          <span className="term-chip" data-testid="cockpit-risk-count-pending">
            PENDING {model.counts.pending}
          </span>
          <span className="term-chip" data-testid="cockpit-risk-count-critical">
            CRITICAL {model.counts.critical}
          </span>
        </div>
        <TermKV
          rows={[
            { k: "freshness", v: model.freshness_summary },
            { k: "robustness", v: model.robustness_summary },
            { k: "exec_realism", v: model.execution_realism_summary },
            { k: "benchmark", v: model.benchmark_summary },
            { k: "paper_safety", v: model.paper_safety_summary },
          ]}
        />
        {model.blocker_lines.length > 0 ? (
          <div className="cockpit-risk-blockers" data-testid="cockpit-risk-blocker-list">
            <div className="pane-footer" style={{ marginBottom: 6 }}>
              Promotion / provider blockers ({model.blocker_lines.length})
            </div>
            <ul className="cockpit-risk-blocker-ul">
              {model.blocker_lines.slice(0, 10).map((line) => (
                <li key={line} style={{ fontSize: 11 }}>
                  {line}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        <DenseTable
          columns={columns}
          rows={rows}
          rowKey={(r) => r.gate_id}
          selectedKey={selectedKey}
          onRowClick={(row) => {
            setSelectedKey(row.gate_id);
            const dig = asString(row.raw["digest_full"]);
            if (dig) setLastDigest?.(dig);
            openInspector({
              title: `${row.label}`,
              subtitle: `${row.source_endpoint} · ${row.category}`,
              body: inspectBody({
                status: row.status,
                summary: row.remediation ?? row.gate_id,
                warnings: row.warning_count ? [`warnings=${row.warning_count}`] : [],
                details: [
                  { k: "blockers", v: String(row.blocker_count) },
                  { k: "digest_prefix", v: row.evidence_digest_prefix ?? "—" },
                  { k: "generated_at_utc", v: row.generated_at_utc ?? "—" },
                ],
              }),
              rawJson: row.raw,
              digestToCopy: dig,
            });
          }}
          empty="UNKNOWN · no gate rows for this filter"
        />
      </Pane>
    </div>
  );
}
