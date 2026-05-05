"use client";

import { useMemo } from "react";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { StatusBadge } from "@/components/operator/StatusBadge";
import type { UiMutationSafetyStatus } from "@/lib/api/types";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import { buildExecutionFirewallModel, type ExecutionFirewallSafetyLabel } from "@/lib/operator/execution-firewall-model";
import { inspectBody } from "./cockpit-utils";

export type CapitalExecutionFirewallPaneProps = {
  paperExecution: Record<string, unknown> | null;
  paperBroker: Record<string, unknown> | null;
  paperTracking: Record<string, unknown> | null;
  providerSetup: Record<string, unknown> | null;
  providerHealth: Record<string, unknown> | null;
  runtimeMutationSafety: UiMutationSafetyStatus | null;
  executionAuthorityHint: string | null;
  queryFailed: boolean;
  openInspector: (payload: InspectorPayload) => void;
};

function paneBadge(labels: ExecutionFirewallSafetyLabel[], queryFailed: boolean): string {
  if (queryFailed) return "DEGRADED";
  if (labels.includes("LIVE_BLOCKED") || labels.includes("PAPER_ONLY")) return "BOUNDARY";
  return "READ_PLANE";
}

export function CapitalExecutionFirewallPane({
  paperExecution,
  paperBroker,
  paperTracking,
  providerSetup,
  providerHealth,
  runtimeMutationSafety,
  executionAuthorityHint,
  queryFailed,
  openInspector,
}: CapitalExecutionFirewallPaneProps) {
  const model = useMemo(
    () =>
      buildExecutionFirewallModel({
        paperExecution,
        paperBroker,
        paperTracking,
        providerSetup,
        providerHealth,
        runtimeMutationSafety,
        executionAuthorityHint,
        queryFailed,
      }),
    [
      executionAuthorityHint,
      paperBroker,
      paperExecution,
      paperTracking,
      providerHealth,
      providerSetup,
      queryFailed,
      runtimeMutationSafety,
    ],
  );

  const badge = paneBadge(model.safety_labels, queryFailed);

  return (
    <div className="cockpit-execution-firewall-row" data-testid="cockpit-execution-firewall">
      <Pane
        title="Capital / execution firewall"
        dense
        badge={<StatusBadge raw={badge} />}
        onInspect={() =>
          openInspector({
            title: "Execution firewall · read-plane bundle",
            subtitle: model.firewall_id,
            body: inspectBody({
              status: model.capital_mode,
              summary: model.recommended_review_action,
              warnings: model.safety_labels,
              details: model.proof_lines.slice(0, 8).map((line) => {
                const [k, ...rest] = line.split("=");
                return { k: k ?? line, v: rest.length ? rest.join("=") : "—" };
              }),
            }),
            rawJson: model.raw_sources,
            digestToCopy: model.digest_full ?? undefined,
          })
        }
      >
        <div className="pane-footer" style={{ marginBottom: 6 }}>
          Safety posture
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }} data-testid="cockpit-firewall-safety-labels">
          {model.safety_labels.map((lab) => (
            <span key={lab} className="term-chip" data-testid={`cockpit-firewall-safety-label-${lab}`}>
              {lab}
            </span>
          ))}
        </div>
        <TermKV
          rows={[
            { k: "capital_mode", v: <StatusBadge raw={model.capital_mode} /> },
            { k: "recommended_review", v: <StatusBadge raw={model.recommended_review_action} /> },
            { k: "live_blocked", v: String(model.live_blocked) },
            { k: "paper_only", v: String(model.paper_only) },
            { k: "broker_status", v: <StatusBadge raw={model.broker_status} /> },
            { k: "submission", v: model.submission_status },
            { k: "reconciliation", v: <StatusBadge raw={model.reconciliation_status} /> },
            { k: "evidence_freshness", v: <StatusBadge raw={model.evidence_freshness_status} /> },
            { k: "authorities", v: model.authority_status },
            { k: "blockers_warnings", v: `${model.blocker_count}/${model.warning_count}` },
            { k: "digest_prefix", v: model.digest_prefix },
            { k: "generated_at_utc", v: model.generated_at_utc },
          ]}
        />

        <div className="pane-footer" style={{ margin: "10px 0 6px" }}>
          Proof lines (no secrets)
        </div>
        <ul className="cockpit-risk-blocker-ul" style={{ fontSize: 11 }} data-testid="cockpit-firewall-proof-lines">
          {model.proof_lines.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>

        {model.safe_artifact_hints.length > 0 ? (
          <>
            <div className="pane-footer" style={{ margin: "10px 0 6px" }}>
              Artifact basenames (read-plane paths)
            </div>
            <ul className="cockpit-risk-blocker-ul" style={{ fontSize: 11 }} data-testid="cockpit-firewall-artifact-hints">
              {model.safe_artifact_hints.map((h) => (
                <li key={h}>{h}</li>
              ))}
            </ul>
          </>
        ) : null}
      </Pane>
    </div>
  );
}
