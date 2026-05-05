"use client";

import { useMemo, useState } from "react";
import { Pane } from "@/components/terminal/Pane";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { TermKV } from "@/components/terminal/TermKV";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import {
  buildProviderReadinessModel,
  providerReadinessPaneStatus,
  type ProviderReadinessRow,
} from "@/lib/operator/provider-readiness-model";
import type { UiProviderSetupConsolePayload } from "@/lib/api/types";

export type ProviderSetupReadinessPaneProps = {
  providerSetupData: UiProviderSetupConsolePayload | null | undefined;
  providerHealthData: unknown;
  openInspector: (payload: InspectorPayload) => void;
};

function CopyEnvHints({ lines }: { lines: string[] }) {
  const [copied, setCopied] = useState(false);
  if (lines.length === 0) return null;
  const payload = lines.join("\n");
  return (
    <button
      type="button"
      className="linkish"
      data-testid="provider-env-hints-copy"
      onClick={() => {
        void navigator.clipboard.writeText(payload).then(() => {
          setCopied(true);
          window.setTimeout(() => setCopied(false), 1500);
        });
      }}
    >
      {copied ? "Copied env hints" : "Copy env hint placeholders"}
    </button>
  );
}

const columns: DenseColumn<ProviderReadinessRow>[] = [
  { key: "provider", header: "Provider", cell: (r) => r.display_name || r.provider_id },
  { key: "tier", header: "Readiness", width: "120px", cell: (r) => <StatusBadge raw={r.readiness_tier} /> },
  { key: "setup", header: "Setup", width: "150px", cell: (r) => r.setup_status },
  { key: "pit", header: "PIT", width: "120px", cell: (r) => r.pit_suitability },
  { key: "trust", header: "Trust", width: "100px", cell: (r) => r.trust_level },
  { key: "fresh", header: "Freshness", cell: (r) => r.freshness_line },
];

export function ProviderSetupReadinessPane({
  providerSetupData,
  providerHealthData,
  openInspector,
}: ProviderSetupReadinessPaneProps) {
  const model = useMemo(
    () => buildProviderReadinessModel(providerSetupData ?? null, providerHealthData),
    [providerSetupData, providerHealthData],
  );
  const paneStatus = providerReadinessPaneStatus(model);

  const selectedNext = model.rows.find((r) => r.provider_id === model.recommended_next_provider_id) ?? null;

  return (
    <div className="cockpit-provider-setup-row" data-testid="cockpit-provider-setup-readiness">
      <Pane
        title="Provider setup / data-source readiness"
        dense
        badge={<StatusBadge raw={paneStatus} />}
        onInspect={() =>
          openInspector({
            title: "Provider setup readiness",
            subtitle: "Read-plane setup/freshness/safety view",
            rawJson: providerSetupData ?? {},
          })
        }
      >
        <TermKV
          rows={[
            { k: "generated_at_utc", v: model.generated_at_utc ?? "—" },
            { k: "sample_manifest_digest", v: model.samples_manifest_digest_prefix ?? "—" },
            { k: "sample_manifest_path", v: model.samples_manifest_path ?? "—" },
            { k: "provider_count", v: String(model.summary.provider_count) },
            { k: "ready_count", v: String(model.summary.ready_count) },
            { k: "blocked_count", v: String(model.summary.blocked_count) },
            { k: "action_required_count", v: String(model.summary.action_required_count) },
            { k: "stale_count", v: String(model.summary.stale_count) },
            { k: "not_checked_count", v: String(model.summary.not_checked_count) },
            { k: "missing_secret_count", v: String(model.summary.missing_secret_count) },
          ]}
        />
        {model.execution_workflow_blockers.length > 0 && (
          <p className="term-page__banner" role="status" style={{ fontSize: "11px", marginTop: "6px" }}>
            Execution-safety blockers: {model.execution_workflow_blockers.join(" · ")}
          </p>
        )}
        {selectedNext && (
          <p className="muted" style={{ fontSize: "10px", margin: "6px 0" }} data-testid="provider-recommended-next">
            Recommended next provider: <strong>{selectedNext.display_name}</strong> ({selectedNext.provider_id}) · priority{" "}
            {String(selectedNext.recommended_priority)}
          </p>
        )}

        <DenseTable
          columns={columns}
          rows={model.rows}
          rowKey={(r) => r.__id}
          onRowClick={(row) => {
            const warnings = Array.isArray(row.warnings) ? row.warnings : [];
            const blockers = Array.isArray(row.blockers) ? row.blockers : [];
            openInspector({
              title: `Provider setup · ${row.display_name}`,
              subtitle: row.provider_id,
              body: (
                <div style={{ display: "grid", gap: "6px", fontSize: "11px" }}>
                  <TermKV
                    rows={[
                      { k: "category", v: row.category },
                      { k: "research_role", v: row.research_role },
                      { k: "access_type", v: row.access_type },
                      { k: "trust_level", v: row.trust_level },
                      { k: "pit_suitability", v: row.pit_suitability },
                      { k: "classified_status", v: row.classified_status },
                      { k: "setup_status", v: row.setup_status },
                      { k: "readiness_tier", v: row.readiness_tier },
                      { k: "may_gate_live_promotion", v: String(row.may_gate_live_promotion) },
                      {
                        k: "unsafe_promotion_authority_without_license",
                        v: String(row.unsafe_as_promotion_authority_without_license),
                      },
                      { k: "sample_digest_prefix", v: row.sample_digest_prefix ?? "—" },
                      { k: "evidence_reference", v: row.evidence_reference ?? "—" },
                    ]}
                  />
                  <div>
                    <strong>Blockers:</strong> {blockers.length ? blockers.join(" · ") : "NONE"}
                  </div>
                  <div>
                    <strong>Warnings:</strong> {warnings.length ? warnings.join(" · ") : "NONE"}
                  </div>
                  <div>
                    <strong>Expected env vars (names only):</strong>{" "}
                    {row.expected_env_vars && row.expected_env_vars.length ? row.expected_env_vars.join(", ") : "NONE"}
                  </div>
                  <div>
                    <strong>Env hint placeholders:</strong>
                    <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>
                      {row.env_hint_lines.length ? row.env_hint_lines.join("\n") : "NONE"}
                    </pre>
                  </div>
                  <CopyEnvHints lines={row.env_hint_lines} />
                </div>
              ),
              rawJson: {
                ...row,
                secret_values_exposed: false,
              },
            });
          }}
          empty="UNKNOWN · provider setup unavailable"
        />
      </Pane>
    </div>
  );
}
