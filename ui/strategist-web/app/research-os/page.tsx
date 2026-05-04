"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiResearchOsStatus } from "@/hooks/useUiResearchOsStatus";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

export default function ResearchOsPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiResearchOsStatus();
  const root = q.data != null ? asRecord(q.data) : null;

  const tape: TapeLine[] = useMemo(() => {
    const ts = asString(root?.generated_at_utc);
    const deg = root?.degraded != null ? asStringArray(root.degraded) : [];
    return [
      {
        id: "ros",
        ts,
        severity: deg.length ? "warn" : "ok",
        text: `RESEARCH_OS ${deg.length ? `DEGRADED:${deg.length}` : "OK"}`,
      },
    ];
  }, [root]);

  useTerminalPageBind(tape, []);

  if (!config.ok) {
    return (
      <div className="term-page cockpit-page">
        <div className="term-page__banner">{config.error.message}</div>
      </div>
    );
  }

  const artSummary = root?.artifact_root_summary != null ? asRecord(root.artifact_root_summary as object) : null;
  const runtimeDemo = root?.runtime_demo_manifest != null ? asRecord(root.runtime_demo_manifest as object) : null;
  const gauntlet = root?.gauntlet_latest != null ? asRecord(root.gauntlet_latest as object) : null;
  const paper = root?.paper_tracking_latest != null ? asRecord(root.paper_tracking_latest as object) : null;
  const promo = root?.promotion_packet_latest != null ? asRecord(root.promotion_packet_latest as object) : null;
  const broker = root?.paper_broker_status != null ? asRecord(root.paper_broker_status as object) : null;
  const compute = root?.compute_status != null ? asRecord(root.compute_status as object) : null;
  const demo = root?.demo_manifest != null ? asRecord(root.demo_manifest as object) : null;
  const provider = root?.provider_ingestion_latest != null ? asRecord(root.provider_ingestion_latest as object) : null;
  const providerLoop =
    root?.provider_paper_loop_latest != null ? asRecord(root.provider_paper_loop_latest as object) : null;
  const providerHist =
    root?.provider_historical_snapshot_latest != null ? asRecord(root.provider_historical_snapshot_latest as object) : null;
  const shadowBook = root?.shadow_book_latest != null ? asRecord(root.shadow_book_latest as object) : null;
  const researchClosure = root?.research_os_closure_latest != null ? asRecord(root.research_os_closure_latest as object) : null;
  const closureLatest = researchClosure?.latest != null ? asRecord(researchClosure.latest as object) : null;
  const researchAttestation = root?.research_os_attestation_latest != null ? asRecord(root.research_os_attestation_latest as object) : null;
  const researchBriefing = root?.research_os_briefing_latest != null ? asRecord(root.research_os_briefing_latest as object) : null;
  const researchExport = root?.research_os_export_latest != null ? asRecord(root.research_os_export_latest as object) : null;
  const researchRun = root?.research_os_operator_run_latest != null ? asRecord(root.research_os_operator_run_latest as object) : null;
  const researchCatalog = root?.research_os_evidence_catalog_latest != null ? asRecord(root.research_os_evidence_catalog_latest as object) : null;
  const researchDrift = root?.research_os_evidence_drift_latest != null ? asRecord(root.research_os_evidence_drift_latest as object) : null;
  const researchPolicyGate = root?.research_os_policy_gate_latest != null ? asRecord(root.research_os_policy_gate_latest as object) : null;
  const researchException = root?.research_os_exception_latest != null ? asRecord(root.research_os_exception_latest as object) : null;
  const researchRemediation = root?.research_os_remediation_latest != null ? asRecord(root.research_os_remediation_latest as object) : null;
  const researchReleaseReadiness = root?.research_os_release_readiness_latest != null ? asRecord(root.research_os_release_readiness_latest as object) : null;
  const attestationVerification = researchAttestation?.latest_verification != null ? asRecord(researchAttestation.latest_verification as object) : null;
  const attestationLatest = researchAttestation?.latest_attestation != null ? asRecord(researchAttestation.latest_attestation as object) : null;
  const briefingLatest = researchBriefing?.latest_briefing != null ? asRecord(researchBriefing.latest_briefing as object) : null;
  const exportLatest = researchExport?.latest_export != null ? asRecord(researchExport.latest_export as object) : null;
  const runLatest = researchRun?.latest != null ? asRecord(researchRun.latest as object) : null;
  const catalogLatest = researchCatalog?.latest != null ? asRecord(researchCatalog.latest as object) : null;
  const driftLatest = researchDrift?.latest != null ? asRecord(researchDrift.latest as object) : null;
  const policyGateLatest = researchPolicyGate?.latest != null ? asRecord(researchPolicyGate.latest as object) : null;
  const exceptionLatest = researchException?.latest != null ? asRecord(researchException.latest as object) : null;
  const remediationLatest = researchRemediation?.latest != null ? asRecord(researchRemediation.latest as object) : null;
  const releaseReadinessLatest = researchReleaseReadiness?.latest != null ? asRecord(researchReleaseReadiness.latest as object) : null;
  const exportVerification = researchExport?.latest_verification != null ? asRecord(researchExport.latest_verification as object) : null;
  const shadowLatest = shadowBook?.latest != null ? asRecord(shadowBook.latest as object) : null;
  const shadowRisk = shadowBook?.latest_risk_summary != null ? asRecord(shadowBook.latest_risk_summary as object) : null;
  const brokerArt =
    root?.paper_broker_status_latest != null ? asRecord(root.paper_broker_status_latest as object) : null;
  const provGaunt =
    root?.provider_backed_gauntlet_latest != null ? asRecord(root.provider_backed_gauntlet_latest as object) : null;
  const daily = root?.daily_tracking_latest != null ? asRecord(root.daily_tracking_latest as object) : null;
  const cpcv = root?.cpcv_latest != null ? asRecord(root.cpcv_latest as object) : null;
  const portfolio = root?.portfolio_allocation_latest != null ? asRecord(root.portfolio_allocation_latest as object) : null;
  const latestPaper = paper?.latest != null ? asRecord(paper.latest as object) : null;
  const trackingId = asString(latestPaper?.tracking_id as string);

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Research OS</h1>
          <p className="muted">
            Consolidated read-plane status · evidence only · no live trading · no broker orders from browser · promotion
            packets are not live approval
          </p>
        </div>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Status rail" dense onInspect={() => openInspector({ title: "Research OS status", rawJson: root ?? {} })}>
          {q.isLoading && <p className="muted">Loading…</p>}
          {q.isError && <p className="term-page__banner">Could not load /ui/research-os/status</p>}
          {root && (
            <div style={{ fontSize: "11px", display: "grid", gap: "0.5rem" }}>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", alignItems: "center" }}>
                <span className="muted">Degraded</span>
                <span>{(asStringArray(root.degraded).length ? asStringArray(root.degraded).join(", ") : "—") as string}</span>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", alignItems: "center" }}>
                <span className="muted">Warnings</span>
                <span>{(asStringArray(root.warnings).length ? asStringArray(root.warnings).join("; ") : "—") as string}</span>
              </div>
            </div>
          )}
        </Pane>

        <Pane
          title="Artifact roots (API scan)"
          dense
          onInspect={() => openInspector({ title: "Artifact roots", rawJson: artSummary ?? {} })}
        >
          {!artSummary ? (
            <p className="muted">—</p>
          ) : (
            <TermKV
              rows={[
                { k: "artifact_root", v: asString(artSummary.artifact_root as string) ?? "—" },
                { k: "strategy_batch_scan", v: asString(artSummary.strategy_batch_scan_root as string) ?? "—" },
                { k: "paper_tracking_scan", v: asString(artSummary.paper_tracking_scan_root as string) ?? "—" },
                { k: "strategy_data", v: asString(artSummary.strategy_data_root as string) ?? "—" },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Runtime demo manifest"
          dense
          onInspect={() => openInspector({ title: "Runtime demo manifest", rawJson: runtimeDemo ?? {} })}
        >
          {!runtimeDemo || runtimeDemo.status === "NOT_PRESENT" ? (
            <p className="muted">
              No runtime_demo_manifest.json — run{" "}
              <code className="json-preview">strategy-validator-research-os-runtime-demo</code> or host script (see
              docs).
            </p>
          ) : (
            <TermKV
              rows={[
                { k: "status", v: <StatusBadge raw={asString(runtimeDemo.status as string) ?? "—"} /> },
                { k: "ok", v: String(runtimeDemo.ok ?? "—") },
                { k: "run_id", v: asString(runtimeDemo.run_id as string) ?? "—" },
                { k: "generated_at", v: asString(runtimeDemo.generated_at_utc as string) ?? "—" },
                { k: "artifact_root", v: asString(runtimeDemo.artifact_root as string) ?? "—" },
                { k: "digest", v: asString(runtimeDemo.manifest_sha256 as string) ?? "—" },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Provider-backed paper loop"
          dense
          onInspect={() => openInspector({ title: "Provider paper loop", rawJson: providerLoop ?? {} })}
        >
          {!providerLoop || providerLoop.status === "NOT_PRESENT" ? (
            <p className="muted">
              No provider_paper_loop_manifest.json — run{" "}
              <code className="json-preview">strategy-validator-provider-paper-loop</code> or{" "}
              <code className="json-preview">python scripts/run_provider_paper_loop.py</code> (fixture-first; see docs).
            </p>
          ) : (
            <TermKV
              rows={[
                { k: "status", v: <StatusBadge raw={asString(providerLoop.status as string) ?? "—"} /> },
                { k: "ok", v: String(providerLoop.ok ?? "—") },
                { k: "run_id", v: asString(providerLoop.run_id as string) ?? "—" },
                { k: "generated_at", v: asString(providerLoop.generated_at_utc as string) ?? "—" },
                {
                  k: "historical_snapshot_run",
                  v: <StatusBadge raw={asString(providerHist?.status as string) ?? "—"} />,
                },
                {
                  k: "broker_status_artifact",
                  v: <StatusBadge raw={asString(brokerArt?.status as string) ?? "—"} />,
                },
                {
                  k: "provider_strategies_in_latest_batch",
                  v: String(provGaunt?.provider_snapshot_strategy_count ?? "—"),
                },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Shadow Book"
          dense
          onInspect={() => openInspector({ title: "Shadow Book", rawJson: shadowBook ?? {} })}
        >
          {!shadowLatest ? (
            <p className="muted">No shadow book manifest detected — run <code className="json-preview">strategy-validator-shadow-book create</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "book_id", v: asString(shadowLatest.book_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(shadowLatest.status as string) ?? "—"} /> },
                { k: "cash", v: String(shadowLatest.cash ?? "—") },
                { k: "risk_status", v: <StatusBadge raw={asString(shadowRisk?.status as string) ?? "—"} /> },
                { k: "net_liquidation_value", v: String(shadowRisk?.net_liquidation_value ?? "—") },
                { k: "risk_flags", v: Array.isArray(shadowRisk?.risk_flags) ? shadowRisk.risk_flags.join(", ") : "—" },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Research OS closure"
          dense
          onInspect={() => openInspector({ title: "Research OS closure", rawJson: researchClosure ?? {} })}
        >
          {!closureLatest ? (
            <p className="muted">No closure manifest detected — run <code className="json-preview">strategy-validator-research-os-closure build</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "closure_id", v: asString(closureLatest.closure_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(closureLatest.status as string) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(closureLatest.trust_banner as string) ?? "—"} /> },
                { k: "present_artifacts", v: String(closureLatest.present_artifact_count ?? "—") },
                { k: "manifest_sha256", v: (asString(closureLatest.manifest_sha256 as string) ?? "—").slice(0, 16) },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Research OS attestation"
          dense
          onInspect={() => openInspector({ title: "Research OS attestation", rawJson: researchAttestation ?? {} })}
        >
          {!attestationVerification ? (
            <p className="muted">No closure verification result — run <code className="json-preview">strategy-validator-research-os-attestation verify --write</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "verification_status", v: <StatusBadge raw={asString(attestationVerification.status as string) ?? "—"} /> },
                { k: "closure_id", v: asString(attestationVerification.closure_id as string) ?? "—" },
                { k: "digest_mismatches", v: String(Array.isArray(attestationVerification.digest_mismatches) ? attestationVerification.digest_mismatches.length : 0) },
                { k: "attestation_decision", v: <StatusBadge raw={asString(attestationLatest?.decision as string) ?? "NOT_ATTESTED"} /> },
                { k: "attestation_sha256", v: (asString(attestationLatest?.attestation_sha256 as string) ?? "—").slice(0, 16) },
              ]}
            />
          )}
        </Pane>


        <Pane
          title="Research OS briefing"
          dense
          onInspect={() => openInspector({ title: "Research OS briefing", rawJson: researchBriefing ?? {} })}
        >
          {!briefingLatest ? (
            <p className="muted">No briefing pack detected — run <code className="json-preview">strategy-validator-research-os-briefing build --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "briefing_id", v: asString(briefingLatest.briefing_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(briefingLatest.status as string) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(briefingLatest.trust_banner as string) ?? "—"} /> },
                { k: "actions", v: String(Array.isArray(briefingLatest.action_items) ? briefingLatest.action_items.length : 0) },
                { k: "sections", v: String(Array.isArray(briefingLatest.sections) ? briefingLatest.sections.length : 0) },
                { k: "briefing_sha256", v: (asString(briefingLatest.briefing_sha256 as string) ?? "—").slice(0, 16) },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Research OS export"
          dense
          onInspect={() => openInspector({ title: "Research OS export", rawJson: researchExport ?? {} })}
        >
          {!exportLatest ? (
            <p className="muted">No export bundle detected — run <code className="json-preview">strategy-validator-research-os-export build --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "export_id", v: asString(exportLatest.export_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(exportLatest.status as string) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(exportLatest.trust_banner as string) ?? "—"} /> },
                { k: "verification", v: <StatusBadge raw={asString(exportVerification?.status as string) ?? "NO_VERIFY"} /> },
                { k: "files", v: String(Array.isArray(exportLatest.files) ? exportLatest.files.length : 0) },
                { k: "archive_sha256", v: (asString(exportLatest.archive_sha256 as string) ?? "—").slice(0, 16) },
                { k: "manifest_sha256", v: (asString(exportLatest.manifest_sha256 as string) ?? "—").slice(0, 16) },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Research OS operator run"
          dense
          onInspect={() => openInspector({ title: "Research OS operator run", rawJson: researchRun ?? {} })}
        >
          {!runLatest ? (
            <p className="muted">No operator run manifest detected — run <code className="json-preview">strategy-validator-research-os-run run --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "run_id", v: asString(runLatest.run_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(runLatest.status as string) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(runLatest.trust_banner as string) ?? "—"} /> },
                { k: "steps", v: String(Array.isArray(runLatest.steps) ? runLatest.steps.length : 0) },
                { k: "operator_run_spine", v: (asString(asRecord(runLatest.digests)?.operator_run_spine_sha256) ?? "—").slice(0, 16) },
                { k: "manifest_sha256", v: (asString(runLatest.manifest_sha256 as string) ?? "—").slice(0, 16) },
              ]}
            />
          )}
        </Pane>


        <Pane
          title="Research OS evidence catalog"
          dense
          onInspect={() => openInspector({ title: "Research OS evidence catalog", rawJson: researchCatalog ?? {} })}
        >
          {!catalogLatest ? (
            <p className="muted">No evidence catalog detected — run <code className="json-preview">strategy-validator-research-os-catalog build --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "catalog_id", v: asString(catalogLatest.catalog_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(catalogLatest.status as string) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(catalogLatest.trust_banner as string) ?? "—"} /> },
                { k: "entries", v: String(catalogLatest.entry_count ?? "—") },
                { k: "latest_entries", v: String(catalogLatest.latest_entry_count ?? "—") },
                { k: "catalog_spine", v: (asString(catalogLatest.catalog_spine_sha256 as string) ?? "—").slice(0, 16) },
                { k: "manifest_sha256", v: (asString(catalogLatest.manifest_sha256 as string) ?? "—").slice(0, 16) },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Research OS evidence drift"
          dense
          onInspect={() => openInspector({ title: "Research OS evidence drift", rawJson: researchDrift ?? {} })}
        >
          {!driftLatest ? (
            <p className="muted">No drift report detected — run <code className="json-preview">strategy-validator-research-os-drift build --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "drift_id", v: asString(driftLatest.drift_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(driftLatest.status as string) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(driftLatest.trust_banner as string) ?? "—"} /> },
                { k: "added", v: String(driftLatest.added_count ?? "—") },
                { k: "removed", v: String(driftLatest.removed_count ?? "—") },
                { k: "changed", v: String(driftLatest.changed_count ?? "—") },
                { k: "unchanged", v: String(driftLatest.unchanged_count ?? "—") },
                { k: "drift_spine", v: (asString(driftLatest.drift_spine_sha256 as string) ?? "—").slice(0, 16) },
              ]}
            />
          )}
        </Pane>



        <Pane
          title="Research OS policy gate"
          dense
          onInspect={() => openInspector({ title: "Research OS policy gate", rawJson: researchPolicyGate ?? {} })}
        >
          {!policyGateLatest ? (
            <p className="muted">No policy gate report detected — run <code className="json-preview">strategy-validator-research-os-policy-gate build --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "gate_id", v: asString(policyGateLatest.gate_id) ?? "—" },
                { k: "decision", v: <StatusBadge raw={asString(policyGateLatest.decision as string) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(policyGateLatest.trust_banner as string) ?? "—"} /> },
                { k: "required_inputs", v: `${policyGateLatest.present_input_count ?? 0}/${policyGateLatest.required_input_count ?? 0}` },
                { k: "warnings", v: String(policyGateLatest.warning_count ?? "—") },
                { k: "blockers", v: String(policyGateLatest.blocker_count ?? "—") },
                { k: "gate_spine", v: (asString(policyGateLatest.gate_spine_sha256 as string) ?? "—").slice(0, 16) },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Research OS governed exception"
          dense
          onInspect={() => openInspector({ title: "Research OS exception", rawJson: researchException ?? {} })}
        >
          {!exceptionLatest ? (
            <p className="muted">No exception record detected — run <code className="json-preview">strategy-validator-research-os-exception request --rationale "..." --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "exception_id", v: asString(exceptionLatest.exception_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(exceptionLatest.status as string) ?? "—"} /> },
                { k: "decision", v: <StatusBadge raw={asString(exceptionLatest.decision as string) ?? "—"} /> },
                { k: "expires_at", v: asString(exceptionLatest.expires_at_utc as string) ?? "—" },
                { k: "source_gate", v: asString(exceptionLatest.source_policy_gate_id as string) ?? "—" },
                { k: "gate_decision", v: <StatusBadge raw={asString(exceptionLatest.source_policy_gate_decision as string) ?? "—"} /> },
                { k: "exception_spine", v: (asString(exceptionLatest.exception_spine_sha256 as string) ?? "—").slice(0, 16) },
              ]}
            />
          )}
        </Pane>



        <Pane
          title="Research OS remediation plan"
          dense
          onInspect={() => openInspector({ title: "Research OS remediation", rawJson: researchRemediation ?? {} })}
        >
          {!remediationLatest ? (
            <p className="muted">No remediation plan detected — run <code className="json-preview">strategy-validator-research-os-remediation build --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "plan_id", v: asString(remediationLatest.plan_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(remediationLatest.status as string) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(remediationLatest.trust_banner as string) ?? "—"} /> },
                { k: "items", v: String(remediationLatest.item_count ?? "—") },
                { k: "open", v: String(remediationLatest.open_count ?? "—") },
                { k: "blocked", v: String(remediationLatest.blocked_count ?? "—") },
                { k: "waived", v: String(remediationLatest.waived_count ?? "—") },
                { k: "source_gate", v: asString(remediationLatest.source_policy_gate_id as string) ?? "—" },
                { k: "spine", v: (asString(remediationLatest.remediation_spine_sha256 as string) ?? "—").slice(0, 16) },
              ]}
            />
          )}
        </Pane>



        <Pane
          title="Research OS release readiness"
          dense
          onInspect={() => openInspector({ title: "Research OS release readiness", rawJson: researchReleaseReadiness ?? {} })}
        >
          {!releaseReadinessLatest ? (
            <p className="muted">No release-readiness report detected — run <code className="json-preview">strategy-validator-research-os-release-readiness build --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "report_id", v: asString(releaseReadinessLatest.report_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(releaseReadinessLatest.status as string) ?? "—"} /> },
                { k: "decision", v: <StatusBadge raw={asString(releaseReadinessLatest.decision as string) ?? "—"} /> },
                { k: "review_ready", v: String(releaseReadinessLatest.release_review_ready ?? "—") },
                { k: "deployment_approved", v: String(releaseReadinessLatest.deployment_approved ?? "—") },
                { k: "P0/P1 open", v: `${String(releaseReadinessLatest.p0_open_count ?? 0)} / ${String(releaseReadinessLatest.p1_open_count ?? 0)}` },
                { k: "source_gate", v: asString(releaseReadinessLatest.source_policy_gate_id as string) ?? "—" },
                { k: "spine", v: (asString(releaseReadinessLatest.release_readiness_spine_sha256 as string) ?? "—").slice(0, 16) },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Gauntlet (latest batch)"
          dense
          onInspect={() => openInspector({ title: "Gauntlet latest", rawJson: gauntlet ?? {} })}
        >
          {!gauntlet ? (
            <p className="muted">—</p>
          ) : (
            <TermKV
              rows={[
                { k: "batch_id", v: asString(gauntlet.batch_id) ?? "—" },
                { k: "run_id", v: asString(gauntlet.run_id) ?? "—" },
                { k: "ok", v: String(gauntlet.ok ?? "—") },
                { k: "strategies", v: String(gauntlet.strategy_count ?? "—") },
                { k: "passed", v: String(gauntlet.passed_count ?? "—") },
                { k: "paper_only", v: String(gauntlet.paper_only_count ?? "—") },
                { k: "blocked", v: String(gauntlet.blocked_count ?? "—") },
                { k: "failed", v: String(gauntlet.failed_count ?? "—") },
                {
                  k: "top_candidate",
                  v: asString((gauntlet.top_candidate as { strategy_id?: string } | undefined)?.strategy_id) ?? "—",
                },
                {
                  k: "provider_snapshot_strategies",
                  v: String(provGaunt?.provider_snapshot_strategy_count ?? "—"),
                },
                { k: "summary_path", v: asString(gauntlet.summary_path) ?? "—" },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.5rem", fontSize: "10px" }}>
            docker exec strategist-local-api strategy-validator-research-os-runtime-demo --artifact-root
            /var/lib/strategy-validator/artifacts --run-id my-run --allow-synthetic-demo --overwrite --skip-benchmark
            --json
          </pre>
        </Pane>

        <Pane
          title="Paper tracking & lifecycle"
          dense
          onInspect={() => openInspector({ title: "Paper latest", rawJson: paper ?? {} })}
        >
          {!paper?.latest ? (
            <p className="muted">No paper tracking bundle detected under scan root.</p>
          ) : (
            <TermKV
              rows={[
                { k: "tracking_id", v: trackingId || "—" },
                {
                  k: "kill_posture",
                  v: asString(latestPaper?.lifecycle_kill_rule_posture as string) ?? "—",
                },
                {
                  k: "lifecycle",
                  v: asString(latestPaper?.lifecycle_state as string) ?? "—",
                },
                {
                  k: "promotion_review_ready",
                  v: String((latestPaper?.promotion_review_ready as boolean | undefined) ?? false),
                },
                {
                  k: "promotion_packet",
                  v: <StatusBadge raw={asString(promo?.recommendation as string) ?? "—"} />,
                },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Lifecycle / promotion (evidence only)"
          dense
          onInspect={() => openInspector({ title: "Lifecycle / promotion", rawJson: { lifecycle: root?.lifecycle_latest, promo } })}
        >
          <p className="muted" style={{ fontSize: "11px", marginBottom: "0.5rem" }}>
            READY_FOR_HUMAN_REVIEW is an evidence gate for operators, not automated live promotion.
          </p>
          {!latestPaper ? (
            <p className="muted">—</p>
          ) : (
            <TermKV
              rows={[
                { k: "state", v: asString(latestPaper.lifecycle_state as string) ?? "—" },
                {
                  k: "recommendation",
                  v: <StatusBadge raw={asString(promo?.recommendation as string) ?? "—"} />,
                },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Provider ingestion (artifacts)"
          dense
          onInspect={() => openInspector({ title: "Provider ingestion", rawJson: provider ?? {} })}
        >
          {!provider ? (
            <p className="muted">—</p>
          ) : (
            <TermKV
              rows={[
                { k: "status", v: <StatusBadge raw={asString(provider.status) ?? "—"} /> },
                { k: "provider_status", v: asString(provider.provider_status as string) ?? "—" },
                { k: "pit_status", v: asString(provider.pit_status as string) ?? "—" },
                { k: "artifact_path", v: asString(provider.artifact_path as string) ?? "—" },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Daily paper tracking"
          dense
          onInspect={() => openInspector({ title: "Daily tracking", rawJson: daily ?? {} })}
        >
          {!daily || Object.keys(daily).length === 0 ? (
            <p className="muted">No daily_run manifest found under paper scan root.</p>
          ) : (
            <TermKV
              rows={[
                { k: "manifest_path", v: asString(daily.manifest_path as string) ?? "—" },
                { k: "run_date_utc", v: asString(daily.run_date_utc as string) ?? "—" },
                { k: "failure_count", v: String((daily.failure_count as number | undefined) ?? "—") },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="CPCV / robustness (from latest batch)"
          dense
          onInspect={() => openInspector({ title: "CPCV hint", rawJson: cpcv ?? {} })}
        >
          {!cpcv ? (
            <p className="muted">—</p>
          ) : (
            <TermKV
              rows={[
                { k: "hint_status", v: asString(cpcv.status as string) ?? "—" },
                {
                  k: "strategies_with_cpcv_fields",
                  v: String(Array.isArray(cpcv.strategies) ? cpcv.strategies.length : 0),
                },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Portfolio allocation (latest batch dir)"
          dense
          onInspect={() => openInspector({ title: "Portfolio allocation", rawJson: portfolio ?? {} })}
        >
          {!portfolio || Object.keys(portfolio).length === 0 ? (
            <p className="muted">No portfolio_allocation_result.json next to latest batch summary.</p>
          ) : (
            <TermKV
              rows={[
                {
                  k: "gate",
                  v: <StatusBadge raw={asString(portfolio.allocation_gate_status as string) ?? "—"} />,
                },
                {
                  k: "excluded_n",
                  v: String(Array.isArray(portfolio.excluded) ? portfolio.excluded.length : 0),
                },
                {
                  k: "warnings_n",
                  v: String(Array.isArray(portfolio.warnings) ? portfolio.warnings.length : 0),
                },
                {
                  k: "blockers_n",
                  v: String(Array.isArray(portfolio.blockers) ? portfolio.blockers.length : 0),
                },
              ]}
            />
          )}
          {portfolio?.allocation_gate_status === "BLOCKED" && (
            <p className="muted" style={{ fontSize: "11px", marginTop: "0.35rem" }}>
              BLOCKED is a documented gate outcome (e.g. correlation / eligibility), not a UI error.
            </p>
          )}
        </Pane>

        <Pane
          title="Paper broker policy (env)"
          dense
          onInspect={() => openInspector({ title: "Paper broker", rawJson: broker ?? {} })}
        >
          {!broker ? (
            <p className="muted">—</p>
          ) : (
            <TermKV
              rows={[
                {
                  k: "policy",
                  v: <StatusBadge raw={asString(broker.policy_status) ?? "—"} />,
                },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Compute / GPU (advisory)"
          dense
          onInspect={() => openInspector({ title: "Compute", rawJson: compute ?? {} })}
        >
          {!compute ? (
            <p className="muted">—</p>
          ) : (
            <TermKV
              rows={[
                { k: "readiness", v: asString(compute.research_compute_readiness) ?? "—" },
                {
                  k: "gpu",
                  v: String((compute.gpu_probe as { gpu_available?: boolean } | undefined)?.gpu_available ?? "—"),
                },
              ]}
            />
          )}
        </Pane>

        <Pane title="Legacy demo manifest" dense onInspect={() => openInspector({ title: "Demo manifest", rawJson: demo ?? {} })}>
          {!demo || demo.status === "NOT_PRESENT" ? (
            <p className="muted">Optional: scripts/run_research_os_demo.py (older layout).</p>
          ) : (
            <TermKV
              rows={[
                { k: "status", v: asString(demo.status) ?? "—" },
                { k: "run_id", v: asString(demo.run_id) ?? "—" },
                { k: "path", v: asString(demo.artifact_path) ?? "—" },
              ]}
            />
          )}
        </Pane>

        {root && <JsonDetails summary="Full /ui/research-os/status" data={root} />}
      </div>
    <div style={{ display: "none" }}>research_os_handoff_latest /research-handoff research_os_handoff_signoff_latest /research-handoff-signoff research_os_review_journal_latest /research-review-journal</div></main>
  );
}
