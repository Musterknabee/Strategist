"use client";

import { useMemo } from "react";
import { LocalOpsCommandHintsSection } from "@/components/cockpit/LocalOpsCommandHintsSection";
import { Pane } from "@/components/terminal/Pane";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { TermKV } from "@/components/terminal/TermKV";
import { FIRST_RUN_CLI_COMMAND_IDS } from "@/lib/operator/local-ops-command-hints";
import {
  buildFirstRunDeploymentChecklist,
  firstRunTrustSummary,
  suggestNextFirstRunCommand,
  type FirstRunChecklistInput,
  type FirstRunStepStatus,
} from "@/lib/operator/first-run-deployment-checklist";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import { asRecord, asString } from "@/lib/operator/payload-utils";

function statusBadgeRaw(s: FirstRunStepStatus): string {
  return s;
}

export type FirstRunDeploymentCockpitPaneProps = {
  checklistInput: FirstRunChecklistInput;
  deploymentBlockerCodes: string[];
  deploymentWarningCodes: string[];
  facadeOperatorHint: string | null | undefined;
  openInspector: (payload: InspectorPayload) => void;
};

export function SingleTenantFirstRunWizard({
  checklistInput,
  deploymentBlockerCodes,
  deploymentWarningCodes,
  facadeOperatorHint,
  openInspector,
}: FirstRunDeploymentCockpitPaneProps) {
  const steps = useMemo(() => buildFirstRunDeploymentChecklist(checklistInput), [checklistInput]);
  const nextCmd = useMemo(() => suggestNextFirstRunCommand(steps), [steps]);
  const trust = useMemo(
    () => firstRunTrustSummary(checklistInput.evidencePayload),
    [checklistInput.evidencePayload],
  );

  const ps = checklistInput.providerSetup.data?.summary;

  const inspectFull = () => {
    openInspector({
      title: "Single-tenant first-run · raw inputs",
      subtitle: "Read-plane JSON only (no secrets)",
      body: null,
      rawJson: {
        checklist_steps: steps,
        suggested_next: nextCmd,
        deployment_blockers: deploymentBlockerCodes,
        deployment_warnings: deploymentWarningCodes,
        trust_summary: trust,
        evidence_search_root: trust.searchRoot,
      },
    });
  };

  const cockpit = checklistInput.cockpit;
  const manifestPath = cockpit?.deployment_evidence_manifest_path;
  const cockpitFe = cockpit?.frontend_readiness_status;
  const facadePkg = checklistInput.facade.data?.frontend_package_present;
  const facadeClaimed = checklistInput.facade.data?.frontend_readiness_claimed;

  const deploymentStatusLine = asString(asRecord(checklistInput.evidencePayload)?.deployment_status);
  const deploymentOk = checklistInput.cockpit?.deployment_evidence_ok;

  return (
    <div className="cockpit-first-run-row" data-testid="cockpit-first-run-deployment">
      <Pane
        title="First run · single-tenant deployment"
        badge={<StatusBadge raw="READ_PLANE" />}
        dense
        onInspect={inspectFull}
      >
        <p className="muted" style={{ fontSize: "10px", margin: "0 0 8px" }}>
          Read-plane-first wizard: no shell execution, no ledger writes, no tokens stored, no DEPLOYMENT_APPROVED from browser-only
          views. When blocked, use the suggested command or copy a hint below.
        </p>

        {nextCmd && (
          <div
            className="term-page__banner"
            style={{ fontSize: "11px", marginBottom: "8px" }}
            role="status"
            data-testid="first-run-suggested-next"
          >
            <strong>Suggested next ({nextCmd.stepId}):</strong> {nextCmd.label}
            {nextCmd.command ? (
              <>
                {" "}
                <code style={{ fontSize: "10px", wordBreak: "break-all" }}>{nextCmd.command}</code>
              </>
            ) : null}
          </div>
        )}

        {(deploymentBlockerCodes.length > 0 || deploymentWarningCodes.length > 0) && (
          <p className="term-page__banner" style={{ fontSize: "11px" }} role="status">
            Deployment tier: {deploymentBlockerCodes.length} blocker(s), {deploymentWarningCodes.length} warning(s) from{" "}
            <code>/readiness/deployment</code>.
          </p>
        )}

        <div style={{ marginBottom: "10px" }}>
          <h3 className="muted" style={{ fontSize: "11px", margin: "0 0 4px", fontWeight: 600 }}>
            Deployment evidence summary
          </h3>
          <TermKV
            rows={[
              { k: "deployment_evidence_status", v: deploymentStatusLine ?? cockpit?.deployment_status ?? "—" },
              { k: "deployment_evidence_ok", v: String(deploymentOk ?? "—") },
              { k: "evidence_generated_at_utc", v: cockpit?.evidence_generated_at_utc ?? "—" },
              { k: "deployment_manifest_path", v: manifestPath ?? "—" },
              { k: "registry_digest_prefix", v: trust.digestPrefix },
              { k: "lineage_trust", v: trust.trustStatus },
              { k: "evidence_search_root", v: trust.searchRoot },
            ]}
          />
          {trust.warnings.length > 0 && (
            <p className="muted" style={{ fontSize: "10px", margin: "4px 0 0" }}>
              Lineage / integrity warnings: {trust.warnings.slice(0, 4).join(" · ")}
              {trust.warnings.length > 4 ? " · …" : ""}
            </p>
          )}
        </div>

        {ps && (
          <div style={{ marginBottom: "10px" }} data-testid="first-run-provider-summary">
            <h3 className="muted" style={{ fontSize: "11px", margin: "0 0 4px", fontWeight: 600 }}>
              Provider setup summary
            </h3>
            <TermKV
              rows={[
                { k: "provider_count", v: String(ps.provider_count ?? "—") },
                { k: "ready_count", v: String(ps.ready_count ?? "—") },
                { k: "blocked_count", v: String(ps.blocked_count ?? "—") },
                { k: "action_required_count", v: String(ps.action_required_count ?? "—") },
                { k: "stale_count", v: String(ps.stale_count ?? "—") },
                { k: "not_checked_count", v: String(ps.not_checked_count ?? "—") },
                { k: "missing_secret_count", v: String(ps.missing_secret_count ?? "—") },
              ]}
            />
            <p className="muted" style={{ fontSize: "9px", margin: "4px 0 0" }}>
              Counts only — secret values are never sent to this console.
            </p>
          </div>
        )}

        <section aria-label="First-run checklist">
          <h3 className="muted" style={{ fontSize: "11px", margin: "0 0 6px", fontWeight: 600 }}>
            Ordered checklist
          </h3>
          <ol style={{ margin: 0, paddingLeft: "18px", fontSize: "10px", display: "grid", gap: "8px" }}>
            {steps.map((step) => (
              <li key={step.id} data-testid={`first-run-step-${step.id}`}>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", alignItems: "center" }}>
                  <StatusBadge raw={statusBadgeRaw(step.status)} />
                  <strong>{step.title}</strong>
                </div>
                <div className="muted" style={{ fontSize: "9px", marginTop: "2px" }}>
                  Source: {step.source}
                </div>
                {(step.blockerCount != null || step.warningCount != null) && (
                  <div className="muted" style={{ fontSize: "9px", marginTop: "2px" }}>
                    Blockers: {step.blockerCount ?? "—"} · Warnings: {step.warningCount ?? "—"}
                  </div>
                )}
                {(step.digestPrefix || step.generatedAtUtc) && (
                  <div className="muted" style={{ fontSize: "9px", marginTop: "2px" }}>
                    {step.digestPrefix ? <>Digest prefix: {step.digestPrefix} · </> : null}
                    {step.generatedAtUtc ? <>generated_at_utc: {step.generatedAtUtc}</> : null}
                  </div>
                )}
                {step.supplementalLine && (
                  <div className="muted" style={{ fontSize: "9px", marginTop: "2px" }}>
                    {step.supplementalLine}
                  </div>
                )}
                <div style={{ fontSize: "9px", marginTop: "2px" }}>{step.remediation}</div>
                <button
                  type="button"
                  className="linkish"
                  style={{ fontSize: "9px", marginTop: "2px" }}
                  onClick={() =>
                    openInspector({
                      title: step.title,
                      subtitle: step.source,
                      body: <p style={{ fontSize: "11px" }}>{step.remediation}</p>,
                      rawJson: {
                        step,
                        facade_operator_hint: facadeOperatorHint ?? null,
                        facade_frontend_package_present: facadePkg ?? null,
                        facade_frontend_readiness_claimed: facadeClaimed ?? null,
                        cockpit_frontend_readiness_status: cockpitFe ?? null,
                      },
                    })
                  }
                >
                  Inspect step
                </button>
              </li>
            ))}
          </ol>
        </section>

        <section aria-label="Frontend readiness explanation" style={{ marginTop: "12px" }}>
          <h3 className="muted" style={{ fontSize: "11px", margin: "0 0 4px", fontWeight: 600 }}>
            Frontend readiness (package vs claim)
          </h3>
          <p className="muted" style={{ fontSize: "10px", margin: 0 }} data-testid="first-run-frontend-readiness-copy">
            <strong>Package-present</strong> means the API process sees <code>ui/strategist-web</code> on disk — not that your browser
            build is certified. <strong>Readiness claimed</strong> is opt-in via env + validated artifact and is{" "}
            <strong>not</strong> automatic production certification.
          </p>
          {facadeOperatorHint?.trim() ? (
            <p className="muted" style={{ fontSize: "10px", margin: "6px 0 0" }}>
              Backend hint: {facadeOperatorHint.trim()}
            </p>
          ) : null}
        </section>

        <div style={{ marginTop: "12px" }}>
          <h3 className="muted" style={{ fontSize: "11px", margin: "0 0 6px", fontWeight: 600 }}>
            Copyable CLI hints (not executed here)
          </h3>
          <LocalOpsCommandHintsSection commandIds={FIRST_RUN_CLI_COMMAND_IDS} testIdPrefix="cockpit-first-run-cli-hints" />
        </div>
      </Pane>
    </div>
  );
}

/** @internal Build blocker/warning code lists from deployment payload. */
export function deploymentCodesFromPayload(payload: unknown): { blockers: string[]; warnings: string[] } {
  const r = asRecord(payload);
  if (!r) return { blockers: [], warnings: [] };
  const b = r.blocker_codes;
  const w = r.warning_codes;
  const blockers = Array.isArray(b) ? b.map((x) => String(x)) : [];
  const warnings = Array.isArray(w) ? w.map((x) => String(x)) : [];
  return { blockers, warnings };
}
