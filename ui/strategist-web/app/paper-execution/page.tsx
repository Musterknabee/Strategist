"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { SeverityBadge } from "@/components/terminal/SeverityBadge";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiPaperExecutionCockpit } from "@/hooks/useUiPaperExecution";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asBool, asNumber, asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

function countLabel(value: unknown): string {
  const n = asNumber(value);
  return n === undefined ? "0" : String(n);
}

export default function PaperExecutionPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const cockpit = useUiPaperExecutionCockpit();
  const root = cockpit.data ?? null;
  const summary = root ? asRecord(root.summary) : null;
  const broker = root ? asRecord(root.broker_status) : null;
  const intents = Array.isArray(root?.candidate_intents) ? root.candidate_intents : [];
  const dryRuns = Array.isArray(root?.dry_run_results) ? root.dry_run_results : [];
  const journal = Array.isArray(root?.journal_entries) ? root.journal_entries : [];
  const receipts = Array.isArray(root?.submission_receipts) ? root.submission_receipts : [];
  const orderStatuses = Array.isArray(root?.order_statuses) ? root.order_statuses : [];
  const executionTimeline = Array.isArray(root?.execution_timeline) ? root.execution_timeline : [];
  const timelineSummary = root?.execution_timeline_summary != null ? asRecord(root.execution_timeline_summary) : null;
  const evidenceBundles = Array.isArray(root?.evidence_bundles) ? root.evidence_bundles : [];
  const latestEvidenceBundle = root?.latest_evidence_bundle != null ? asRecord(root.latest_evidence_bundle) : null;
  const evidenceBundleVerifications = Array.isArray(root?.evidence_bundle_verifications) ? root.evidence_bundle_verifications : [];
  const latestEvidenceBundleVerification = root?.latest_evidence_bundle_verification != null ? asRecord(root.latest_evidence_bundle_verification) : null;
  const evidenceBundleDrifts = Array.isArray(root?.evidence_bundle_drifts) ? root.evidence_bundle_drifts : [];
  const latestEvidenceBundleDrift = root?.latest_evidence_bundle_drift != null ? asRecord(root.latest_evidence_bundle_drift) : null;
  const evidenceBundleRotations = Array.isArray(root?.evidence_bundle_rotations) ? root.evidence_bundle_rotations : [];
  const latestEvidenceBundleRotation = root?.latest_evidence_bundle_rotation != null ? asRecord(root.latest_evidence_bundle_rotation) : null;
  const evidenceBundleRotationExecutions = Array.isArray(root?.evidence_bundle_rotation_executions) ? root.evidence_bundle_rotation_executions : [];
  const latestEvidenceBundleRotationExecution = root?.latest_evidence_bundle_rotation_execution != null ? asRecord(root.latest_evidence_bundle_rotation_execution) : null;
  const evidenceBundleAttestations = Array.isArray(root?.evidence_bundle_attestations) ? root.evidence_bundle_attestations : [];
  const latestEvidenceBundleAttestation = root?.latest_evidence_bundle_attestation != null ? asRecord(root.latest_evidence_bundle_attestation) : null;
  const evidenceBundleAttestationVerifications = Array.isArray(root?.evidence_bundle_attestation_verifications) ? root.evidence_bundle_attestation_verifications : [];
  const latestEvidenceBundleAttestationVerification = root?.latest_evidence_bundle_attestation_verification != null ? asRecord(root.latest_evidence_bundle_attestation_verification) : null;
  const evidenceBundleClosures = Array.isArray(root?.evidence_bundle_closures) ? root.evidence_bundle_closures : [];
  const latestEvidenceBundleClosure = root?.latest_evidence_bundle_closure != null ? asRecord(root.latest_evidence_bundle_closure) : null;
  const evidenceBundleClosureVerifications = Array.isArray(root?.evidence_bundle_closure_verifications) ? root.evidence_bundle_closure_verifications : [];
  const latestEvidenceBundleClosureVerification = root?.latest_evidence_bundle_closure_verification != null ? asRecord(root.latest_evidence_bundle_closure_verification) : null;
  const evidenceBundleExportManifests = Array.isArray(root?.evidence_bundle_export_manifests) ? root.evidence_bundle_export_manifests : [];
  const latestEvidenceBundleExportManifest = root?.latest_evidence_bundle_export_manifest != null ? asRecord(root.latest_evidence_bundle_export_manifest) : null;
  const evidenceBundleExportVerifications = Array.isArray(root?.evidence_bundle_export_verifications) ? root.evidence_bundle_export_verifications : [];
  const latestEvidenceBundleExportVerification = root?.latest_evidence_bundle_export_verification != null ? asRecord(root.latest_evidence_bundle_export_verification) : null;
  const evidenceBundleRetentionReceipts = Array.isArray(root?.evidence_bundle_retention_receipts) ? root.evidence_bundle_retention_receipts : [];
  const latestEvidenceBundleRetentionReceipt = root?.latest_evidence_bundle_retention_receipt != null ? asRecord(root.latest_evidence_bundle_retention_receipt) : null;
  const evidenceBundleRetentionVerifications = Array.isArray(root?.evidence_bundle_retention_verifications) ? root.evidence_bundle_retention_verifications : [];
  const latestEvidenceBundleRetentionVerification = root?.latest_evidence_bundle_retention_verification != null ? asRecord(root.latest_evidence_bundle_retention_verification) : null;
  const evidenceBundleRetentionSignoffs = Array.isArray(root?.evidence_bundle_retention_signoffs) ? root.evidence_bundle_retention_signoffs : [];
  const latestEvidenceBundleRetentionSignoff = root?.latest_evidence_bundle_retention_signoff != null ? asRecord(root.latest_evidence_bundle_retention_signoff) : null;
  const evidenceBundleRetentionSignoffVerifications = Array.isArray(root?.evidence_bundle_retention_signoff_verifications) ? root.evidence_bundle_retention_signoff_verifications : [];
  const latestEvidenceBundleRetentionSignoffVerification = root?.latest_evidence_bundle_retention_signoff_verification != null ? asRecord(root.latest_evidence_bundle_retention_signoff_verification) : null;
  const evidenceBundleRetentionHandoffs = Array.isArray(root?.evidence_bundle_retention_handoffs) ? root.evidence_bundle_retention_handoffs : [];
  const latestEvidenceBundleRetentionHandoff = root?.latest_evidence_bundle_retention_handoff != null ? asRecord(root.latest_evidence_bundle_retention_handoff) : null;
  const evidenceBundleRetentionHandoffVerifications = Array.isArray(root?.evidence_bundle_retention_handoff_verifications) ? root.evidence_bundle_retention_handoff_verifications : [];
  const latestEvidenceBundleRetentionHandoffVerification = root?.latest_evidence_bundle_retention_handoff_verification != null ? asRecord(root.latest_evidence_bundle_retention_handoff_verification) : null;
  const evidenceBundleRetentionHandoffAcceptances = Array.isArray(root?.evidence_bundle_retention_handoff_acceptances) ? root.evidence_bundle_retention_handoff_acceptances : [];
  const latestEvidenceBundleRetentionHandoffAcceptance = root?.latest_evidence_bundle_retention_handoff_acceptance != null ? asRecord(root.latest_evidence_bundle_retention_handoff_acceptance) : null;
  const evidenceBundleRetentionHandoffAcceptanceVerifications = Array.isArray(root?.evidence_bundle_retention_handoff_acceptance_verifications) ? root.evidence_bundle_retention_handoff_acceptance_verifications : [];
  const latestEvidenceBundleRetentionHandoffAcceptanceVerification = root?.latest_evidence_bundle_retention_handoff_acceptance_verification != null ? asRecord(root.latest_evidence_bundle_retention_handoff_acceptance_verification) : null;
  const evidenceBundleRetentionCustodyRegisters = Array.isArray(root?.evidence_bundle_retention_custody_registers) ? root.evidence_bundle_retention_custody_registers : [];
  const latestEvidenceBundleRetentionCustodyRegister = root?.latest_evidence_bundle_retention_custody_register != null ? asRecord(root.latest_evidence_bundle_retention_custody_register) : null;
  const evidenceBundleRetentionCustodyRegisterVerifications = Array.isArray(root?.evidence_bundle_retention_custody_register_verifications) ? root.evidence_bundle_retention_custody_register_verifications : [];
  const latestEvidenceBundleRetentionCustodyRegisterVerification = root?.latest_evidence_bundle_retention_custody_register_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_register_verification) : null;
  const evidenceBundleRetentionCustodySeals = Array.isArray(root?.evidence_bundle_retention_custody_seals) ? root.evidence_bundle_retention_custody_seals : [];
  const latestEvidenceBundleRetentionCustodySeal = root?.latest_evidence_bundle_retention_custody_seal != null ? asRecord(root.latest_evidence_bundle_retention_custody_seal) : null;
  const evidenceBundleRetentionCustodySealVerifications = Array.isArray(root?.evidence_bundle_retention_custody_seal_verifications) ? root.evidence_bundle_retention_custody_seal_verifications : [];
  const latestEvidenceBundleRetentionCustodySealVerification = root?.latest_evidence_bundle_retention_custody_seal_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_seal_verification) : null;
  const evidenceBundleRetentionCustodyAudits = Array.isArray(root?.evidence_bundle_retention_custody_audits) ? root.evidence_bundle_retention_custody_audits : [];
  const latestEvidenceBundleRetentionCustodyAudit = root?.latest_evidence_bundle_retention_custody_audit != null ? asRecord(root.latest_evidence_bundle_retention_custody_audit) : null;
  const evidenceBundleRetentionCustodyAuditVerifications = Array.isArray(root?.evidence_bundle_retention_custody_audit_verifications) ? root.evidence_bundle_retention_custody_audit_verifications : [];
  const latestEvidenceBundleRetentionCustodyAuditVerification = root?.latest_evidence_bundle_retention_custody_audit_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_audit_verification) : null;
  const evidenceBundleRetentionCustodyContinuities = Array.isArray(root?.evidence_bundle_retention_custody_continuities) ? root.evidence_bundle_retention_custody_continuities : [];
  const latestEvidenceBundleRetentionCustodyContinuity = root?.latest_evidence_bundle_retention_custody_continuity != null ? asRecord(root.latest_evidence_bundle_retention_custody_continuity) : null;
  const evidenceBundleRetentionCustodyContinuityVerifications = Array.isArray(root?.evidence_bundle_retention_custody_continuity_verifications) ? root.evidence_bundle_retention_custody_continuity_verifications : [];
  const latestEvidenceBundleRetentionCustodyContinuityVerification = root?.latest_evidence_bundle_retention_custody_continuity_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_continuity_verification) : null;
  const evidenceBundleRetentionCustodyReviews = Array.isArray(root?.evidence_bundle_retention_custody_reviews) ? root.evidence_bundle_retention_custody_reviews : [];
  const latestEvidenceBundleRetentionCustodyReview = root?.latest_evidence_bundle_retention_custody_review != null ? asRecord(root.latest_evidence_bundle_retention_custody_review) : null;
  const evidenceBundleRetentionCustodyReviewVerifications = Array.isArray(root?.evidence_bundle_retention_custody_review_verifications) ? root.evidence_bundle_retention_custody_review_verifications : [];
  const latestEvidenceBundleRetentionCustodyReviewVerification = root?.latest_evidence_bundle_retention_custody_review_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_review_verification) : null;
  const evidenceBundleRetentionCustodyRenewals = Array.isArray(root?.evidence_bundle_retention_custody_renewals) ? root.evidence_bundle_retention_custody_renewals : [];
  const latestEvidenceBundleRetentionCustodyRenewal = root?.latest_evidence_bundle_retention_custody_renewal != null ? asRecord(root.latest_evidence_bundle_retention_custody_renewal) : null;
  const evidenceBundleRetentionCustodyRenewalVerifications = Array.isArray(root?.evidence_bundle_retention_custody_renewal_verifications) ? root.evidence_bundle_retention_custody_renewal_verifications : [];
  const latestEvidenceBundleRetentionCustodyRenewalVerification = root?.latest_evidence_bundle_retention_custody_renewal_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_renewal_verification) : null;
  const evidenceBundleRetentionCustodySchedules = Array.isArray(root?.evidence_bundle_retention_custody_schedules) ? root.evidence_bundle_retention_custody_schedules : [];
  const latestEvidenceBundleRetentionCustodySchedule = root?.latest_evidence_bundle_retention_custody_schedule != null ? asRecord(root.latest_evidence_bundle_retention_custody_schedule) : null;
  const evidenceBundleRetentionCustodyScheduleVerifications = Array.isArray(root?.evidence_bundle_retention_custody_schedule_verifications) ? root.evidence_bundle_retention_custody_schedule_verifications : [];
  const latestEvidenceBundleRetentionCustodyScheduleVerification = root?.latest_evidence_bundle_retention_custody_schedule_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_schedule_verification) : null;
  const evidenceBundleRetentionCustodyNotices = Array.isArray(root?.evidence_bundle_retention_custody_notices) ? root.evidence_bundle_retention_custody_notices : [];
  const latestEvidenceBundleRetentionCustodyNotice = root?.latest_evidence_bundle_retention_custody_notice != null ? asRecord(root.latest_evidence_bundle_retention_custody_notice) : null;
  const evidenceBundleRetentionCustodyNoticeVerifications = Array.isArray(root?.evidence_bundle_retention_custody_notice_verifications) ? root.evidence_bundle_retention_custody_notice_verifications : [];
  const latestEvidenceBundleRetentionCustodyNoticeVerification = root?.latest_evidence_bundle_retention_custody_notice_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_notice_verification) : null;
  const evidenceBundleRetentionCustodyAcknowledgments = Array.isArray(root?.evidence_bundle_retention_custody_acknowledgments) ? root.evidence_bundle_retention_custody_acknowledgments : [];
  const latestEvidenceBundleRetentionCustodyAcknowledgment = root?.latest_evidence_bundle_retention_custody_acknowledgment != null ? asRecord(root.latest_evidence_bundle_retention_custody_acknowledgment) : null;
  const evidenceBundleRetentionCustodyAcknowledgmentVerifications = Array.isArray(root?.evidence_bundle_retention_custody_acknowledgment_verifications) ? root.evidence_bundle_retention_custody_acknowledgment_verifications : [];
  const latestEvidenceBundleRetentionCustodyAcknowledgmentVerification = root?.latest_evidence_bundle_retention_custody_acknowledgment_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_acknowledgment_verification) : null;
  const evidenceBundleRetentionCustodyCompletions = Array.isArray(root?.evidence_bundle_retention_custody_completions) ? root.evidence_bundle_retention_custody_completions : [];
  const latestEvidenceBundleRetentionCustodyCompletion = root?.latest_evidence_bundle_retention_custody_completion != null ? asRecord(root.latest_evidence_bundle_retention_custody_completion) : null;
  const evidenceBundleRetentionCustodyCompletionVerifications = Array.isArray(root?.evidence_bundle_retention_custody_completion_verifications) ? root.evidence_bundle_retention_custody_completion_verifications : [];
  const latestEvidenceBundleRetentionCustodyCompletionVerification = root?.latest_evidence_bundle_retention_custody_completion_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_completion_verification) : null;
  const evidenceBundleRetentionCustodyCloseouts = Array.isArray(root?.evidence_bundle_retention_custody_closeouts) ? root.evidence_bundle_retention_custody_closeouts : [];
  const latestEvidenceBundleRetentionCustodyCloseout = root?.latest_evidence_bundle_retention_custody_closeout != null ? asRecord(root.latest_evidence_bundle_retention_custody_closeout) : null;
  const evidenceBundleRetentionCustodyCloseoutVerifications = Array.isArray(root?.evidence_bundle_retention_custody_closeout_verifications) ? root.evidence_bundle_retention_custody_closeout_verifications : [];
  const latestEvidenceBundleRetentionCustodyCloseoutVerification = root?.latest_evidence_bundle_retention_custody_closeout_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_closeout_verification) : null;
  const evidenceBundleRetentionCustodyArchives = Array.isArray(root?.evidence_bundle_retention_custody_archives) ? root.evidence_bundle_retention_custody_archives : [];
  const latestEvidenceBundleRetentionCustodyArchive = root?.latest_evidence_bundle_retention_custody_archive != null ? asRecord(root.latest_evidence_bundle_retention_custody_archive) : null;
  const evidenceBundleRetentionCustodyArchiveVerifications = Array.isArray(root?.evidence_bundle_retention_custody_archive_verifications) ? root.evidence_bundle_retention_custody_archive_verifications : [];
  const latestEvidenceBundleRetentionCustodyArchiveVerification = root?.latest_evidence_bundle_retention_custody_archive_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_archive_verification) : null;
  const evidenceBundleRetentionCustodyRetrievals = Array.isArray(root?.evidence_bundle_retention_custody_retrievals) ? root.evidence_bundle_retention_custody_retrievals : [];
  const latestEvidenceBundleRetentionCustodyRetrieval = root?.latest_evidence_bundle_retention_custody_retrieval != null ? asRecord(root.latest_evidence_bundle_retention_custody_retrieval) : null;
  const evidenceBundleRetentionCustodyRetrievalVerifications = Array.isArray(root?.evidence_bundle_retention_custody_retrieval_verifications) ? root.evidence_bundle_retention_custody_retrieval_verifications : [];
  const latestEvidenceBundleRetentionCustodyRetrievalVerification = root?.latest_evidence_bundle_retention_custody_retrieval_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_retrieval_verification) : null;
  const evidenceBundleRetentionCustodyReturns = Array.isArray(root?.evidence_bundle_retention_custody_returns) ? root.evidence_bundle_retention_custody_returns : [];
  const latestEvidenceBundleRetentionCustodyReturn = root?.latest_evidence_bundle_retention_custody_return != null ? asRecord(root.latest_evidence_bundle_retention_custody_return) : null;
  const evidenceBundleRetentionCustodyReturnVerifications = Array.isArray(root?.evidence_bundle_retention_custody_return_verifications) ? root.evidence_bundle_retention_custody_return_verifications : [];
  const latestEvidenceBundleRetentionCustodyReturnVerification = root?.latest_evidence_bundle_retention_custody_return_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_return_verification) : null;
  const evidenceBundleRetentionCustodyRedeposits = Array.isArray(root?.evidence_bundle_retention_custody_redeposits) ? root.evidence_bundle_retention_custody_redeposits : [];
  const latestEvidenceBundleRetentionCustodyRedeposit = root?.latest_evidence_bundle_retention_custody_redeposit != null ? asRecord(root.latest_evidence_bundle_retention_custody_redeposit) : null;
  const evidenceBundleRetentionCustodyRedepositVerifications = Array.isArray(root?.evidence_bundle_retention_custody_redeposit_verifications) ? root.evidence_bundle_retention_custody_redeposit_verifications : [];
  const latestEvidenceBundleRetentionCustodyRedepositVerification = root?.latest_evidence_bundle_retention_custody_redeposit_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_redeposit_verification) : null;
  const evidenceBundleRetentionCustodyInventories = Array.isArray(root?.evidence_bundle_retention_custody_inventories) ? root.evidence_bundle_retention_custody_inventories : [];
  const latestEvidenceBundleRetentionCustodyInventory = root?.latest_evidence_bundle_retention_custody_inventory != null ? asRecord(root.latest_evidence_bundle_retention_custody_inventory) : null;
  const evidenceBundleRetentionCustodyInventoryVerifications = Array.isArray(root?.evidence_bundle_retention_custody_inventory_verifications) ? root.evidence_bundle_retention_custody_inventory_verifications : [];
  const latestEvidenceBundleRetentionCustodyInventoryVerification = root?.latest_evidence_bundle_retention_custody_inventory_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_inventory_verification) : null;
  const evidenceBundleRetentionCustodyReconciliations = Array.isArray(root?.evidence_bundle_retention_custody_reconciliations) ? root.evidence_bundle_retention_custody_reconciliations : [];
  const latestEvidenceBundleRetentionCustodyReconciliation = root?.latest_evidence_bundle_retention_custody_reconciliation != null ? asRecord(root.latest_evidence_bundle_retention_custody_reconciliation) : null;
  const evidenceBundleRetentionCustodyReconciliationVerifications = Array.isArray(root?.evidence_bundle_retention_custody_reconciliation_verifications) ? root.evidence_bundle_retention_custody_reconciliation_verifications : [];
  const latestEvidenceBundleRetentionCustodyReconciliationVerification = root?.latest_evidence_bundle_retention_custody_reconciliation_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_reconciliation_verification) : null;
  const evidenceBundleRetentionCustodyCertifications = Array.isArray(root?.evidence_bundle_retention_custody_certifications) ? root.evidence_bundle_retention_custody_certifications : [];
  const latestEvidenceBundleRetentionCustodyCertification = root?.latest_evidence_bundle_retention_custody_certification != null ? asRecord(root.latest_evidence_bundle_retention_custody_certification) : null;
  const evidenceBundleRetentionCustodyCertificationVerifications = Array.isArray(root?.evidence_bundle_retention_custody_certification_verifications) ? root.evidence_bundle_retention_custody_certification_verifications : [];
  const latestEvidenceBundleRetentionCustodyCertificationVerification = root?.latest_evidence_bundle_retention_custody_certification_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_certification_verification) : null;
  const evidenceBundleRetentionCustodyAttestations = Array.isArray(root?.evidence_bundle_retention_custody_attestations) ? root.evidence_bundle_retention_custody_attestations : [];
  const latestEvidenceBundleRetentionCustodyAttestation = root?.latest_evidence_bundle_retention_custody_attestation != null ? asRecord(root.latest_evidence_bundle_retention_custody_attestation) : null;
  const evidenceBundleRetentionCustodyAttestationVerifications = Array.isArray(root?.evidence_bundle_retention_custody_attestation_verifications) ? root.evidence_bundle_retention_custody_attestation_verifications : [];
  const latestEvidenceBundleRetentionCustodyAttestationVerification = root?.latest_evidence_bundle_retention_custody_attestation_verification != null ? asRecord(root.latest_evidence_bundle_retention_custody_attestation_verification) : null;
  const latestReceipt = receipts[0] ?? null;
  const latestOrderStatus = orderStatuses[0] ?? null;
  const latest = root?.latest_tracking != null ? asRecord(root.latest_tracking) : null;
  const selectedIntent = root?.selected_intent != null ? asRecord(root.selected_intent) : null;
  const freshness = root?.freshness_gate != null ? asRecord(root.freshness_gate) : null;
  const positionSnapshot = root?.account_position_snapshot != null ? asRecord(root.account_position_snapshot) : null;
  const positionReconciliation = root?.position_reconciliation != null ? asRecord(root.position_reconciliation) : null;
  const selectedPreview = selectedIntent?.selected_intent != null ? asRecord(selectedIntent.selected_intent) : null;
  const manifest = latest?.manifest != null ? asRecord(latest.manifest) : null;
  const candidate = manifest?.candidate != null ? asRecord(manifest.candidate) : null;

  const statusSeverity = (() => {
    if (!summary) return "neutral" as const;
    if (asNumber(summary.dry_run_blocked_count) && Number(summary.dry_run_blocked_count) > 0) return "warn" as const;
    if (asBool(summary.broker_ready)) return "ok" as const;
    return "warn" as const;
  })();

  const tape: TapeLine[] = useMemo(() => {
    return [
      {
        id: "paper-exec",
        ts: root?.generated_at_utc,
        severity: asNumber(summary?.dry_run_blocked_count) ? "warn" : "ok",
        text: `PAPER_EXEC ${asString(summary?.broker_policy_status) ?? "UNKNOWN"}`,
      },
    ];
  }, [root, summary]);

  useTerminalPageBind(tape, []);

  if (!config.ok) {
    return (
      <div className="term-page cockpit-page">
        <div className="term-page__banner">{config.error.message}</div>
      </div>
    );
  }

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Paper execution cockpit</h1>
          <p className="muted">Paper-only execution preview · CLI-only submission · no browser orders · no live trading</p>
        </div>
      </div>

      <div className="term-page__banner" style={{ marginBottom: "0.75rem", fontSize: "12px", lineHeight: 1.45 }}>
        <strong>Authority boundary</strong> — this page validates candidate paper order intent and shows journal evidence. It cannot submit broker orders.
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}>
        <Pane title="Cockpit status" dense onInspect={() => openInspector({ title: "Paper execution cockpit", rawJson: root ?? {} })}>
          {cockpit.isLoading ? (
            <p className="muted">Loading…</p>
          ) : !root ? (
            <p className="muted">No payload.</p>
          ) : (
            <TermKV
              rows={[
                { k: "broker_policy", v: <StatusBadge raw={asString(summary?.broker_policy_status) ?? "UNKNOWN"} /> },
                { k: "submission", v: asString(summary?.paper_submission_capability) ?? "CLI_ONLY" },
                { k: "tracking", v: asBool(summary?.tracking_present) ? "present" : "missing" },
                { k: "intent_count", v: countLabel(summary?.candidate_intent_count) },
                { k: "dry_run_ok", v: countLabel(summary?.dry_run_ok_count) },
                { k: "dry_run_blocked", v: countLabel(summary?.dry_run_blocked_count) },
                { k: "journal_entries", v: countLabel(summary?.journal_entry_count) },
                { k: "dry_run_artifacts", v: countLabel(summary?.dry_run_artifact_count) },
                { k: "submission_artifacts", v: countLabel(summary?.submission_artifact_count) },
                { k: "submission_receipts", v: countLabel(summary?.submission_receipt_count) },
                { k: "latest_submission_guard", v: <StatusBadge raw={asString(summary?.latest_submission_guard_status) ?? "UNKNOWN"} /> },
                { k: "latest_submission_freshness", v: <StatusBadge raw={asString(summary?.latest_submission_evidence_freshness_status) ?? "UNKNOWN"} /> },
                { k: "submission_guard_blockers", v: countLabel(summary?.submission_guard_blocker_count) },
                { k: "order_status_artifacts", v: countLabel(summary?.order_status_artifact_count) },
                { k: "latest_order_status", v: <StatusBadge raw={asString(summary?.latest_order_status) ?? "UNKNOWN"} /> },
                { k: "latest_order_filled_qty", v: String(asNumber(summary?.latest_order_status_filled_qty) ?? "—") },
                { k: "order_status_blockers", v: countLabel(summary?.order_status_blocker_count) },
                { k: "position_snapshots", v: countLabel(summary?.position_snapshot_count) },
                { k: "position_reconciliation", v: <StatusBadge raw={asString(summary?.position_reconciliation_status) ?? "UNKNOWN"} /> },
                { k: "position_recon_blockers", v: countLabel(summary?.position_reconciliation_blocker_count) },
                { k: "timeline_status", v: <StatusBadge raw={asString(summary?.timeline_sequence_status) ?? "EMPTY"} /> },
                { k: "timeline_events", v: countLabel(summary?.timeline_event_count) },
                { k: "timeline_trusted", v: countLabel(summary?.timeline_trusted_event_count) },
                { k: "timeline_blockers", v: countLabel(summary?.timeline_blocker_count) },
                { k: "bundle_trust", v: <StatusBadge raw={asString(summary?.latest_evidence_bundle_trust_banner) ?? "NO_BUNDLE"} /> },
                { k: "bundle_status", v: <StatusBadge raw={asString(summary?.latest_evidence_bundle_status) ?? "NO_BUNDLE"} /> },
                { k: "bundle_count", v: countLabel(summary?.evidence_bundle_count) },
                { k: "bundle_blockers", v: countLabel(summary?.evidence_bundle_blocker_count) },
                { k: "bundle_verify", v: <StatusBadge raw={asString(summary?.latest_evidence_bundle_verification_status) ?? "NO_VERIFICATION"} /> },
                { k: "verify_blockers", v: countLabel(summary?.evidence_bundle_verification_blocker_count) },
                { k: "bundle_drift", v: <StatusBadge raw={asString(summary?.latest_evidence_bundle_drift_status) ?? "NO_DRIFT_CHECK"} /> },
                { k: "drift_blockers", v: countLabel(summary?.evidence_bundle_drift_blocker_count) },
                { k: "bundle_attestation", v: <StatusBadge raw={asString(summary?.latest_evidence_bundle_attestation_status) ?? "NO_ATTESTATION"} /> },
                { k: "attestation_verify", v: <StatusBadge raw={asString(summary?.latest_evidence_bundle_attestation_verification_status) ?? "NO_ATTESTATION_VERIFICATION"} /> },
                { k: "attestation_verify_blockers", v: countLabel(summary?.evidence_bundle_attestation_verification_blocker_count) },
                { k: "bundle_closure", v: <StatusBadge raw={asString(summary?.latest_evidence_bundle_closure_status) ?? "NO_CLOSURE"} /> },
                { k: "closure_blockers", v: countLabel(summary?.evidence_bundle_closure_blocker_count) },
                { k: "closure_verify", v: <StatusBadge raw={asString(summary?.latest_evidence_bundle_closure_verification_status) ?? "NO_CLOSURE_VERIFICATION"} /> },
                { k: "closure_verify_blockers", v: countLabel(summary?.evidence_bundle_closure_verification_blocker_count) },
                { k: "export_manifest", v: <StatusBadge raw={asString(summary?.latest_evidence_bundle_export_manifest_status) ?? "NO_EXPORT_MANIFEST"} /> },
                { k: "export_blockers", v: countLabel(summary?.evidence_bundle_export_manifest_blocker_count) },
                { k: "export_verify", v: <StatusBadge raw={asString(summary?.latest_evidence_bundle_export_verification_status) ?? "NO_EXPORT_VERIFICATION"} /> },
                { k: "export_verify_blockers", v: countLabel(summary?.evidence_bundle_export_verification_blocker_count) },
                { k: "latest_broker_order", v: asString(summary?.latest_submission_broker_order_id) ?? "—" },
                { k: "selected_intents", v: countLabel(summary?.selected_intent_count) },
                { k: "selected_tracking", v: asString(summary?.latest_selected_tracking_id) ?? "—" },
                { k: "selected_replay", v: asString(summary?.selected_intent_dry_run_status) ?? "NO_SELECTED_INTENT" },
                { k: "replay_match", v: String(summary?.selected_intent_dry_run_match ?? "—") },
                { k: "freshness", v: <StatusBadge raw={asString(summary?.evidence_freshness_status) ?? "UNKNOWN"} /> },
                { k: "freshness_blockers", v: countLabel(summary?.evidence_freshness_blocker_count) },
                { k: "latest_dry_run", v: asString(summary?.latest_dry_run_artifact_at_utc) ?? "—" },
                { k: "latest_tracking_id", v: asString(summary?.latest_tracking_id) ?? "—" },
                { k: "latest_strategy_id", v: asString(summary?.latest_strategy_id) ?? "—" },
              ]}
            />
          )}
        </Pane>

        <Pane title="Broker policy" dense onInspect={() => openInspector({ title: "Broker status", rawJson: broker ?? {} })}>
          <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
            <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap", alignItems: "center" }}>
              <SeverityBadge severity={statusSeverity}>{asString(summary?.broker_policy_status) ?? "UNKNOWN"}</SeverityBadge>
              <SeverityBadge severity="neutral">browser orders disabled</SeverityBadge>
              <SeverityBadge severity="neutral">live blocked</SeverityBadge>
            </div>
            <TermKV
              rows={[
                { k: "broker_id", v: asString(broker?.broker_id) ?? "alpaca_paper" },
                { k: "artifact", v: root?.broker_artifact_path ?? "env-derived/no artifact" },
                { k: "warnings", v: asStringArray(broker?.warnings).join("; ") || "—" },
                { k: "blockers", v: asStringArray(broker?.blockers).join("; ") || "—" },
              ]}
            />
          </div>
        </Pane>

        <Pane title="Evidence freshness gate" dense onInspect={() => openInspector({ title: "Paper execution freshness gate", rawJson: freshness ?? {} })}>
          {!freshness ? (
            <p className="muted">No freshness gate payload.</p>
          ) : (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap", alignItems: "center" }}>
                <StatusBadge raw={asString(freshness.status) ?? "UNKNOWN"} />
                <SeverityBadge severity={asString(freshness.status) === "FRESH" ? "ok" : "warn"}>evidence age checked</SeverityBadge>
              </div>
              <TermKV
                rows={[
                  { k: "selected_age_h", v: String(asNumber(freshness.selected_intent_age_hours) ?? "—") },
                  { k: "linked_dry_run_age_h", v: String(asNumber(freshness.latest_linked_dry_run_age_hours) ?? "—") },
                  { k: "tracking_signal_age_h", v: String(asNumber(freshness.latest_tracking_signal_age_hours) ?? "—") },
                  { k: "broker_policy_age_h", v: String(asNumber(freshness.broker_policy_age_hours) ?? "—") },
                  { k: "stale_reasons", v: asStringArray(freshness.stale_reasons).join("; ") || "—" },
                  { k: "blockers", v: asStringArray(freshness.blockers).join("; ") || "—" },
                  { k: "warnings", v: asStringArray(freshness.warnings).join("; ") || "—" },
                ]}
              />
            </div>
          )}
        </Pane>

        <Pane title="Selected dry-run target" dense onInspect={() => openInspector({ title: "Selected paper intent", rawJson: selectedIntent ?? {} })}>
          {!selectedIntent ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No selected intent artifact yet. Select one before durable dry-run evidence.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker select-intent --tracking-id &lt;tracking_id&gt; --symbol &lt;symbol&gt; --qty &lt;qty&gt; --side &lt;buy|sell&gt;
              </pre>
            </div>
          ) : (
            <TermKV
              rows={[
                { k: "tracking_id", v: asString(selectedIntent.tracking_id) ?? "—" },
                { k: "strategy_id", v: asString(selectedIntent.strategy_id) ?? "—" },
                { k: "symbol", v: asString(selectedPreview?.symbol) ?? "—" },
                { k: "side", v: asString(selectedPreview?.side) ?? "—" },
                { k: "qty", v: String(selectedPreview?.qty ?? "—") },
                { k: "selected_by", v: asString(selectedIntent.selected_by) ?? "operator" },
                { k: "reason", v: asString(selectedIntent.selection_reason) ?? "—" },
                { k: "artifact_sha", v: (asString(selectedIntent.artifact_sha256) ?? "—").slice(0, 16) },
                { k: "dry_run_cmd", v: asString(root?.dry_run_command_hint) ?? asString(selectedIntent.dry_run_command_hint) ?? "—" },
                { k: "replay_cmd", v: "strategy-validator-paper-broker dry-run-selected-intent --tracking-id " + (asString(selectedIntent.tracking_id) ?? "<tracking_id>") },
              ]}
            />
          )}
        </Pane>

        <Pane title="Latest tracking source" dense onInspect={() => openInspector({ title: "Latest paper tracking", rawJson: latest ?? {} })}>
          {!latest ? (
            <p className="muted">No paper tracking bundle. Enroll a candidate before execution previews.</p>
          ) : (
            <TermKV
              rows={[
                { k: "tracking_id", v: asString(latest.tracking_id) ?? "—" },
                { k: "strategy_id", v: asString(candidate?.strategy_id) ?? "—" },
                { k: "batch_id", v: asString(candidate?.batch_id) ?? "—" },
                { k: "paper_posture", v: asString(candidate?.paper_posture) ?? "—" },
                { k: "lifecycle_state", v: asString(latest.lifecycle_state) ?? "—" },
                { k: "promotion_ready", v: String(Boolean(latest.promotion_review_ready)) },
              ]}
            />
          )}
        </Pane>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr", marginTop: "0.75rem" }}>
        <Pane title="Candidate paper intent preview" dense onInspect={() => openInspector({ title: "Candidate intents", rawJson: { intents, dryRuns } })}>
          {intents.length === 0 ? (
            <p className="muted">No candidate intent preview available.</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table className="dense-table">
                <thead>
                  <tr>
                    <th>Tracking</th>
                    <th>Strategy</th>
                    <th>Symbol</th>
                    <th>Side</th>
                    <th>Qty</th>
                    <th>Source</th>
                    <th>Confidence</th>
                    <th>Warnings</th>
                  </tr>
                </thead>
                <tbody>
                  {intents.map((intent, index) => (
                    <tr key={`${intent.tracking_id ?? "intent"}-${index}`}>
                      <td>{intent.tracking_id ?? "—"}</td>
                      <td>{intent.strategy_id ?? "—"}</td>
                      <td>{intent.symbol}</td>
                      <td>{intent.side}</td>
                      <td>{intent.qty}</td>
                      <td>{intent.source}</td>
                      <td>{intent.confidence}</td>
                      <td>{intent.warnings.slice(0, 3).join("; ") || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-paper-broker select-intent --tracking-id &lt;tracking_id&gt; --symbol &lt;symbol&gt; --qty &lt;qty&gt; --side &lt;buy|sell&gt;
            {"\n"}strategy-validator-paper-broker dry-run-selected-intent --tracking-id &lt;tracking_id&gt;
            {"\n"}strategy-validator-paper-broker dry-run-order --tracking-id &lt;tracking_id&gt; --symbol &lt;symbol&gt; --qty &lt;qty&gt; --side &lt;buy|sell&gt;
          </pre>
        </Pane>

        <Pane title="Dry-run validation results" dense onInspect={() => openInspector({ title: "Dry-run results", rawJson: { dryRuns } })}>
          {dryRuns.length === 0 ? (
            <p className="muted">No dry-run validation yet.</p>
          ) : (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              {dryRuns.map((row, index) => {
                const rec = asRecord(row) ?? {};
                const intent = rec.intent != null ? asRecord(rec.intent) : null;
                return (
                  <div key={index} className="panel" style={{ padding: "0.6rem" }}>
                    <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center" }}>
                      <SeverityBadge severity={rec.ok === true ? "ok" : "warn"}>{rec.ok === true ? "DRY_RUN_OK" : "DRY_RUN_BLOCKED"}</SeverityBadge>
                      <span>{asString(intent?.symbol) ?? "—"}</span>
                      <span className="muted">{asString(intent?.side) ?? "—"}</span>
                      <span className="muted">qty {typeof intent?.qty === "number" ? intent.qty : "—"}</span>
                    </div>
                    <JsonDetails summary="dry-run JSON" data={rec} />
                  </div>
                );
              })}
            </div>
          )}
        </Pane>

        <Pane title="Order status refresh" dense onInspect={() => openInspector({ title: "Paper order statuses", rawJson: { orderStatuses, latestOrderStatus } })}>
          {orderStatuses.length === 0 ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No broker order-status refresh artifacts yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker refresh-order-status --tracking-id &lt;tracking_id&gt; --allow-network
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestOrderStatus ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={latestOrderStatus.status ?? "UNKNOWN"} />
                    <SeverityBadge severity={latestOrderStatus.ok === true ? "ok" : "warn"}>{latestOrderStatus.ok === true ? "STATUS_OK" : "STATUS_ATTENTION"}</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: latestOrderStatus.tracking_id ?? "—" },
                      { k: "broker_order", v: latestOrderStatus.broker_order_id ?? "—" },
                      { k: "status", v: latestOrderStatus.status ?? "—" },
                      { k: "filled_qty", v: String(latestOrderStatus.filled_qty ?? "—") },
                      { k: "symbol", v: latestOrderStatus.symbol ?? "—" },
                      { k: "side", v: latestOrderStatus.side ?? "—" },
                      { k: "generated_at", v: latestOrderStatus.generated_at_utc ?? "—" },
                      { k: "artifact_sha", v: (latestOrderStatus.artifact_sha256 ?? "—").slice(0, 16) },
                      { k: "submission_sha", v: (latestOrderStatus.source_submission_artifact_sha256 ?? "—").slice(0, 16) },
                      { k: "blockers", v: latestOrderStatus.blockers.join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Tracking</th>
                      <th>Status</th>
                      <th>OK</th>
                      <th>Order</th>
                      <th>Filled</th>
                      <th>Symbol</th>
                      <th>Blockers</th>
                      <th>Artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orderStatuses.slice(0, 20).map((status, index) => (
                      <tr key={`${status.artifact_path ?? "order-status"}-${index}`}>
                        <td>{status.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={status.status ?? "UNKNOWN"} /></td>
                        <td>{String(status.ok ?? "—")}</td>
                        <td>{status.broker_order_id ?? "—"}</td>
                        <td>{status.filled_qty ?? "—"}</td>
                        <td>{status.symbol ?? "—"}</td>
                        <td>{status.blockers.length}</td>
                        <td>{status.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>

        <Pane title="Account / position reconciliation" dense onInspect={() => openInspector({ title: "Paper account position reconciliation", rawJson: { positionSnapshot, positionReconciliation } })}>
          {!positionReconciliation ? (
            <p className="muted">No reconciliation payload.</p>
          ) : (
            <div style={{ display: "grid", gap: "0.6rem", fontSize: "11px" }}>
              <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center" }}>
                <StatusBadge raw={asString(positionReconciliation.status) ?? "UNKNOWN"} />
                <SeverityBadge severity={asNumber(positionReconciliation.reconciliation_blocker_count) ? "warn" : "neutral"}>broker-state check</SeverityBadge>
              </div>
              <TermKV
                rows={[
                  { k: "tracking_id", v: asString(positionReconciliation.tracking_id) ?? "—" },
                  { k: "symbol", v: asString(positionReconciliation.symbol) ?? "—" },
                  { k: "side", v: asString(positionReconciliation.side) ?? "—" },
                  { k: "submitted_qty", v: String(asNumber(positionReconciliation.submitted_qty) ?? "—") },
                  { k: "filled_qty", v: String(asNumber(positionReconciliation.filled_qty) ?? "—") },
                  { k: "expected_delta", v: String(asNumber(positionReconciliation.expected_position_delta_qty) ?? "—") },
                  { k: "observed_position", v: String(asNumber(positionReconciliation.observed_position_qty) ?? "—") },
                  { k: "broker_status", v: asString(positionReconciliation.broker_status) ?? "—" },
                  { k: "snapshot_age_h", v: String(asNumber(positionReconciliation.account_position_snapshot_age_hours) ?? "—") },
                  { k: "snapshot_sha", v: (asString(positionReconciliation.account_position_snapshot_sha256) ?? "—").slice(0, 16) },
                  { k: "blockers", v: asStringArray(positionReconciliation.blockers).join("; ") || "—" },
                  { k: "warnings", v: asStringArray(positionReconciliation.warnings).join("; ") || "—" },
                ]}
              />
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker snapshot-account-positions --allow-network
              </pre>
              {positionSnapshot ? (
                <JsonDetails summary={`snapshot positions (${countLabel(positionSnapshot.position_count)})`} data={positionSnapshot} />
              ) : null}
            </div>
          )}
        </Pane>

        <Pane title="Submission receipt viewer" dense onInspect={() => openInspector({ title: "Paper submission receipts", rawJson: { receipts, latestReceipt } })}>
          {receipts.length === 0 ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No guarded paper submission receipts yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker submit-paper-order --tracking-id &lt;tracking_id&gt; --symbol &lt;symbol&gt; --qty &lt;qty&gt; --side &lt;buy|sell&gt;
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestReceipt ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={latestReceipt.guard_status ?? "UNKNOWN"} />
                    <StatusBadge raw={latestReceipt.evidence_freshness_status ?? "UNKNOWN"} />
                    <SeverityBadge severity={latestReceipt.result_ok === true ? "ok" : "warn"}>{latestReceipt.result_ok === true ? "RESULT_OK" : "RESULT_ATTENTION"}</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: latestReceipt.tracking_id },
                      { k: "broker_order", v: latestReceipt.broker_order_id ?? "—" },
                      { k: "broker_status", v: latestReceipt.broker_status ?? "—" },
                      { k: "policy_status", v: latestReceipt.policy_status ?? "—" },
                      { k: "generated_at", v: latestReceipt.generated_at_utc ?? "—" },
                      { k: "artifact_sha", v: (latestReceipt.artifact_sha256 ?? "—").slice(0, 16) },
                      { k: "selected_sha", v: (latestReceipt.selected_intent_artifact_sha256 ?? "—").slice(0, 16) },
                      { k: "dry_run_sha", v: (latestReceipt.linked_dry_run_artifact_sha256 ?? "—").slice(0, 16) },
                      { k: "intent_match", v: String(latestReceipt.submission_intent_matches_selection ?? "—") },
                      { k: "dry_run_match", v: String(latestReceipt.linked_dry_run_matches_selection ?? "—") },
                      { k: "dry_run_ok", v: String(latestReceipt.linked_dry_run_ok ?? "—") },
                      { k: "guard_blockers", v: String(latestReceipt.guard_blocker_count ?? 0) },
                      { k: "refresh_status_cmd", v: "strategy-validator-paper-broker refresh-order-status --tracking-id " + latestReceipt.tracking_id + " --allow-network" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Tracking</th>
                      <th>Guard</th>
                      <th>Freshness</th>
                      <th>Broker</th>
                      <th>Order</th>
                      <th>Selection match</th>
                      <th>Dry-run match</th>
                      <th>Blockers</th>
                      <th>Artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {receipts.slice(0, 20).map((receipt, index) => (
                      <tr key={`${receipt.artifact_path}-${index}`}>
                        <td>{receipt.tracking_id}</td>
                        <td><StatusBadge raw={receipt.guard_status ?? "UNKNOWN"} /></td>
                        <td><StatusBadge raw={receipt.evidence_freshness_status ?? "UNKNOWN"} /></td>
                        <td>{receipt.broker_status ?? "—"}</td>
                        <td>{receipt.broker_order_id ?? "—"}</td>
                        <td>{String(receipt.submission_intent_matches_selection ?? "—")}</td>
                        <td>{String(receipt.linked_dry_run_matches_selection ?? "—")}</td>
                        <td>{receipt.guard_blocker_count ?? 0}</td>
                        <td>{receipt.artifact_path}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>


        <Pane title="Paper execution timeline" dense onInspect={() => openInspector({ title: "Paper execution timeline", rawJson: { timelineSummary, executionTimeline } })}>
          {executionTimeline.length === 0 ? (
            <p className="muted">No paper execution timeline events found yet.</p>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", fontSize: "11px" }}>
                <StatusBadge raw={asString(timelineSummary?.sequence_status) ?? "EMPTY"} />
                <SeverityBadge severity={asNumber(timelineSummary?.blocker_count) ? "warn" : "neutral"}>
                  {countLabel(timelineSummary?.event_count)} events
                </SeverityBadge>
                <SeverityBadge severity="neutral">{countLabel(timelineSummary?.trusted_event_count)} trusted</SeverityBadge>
              </div>
              <TermKV
                rows={[
                  { k: "completed", v: asStringArray(timelineSummary?.completed_stages).join(" → ") || "—" },
                  { k: "missing", v: asStringArray(timelineSummary?.missing_stages).join(", ") || "—" },
                  { k: "latest_event", v: asString(timelineSummary?.latest_event_at_utc) ?? "—" },
                  { k: "blockers", v: countLabel(timelineSummary?.blocker_count) },
                  { k: "warnings", v: countLabel(timelineSummary?.warning_count) },
                ]}
              />
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Stage</th>
                      <th>Status</th>
                      <th>Trusted</th>
                      <th>Time</th>
                      <th>Tracking</th>
                      <th>Order</th>
                      <th>Symbol</th>
                      <th>SHA</th>
                      <th>Summary</th>
                      <th>Blockers</th>
                    </tr>
                  </thead>
                  <tbody>
                    {executionTimeline.slice(0, 30).map((event, index) => (
                      <tr key={`${event.stage}-${event.artifact_path ?? event.generated_at_utc ?? index}`}>
                        <td>{event.stage}</td>
                        <td><StatusBadge raw={event.status ?? "UNKNOWN"} /></td>
                        <td>{String(event.trusted ?? "—")}</td>
                        <td>{event.generated_at_utc ?? "—"}</td>
                        <td>{event.tracking_id ?? "—"}</td>
                        <td>{event.broker_order_id ?? "—"}</td>
                        <td>{event.symbol ?? "—"}</td>
                        <td>{(event.artifact_sha256 ?? "—").slice(0, 16)}</td>
                        <td>{event.summary_line ?? "—"}</td>
                        <td>{Array.isArray(event.blockers) ? event.blockers.length : 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence bundle / timeline attestation" dense onInspect={() => openInspector({ title: "Paper execution evidence bundles", rawJson: { evidenceBundles, latestEvidenceBundle } })}>
          {evidenceBundles.length === 0 ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No sealed paper execution evidence bundle yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker seal-evidence-bundle
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundle ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundle.trust_banner) ?? "TRUST_RESTRICTED"} />
                    <StatusBadge raw={asString(latestEvidenceBundle.bundle_status) ?? "UNKNOWN"} />
                    <SeverityBadge severity={asNumber(latestEvidenceBundle.timeline_blocker_count) ? "warn" : "neutral"}>digest sealed</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: asString(latestEvidenceBundle.tracking_id) ?? "—" },
                      { k: "bundle_sha", v: (asString(latestEvidenceBundle.bundle_sha256) ?? "—").slice(0, 16) },
                      { k: "generated_at", v: asString(latestEvidenceBundle.generated_at_utc) ?? "—" },
                      { k: "timeline_status", v: asString(latestEvidenceBundle.timeline_sequence_status) ?? "EMPTY" },
                      { k: "events", v: countLabel(latestEvidenceBundle.timeline_event_count) },
                      { k: "trusted_events", v: countLabel(latestEvidenceBundle.timeline_trusted_event_count) },
                      { k: "source_artifacts", v: countLabel(latestEvidenceBundle.source_artifact_count) },
                      { k: "missing", v: asStringArray(latestEvidenceBundle.missing_stages).join(", ") || "—" },
                      { k: "blockers", v: asStringArray(latestEvidenceBundle.blockers).join("; ") || "—" },
                      { k: "warnings", v: asStringArray(latestEvidenceBundle.warnings).join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Tracking</th>
                      <th>Trust</th>
                      <th>Status</th>
                      <th>Timeline</th>
                      <th>Events</th>
                      <th>Sources</th>
                      <th>Blockers</th>
                      <th>Bundle SHA</th>
                      <th>Artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidenceBundles.slice(0, 20).map((bundle, index) => (
                      <tr key={`${bundle.artifact_path ?? "bundle"}-${index}`}>
                        <td>{bundle.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={bundle.trust_banner ?? "TRUST_RESTRICTED"} /></td>
                        <td><StatusBadge raw={bundle.bundle_status ?? "UNKNOWN"} /></td>
                        <td>{bundle.timeline_sequence_status ?? "EMPTY"}</td>
                        <td>{bundle.timeline_event_count ?? 0}</td>
                        <td>{bundle.source_artifact_count ?? 0}</td>
                        <td>{Array.isArray(bundle.blockers) ? bundle.blockers.length : 0}</td>
                        <td>{(bundle.bundle_sha256 ?? "—").slice(0, 16)}</td>
                        <td>{bundle.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence bundle verification" dense onInspect={() => openInspector({ title: "Paper execution evidence bundle verifications", rawJson: { evidenceBundleVerifications, latestEvidenceBundleVerification } })}>
          {evidenceBundleVerifications.length === 0 ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No independent bundle verification artifact yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker verify-evidence-bundle
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleVerification ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundleVerification.verification_status) ?? "UNKNOWN"} />
                    <StatusBadge raw={asString(latestEvidenceBundleVerification.trust_banner) ?? "UNTRUSTED"} />
                    <SeverityBadge severity={asBool(latestEvidenceBundleVerification.bundle_hash_valid) ? "ok" : "warn"}>bundle hash</SeverityBadge>
                    <SeverityBadge severity={asBool(latestEvidenceBundleVerification.timeline_source_link_valid) ? "ok" : "warn"}>source links</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: asString(latestEvidenceBundleVerification.tracking_id) ?? "—" },
                      { k: "verification_sha", v: (asString(latestEvidenceBundleVerification.artifact_sha256) ?? "—").slice(0, 16) },
                      { k: "bundle_declared", v: (asString(latestEvidenceBundleVerification.source_bundle_declared_sha256) ?? "—").slice(0, 16) },
                      { k: "bundle_computed", v: (asString(latestEvidenceBundleVerification.source_bundle_computed_sha256) ?? "—").slice(0, 16) },
                      { k: "sources", v: `${countLabel(latestEvidenceBundleVerification.verified_source_artifact_count)} / ${countLabel(latestEvidenceBundleVerification.source_artifact_count)}` },
                      { k: "missing_sources", v: countLabel(latestEvidenceBundleVerification.missing_source_artifact_count) },
                      { k: "mismatched_sources", v: countLabel(latestEvidenceBundleVerification.mismatched_source_artifact_count) },
                      { k: "blockers", v: asStringArray(latestEvidenceBundleVerification.blockers).join("; ") || "—" },
                      { k: "warnings", v: asStringArray(latestEvidenceBundleVerification.warnings).join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Tracking</th>
                      <th>Status</th>
                      <th>Trust</th>
                      <th>Bundle hash</th>
                      <th>Links</th>
                      <th>Verified</th>
                      <th>Missing</th>
                      <th>Mismatched</th>
                      <th>Artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidenceBundleVerifications.slice(0, 20).map((verification, index) => (
                      <tr key={`${verification.artifact_path ?? "verification"}-${index}`}>
                        <td>{verification.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td>
                        <td><StatusBadge raw={verification.trust_banner ?? "UNTRUSTED"} /></td>
                        <td>{verification.bundle_hash_valid ? "yes" : "no"}</td>
                        <td>{verification.timeline_source_link_valid ? "yes" : "no"}</td>
                        <td>{verification.verified_source_artifact_count ?? 0}/{verification.source_artifact_count ?? 0}</td>
                        <td>{verification.missing_source_artifact_count ?? 0}</td>
                        <td>{verification.mismatched_source_artifact_count ?? 0}</td>
                        <td>{verification.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence bundle drift monitor" dense onInspect={() => openInspector({ title: "Paper execution evidence bundle drift", rawJson: { evidenceBundleDrifts, latestEvidenceBundleDrift } })}>
          {evidenceBundleDrifts.length === 0 && !latestEvidenceBundleDrift ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No bundle drift check artifact yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker check-evidence-bundle-drift
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleDrift ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundleDrift.drift_status) ?? "UNKNOWN"} />
                    <StatusBadge raw={asString(latestEvidenceBundleDrift.trust_banner) ?? "TRUST_RESTRICTED"} />
                    <SeverityBadge severity={asString(latestEvidenceBundleDrift.drift_status) === "IN_SYNC" ? "ok" : "warn"}>timeline source set</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: asString(latestEvidenceBundleDrift.tracking_id) ?? "—" },
                      { k: "bundle_sha", v: (asString(latestEvidenceBundleDrift.source_bundle_sha256) ?? "—").slice(0, 16) },
                      { k: "current_fp", v: (asString(latestEvidenceBundleDrift.current_timeline_fingerprint) ?? "—").slice(0, 16) },
                      { k: "bundled_fp", v: (asString(latestEvidenceBundleDrift.bundled_timeline_fingerprint) ?? "—").slice(0, 16) },
                      { k: "current_sources", v: countLabel(latestEvidenceBundleDrift.current_source_artifact_count) },
                      { k: "bundled_sources", v: countLabel(latestEvidenceBundleDrift.bundled_source_artifact_count) },
                      { k: "new_sources", v: countLabel(latestEvidenceBundleDrift.new_source_artifact_count) },
                      { k: "removed_sources", v: countLabel(latestEvidenceBundleDrift.removed_source_artifact_count) },
                      { k: "changed_stages", v: countLabel(latestEvidenceBundleDrift.changed_stage_count) },
                      { k: "blockers", v: asStringArray(latestEvidenceBundleDrift.blockers).join("; ") || "—" },
                      { k: "warnings", v: asStringArray(latestEvidenceBundleDrift.warnings).join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Tracking</th>
                      <th>Status</th>
                      <th>Trust</th>
                      <th>Current</th>
                      <th>Bundled</th>
                      <th>New</th>
                      <th>Removed</th>
                      <th>Blockers</th>
                      <th>Artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidenceBundleDrifts.slice(0, 20).map((drift, index) => (
                      <tr key={`${drift.artifact_path ?? "drift"}-${index}`}>
                        <td>{drift.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={drift.drift_status ?? "UNKNOWN"} /></td>
                        <td><StatusBadge raw={drift.trust_banner ?? "TRUST_RESTRICTED"} /></td>
                        <td>{drift.current_source_artifact_count ?? 0}</td>
                        <td>{drift.bundled_source_artifact_count ?? 0}</td>
                        <td>{drift.new_source_artifact_count ?? 0}</td>
                        <td>{drift.removed_source_artifact_count ?? 0}</td>
                        <td>{Array.isArray(drift.blockers) ? drift.blockers.length : 0}</td>
                        <td>{drift.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence bundle rotation recommendation" dense onInspect={() => openInspector({ title: "Paper execution evidence bundle rotation", rawJson: { evidenceBundleRotations, latestEvidenceBundleRotation } })}>
          {evidenceBundleRotations.length === 0 && !latestEvidenceBundleRotation ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No bundle rotation recommendation yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker recommend-evidence-bundle-rotation
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRotation ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundleRotation.rotation_status) ?? "UNKNOWN"} />
                    <StatusBadge raw={asString(latestEvidenceBundleRotation.trust_banner) ?? "TRUST_RESTRICTED"} />
                    <SeverityBadge severity={asString(latestEvidenceBundleRotation.rotation_status) === "NOT_NEEDED" ? "ok" : "warn"}>operator recovery</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: asString(latestEvidenceBundleRotation.tracking_id) ?? "—" },
                      { k: "bundle_sha", v: (asString(latestEvidenceBundleRotation.source_bundle_sha256) ?? "—").slice(0, 16) },
                      { k: "bundle_status", v: asString(latestEvidenceBundleRotation.source_bundle_status) ?? "—" },
                      { k: "verification", v: asString(latestEvidenceBundleRotation.source_verification_status) ?? "—" },
                      { k: "drift", v: asString(latestEvidenceBundleRotation.source_drift_status) ?? "—" },
                      { k: "timeline", v: asString(latestEvidenceBundleRotation.timeline_sequence_status) ?? "—" },
                      { k: "reasons", v: asStringArray(latestEvidenceBundleRotation.rotation_reason_codes).join("; ") || "—" },
                      { k: "one_command", v: asString(latestEvidenceBundleRotation.one_command_sequence_hint) ?? "—" },
                      { k: "blockers", v: asStringArray(latestEvidenceBundleRotation.blockers).join("; ") || "—" },
                      { k: "warnings", v: asStringArray(latestEvidenceBundleRotation.warnings).join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Tracking</th>
                      <th>Status</th>
                      <th>Trust</th>
                      <th>Verify</th>
                      <th>Drift</th>
                      <th>Reasons</th>
                      <th>Blockers</th>
                      <th>Artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidenceBundleRotations.slice(0, 20).map((rotation, index) => (
                      <tr key={`${rotation.artifact_path ?? "rotation"}-${index}`}>
                        <td>{rotation.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={rotation.rotation_status ?? "UNKNOWN"} /></td>
                        <td><StatusBadge raw={rotation.trust_banner ?? "TRUST_RESTRICTED"} /></td>
                        <td>{rotation.source_verification_status ?? "—"}</td>
                        <td>{rotation.source_drift_status ?? "—"}</td>
                        <td>{Array.isArray(rotation.rotation_reason_codes) ? rotation.rotation_reason_codes.join("; ") : "—"}</td>
                        <td>{Array.isArray(rotation.blockers) ? rotation.blockers.length : 0}</td>
                        <td>{rotation.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence bundle rotation execution" dense onInspect={() => openInspector({ title: "Paper execution evidence bundle rotation execution", rawJson: { evidenceBundleRotationExecutions, latestEvidenceBundleRotationExecution } })}>
          {evidenceBundleRotationExecutions.length === 0 && !latestEvidenceBundleRotationExecution ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No bundle rotation execution manifest yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker run-evidence-bundle-rotation
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRotationExecution ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundleRotationExecution.rotation_execution_status) ?? "UNKNOWN"} />
                    <StatusBadge raw={asString(latestEvidenceBundleRotationExecution.trust_banner) ?? "TRUST_RESTRICTED"} />
                    <SeverityBadge severity={asString(latestEvidenceBundleRotationExecution.rotation_execution_status) === "PASS" ? "ok" : "warn"}>workflow manifest</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: asString(latestEvidenceBundleRotationExecution.tracking_id) ?? "—" },
                      { k: "source_recommendation", v: asString(latestEvidenceBundleRotationExecution.source_recommendation_status) ?? "—" },
                      { k: "timeline", v: asString(latestEvidenceBundleRotationExecution.timeline_sequence_status) ?? "—" },
                      { k: "bundle_sha", v: (asString(latestEvidenceBundleRotationExecution.sealed_bundle_sha256) ?? "—").slice(0, 16) },
                      { k: "verification", v: asString(latestEvidenceBundleRotationExecution.verification_status) ?? "—" },
                      { k: "drift", v: asString(latestEvidenceBundleRotationExecution.drift_status) ?? "—" },
                      { k: "steps", v: `${countLabel(latestEvidenceBundleRotationExecution.passed_step_count)}/${countLabel(latestEvidenceBundleRotationExecution.step_count)} passed` },
                      { k: "failed", v: countLabel(latestEvidenceBundleRotationExecution.failed_step_count) },
                      { k: "blockers", v: asStringArray(latestEvidenceBundleRotationExecution.blockers).join("; ") || "—" },
                      { k: "warnings", v: asStringArray(latestEvidenceBundleRotationExecution.warnings).join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Tracking</th>
                      <th>Status</th>
                      <th>Trust</th>
                      <th>Verify</th>
                      <th>Drift</th>
                      <th>Steps</th>
                      <th>Failed</th>
                      <th>Blockers</th>
                      <th>Artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidenceBundleRotationExecutions.slice(0, 20).map((execution, index) => (
                      <tr key={`${execution.artifact_path ?? "rotation-execution"}-${index}`}>
                        <td>{execution.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={execution.rotation_execution_status ?? "UNKNOWN"} /></td>
                        <td><StatusBadge raw={execution.trust_banner ?? "TRUST_RESTRICTED"} /></td>
                        <td>{execution.verification_status ?? "—"}</td>
                        <td>{execution.drift_status ?? "—"}</td>
                        <td>{execution.passed_step_count ?? 0}/{execution.step_count ?? 0}</td>
                        <td>{execution.failed_step_count ?? 0}</td>
                        <td>{Array.isArray(execution.blockers) ? execution.blockers.length : 0}</td>
                        <td>{execution.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence bundle attestation" dense onInspect={() => openInspector({ title: "Paper execution evidence bundle attestations", rawJson: { evidenceBundleAttestations, latestEvidenceBundleAttestation } })}>
          {evidenceBundleAttestations.length === 0 && !latestEvidenceBundleAttestation ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No keyless local bundle attestation yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker attest-evidence-bundle
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleAttestation ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundleAttestation.attestation_status) ?? "UNKNOWN"} />
                    <StatusBadge raw={asString(latestEvidenceBundleAttestation.trust_banner) ?? "TRUST_RESTRICTED"} />
                    <SeverityBadge severity={asString(latestEvidenceBundleAttestation.signature_status) === "UNSIGNED_KEYLESS_STUB" ? "neutral" : "warn"}>keyless stub</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: asString(latestEvidenceBundleAttestation.tracking_id) ?? "—" },
                      { k: "attestation_sha", v: (asString(latestEvidenceBundleAttestation.artifact_sha256) ?? "—").slice(0, 16) },
                      { k: "bundle_sha", v: (asString(latestEvidenceBundleAttestation.source_bundle_sha256) ?? "—").slice(0, 16) },
                      { k: "bundle_status", v: asString(latestEvidenceBundleAttestation.source_bundle_status) ?? "—" },
                      { k: "verification", v: asString(latestEvidenceBundleAttestation.source_verification_status) ?? "—" },
                      { k: "drift", v: asString(latestEvidenceBundleAttestation.source_drift_status) ?? "—" },
                      { k: "payload_sha", v: (asString(latestEvidenceBundleAttestation.statement_payload_sha256) ?? "—").slice(0, 16) },
                      { k: "signer", v: asString(latestEvidenceBundleAttestation.signer_identity) ?? "—" },
                      { k: "blockers", v: asStringArray(latestEvidenceBundleAttestation.blockers).join("; ") || "—" },
                      { k: "warnings", v: asStringArray(latestEvidenceBundleAttestation.warnings).join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Tracking</th>
                      <th>Status</th>
                      <th>Trust</th>
                      <th>Mode</th>
                      <th>Signature</th>
                      <th>Verify</th>
                      <th>Drift</th>
                      <th>Blockers</th>
                      <th>Artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidenceBundleAttestations.slice(0, 20).map((attestation, index) => (
                      <tr key={`${attestation.artifact_path ?? "attestation"}-${index}`}>
                        <td>{attestation.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={attestation.attestation_status ?? "UNKNOWN"} /></td>
                        <td><StatusBadge raw={attestation.trust_banner ?? "TRUST_RESTRICTED"} /></td>
                        <td>{attestation.attestation_mode ?? "KEYLESS_LOCAL_STUB"}</td>
                        <td>{attestation.signature_status ?? "UNSIGNED_KEYLESS_STUB"}</td>
                        <td>{attestation.source_verification_status ?? "—"}</td>
                        <td>{attestation.source_drift_status ?? "—"}</td>
                        <td>{attestation.blocker_count ?? 0}</td>
                        <td>{attestation.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence bundle attestation verification" dense onInspect={() => openInspector({ title: "Paper execution evidence bundle attestation verifications", rawJson: { evidenceBundleAttestationVerifications, latestEvidenceBundleAttestationVerification } })}>
          {evidenceBundleAttestationVerifications.length === 0 && !latestEvidenceBundleAttestationVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No attestation verification artifact yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker verify-evidence-bundle-attestation
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleAttestationVerification ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundleAttestationVerification.verification_status) ?? "UNKNOWN"} />
                    <StatusBadge raw={asString(latestEvidenceBundleAttestationVerification.trust_banner) ?? "TRUST_RESTRICTED"} />
                    <SeverityBadge severity={asBool(latestEvidenceBundleAttestationVerification.artifact_hash_valid) ? "ok" : "warn"}>attestation hash</SeverityBadge>
                    <SeverityBadge severity={asBool(latestEvidenceBundleAttestationVerification.statement_payload_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge>
                    <SeverityBadge severity={asBool(latestEvidenceBundleAttestationVerification.keyless_stub_signature_valid) ? "ok" : "warn"}>keyless marker</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: asString(latestEvidenceBundleAttestationVerification.tracking_id) ?? "—" },
                      { k: "verification_sha", v: (asString(latestEvidenceBundleAttestationVerification.artifact_sha256) ?? "—").slice(0, 16) },
                      { k: "attestation_declared", v: (asString(latestEvidenceBundleAttestationVerification.source_attestation_declared_sha256) ?? "—").slice(0, 16) },
                      { k: "attestation_computed", v: (asString(latestEvidenceBundleAttestationVerification.source_attestation_computed_sha256) ?? "—").slice(0, 16) },
                      { k: "source_status", v: asString(latestEvidenceBundleAttestationVerification.source_attestation_status) ?? "—" },
                      { k: "bundle_hash", v: asBool(latestEvidenceBundleAttestationVerification.source_bundle_hash_valid) ? "valid" : "invalid/missing" },
                      { k: "verification_hash", v: asBool(latestEvidenceBundleAttestationVerification.source_verification_hash_valid) ? "valid" : "invalid/missing" },
                      { k: "drift_hash", v: asBool(latestEvidenceBundleAttestationVerification.source_drift_hash_valid) ? "valid" : "invalid/missing" },
                      { k: "blockers", v: asStringArray(latestEvidenceBundleAttestationVerification.blockers).join("; ") || "—" },
                      { k: "warnings", v: asStringArray(latestEvidenceBundleAttestationVerification.warnings).join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Tracking</th>
                      <th>Status</th>
                      <th>Trust</th>
                      <th>Artifact hash</th>
                      <th>Payload</th>
                      <th>Stub sig</th>
                      <th>Bundle</th>
                      <th>Verify</th>
                      <th>Drift</th>
                      <th>Blockers</th>
                      <th>Artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidenceBundleAttestationVerifications.slice(0, 20).map((verification, index) => (
                      <tr key={`${verification.artifact_path ?? "attestation-verification"}-${index}`}>
                        <td>{verification.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td>
                        <td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td>
                        <td>{verification.artifact_hash_valid ? "yes" : "no"}</td>
                        <td>{verification.statement_payload_hash_valid ? "yes" : "no"}</td>
                        <td>{verification.keyless_stub_signature_valid ? "yes" : "no"}</td>
                        <td>{verification.source_bundle_hash_valid ? "yes" : "no"}</td>
                        <td>{verification.source_verification_hash_valid ? "yes" : "no"}</td>
                        <td>{verification.source_drift_hash_valid ? "yes" : "no"}</td>
                        <td>{verification.blocker_count ?? 0}</td>
                        <td>{verification.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence bundle closure" dense onInspect={() => openInspector({ title: "Paper execution evidence bundle closures", rawJson: { evidenceBundleClosures, latestEvidenceBundleClosure } })}>
          {evidenceBundleClosures.length === 0 && !latestEvidenceBundleClosure ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No closure packet yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker close-evidence-bundle
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleClosure ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundleClosure.closure_status) ?? "UNKNOWN"} />
                    <StatusBadge raw={asString(latestEvidenceBundleClosure.trust_banner) ?? "TRUST_RESTRICTED"} />
                    <SeverityBadge severity={asBool(latestEvidenceBundleClosure.source_attestation_artifact_hash_valid) ? "ok" : "warn"}>attestation hash</SeverityBadge>
                    <SeverityBadge severity={asBool(latestEvidenceBundleClosure.source_attestation_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge>
                    <SeverityBadge severity={asBool(latestEvidenceBundleClosure.source_attestation_keyless_stub_valid) ? "ok" : "warn"}>keyless marker</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: asString(latestEvidenceBundleClosure.tracking_id) ?? "—" },
                      { k: "closure_sha", v: (asString(latestEvidenceBundleClosure.artifact_sha256) ?? "—").slice(0, 16) },
                      { k: "bundle_sha", v: (asString(latestEvidenceBundleClosure.source_bundle_sha256) ?? "—").slice(0, 16) },
                      { k: "bundle_status", v: asString(latestEvidenceBundleClosure.source_bundle_status) ?? "—" },
                      { k: "verification", v: asString(latestEvidenceBundleClosure.source_verification_status) ?? "—" },
                      { k: "drift", v: asString(latestEvidenceBundleClosure.source_drift_status) ?? "—" },
                      { k: "attestation", v: asString(latestEvidenceBundleClosure.source_attestation_status) ?? "—" },
                      { k: "attestation_verify", v: asString(latestEvidenceBundleClosure.source_attestation_verification_status) ?? "—" },
                      { k: "reasons", v: asStringArray(latestEvidenceBundleClosure.closure_reason_codes).join("; ") || "—" },
                      { k: "next", v: asStringArray(latestEvidenceBundleClosure.recommended_operator_sequence).join("; ") || "—" },
                      { k: "blockers", v: asStringArray(latestEvidenceBundleClosure.blockers).join("; ") || "—" },
                      { k: "warnings", v: asStringArray(latestEvidenceBundleClosure.warnings).join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Tracking</th>
                      <th>Status</th>
                      <th>Trust</th>
                      <th>Bundle</th>
                      <th>Verify</th>
                      <th>Drift</th>
                      <th>Attest</th>
                      <th>Attest verify</th>
                      <th>Blockers</th>
                      <th>Artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidenceBundleClosures.slice(0, 20).map((closure, index) => (
                      <tr key={`${closure.artifact_path ?? "closure"}-${index}`}>
                        <td>{closure.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={closure.closure_status ?? "UNKNOWN"} /></td>
                        <td><StatusBadge raw={closure.trust_banner ?? "TRUST_RESTRICTED"} /></td>
                        <td>{closure.source_bundle_status ?? "—"}</td>
                        <td>{closure.source_verification_status ?? "—"}</td>
                        <td>{closure.source_drift_status ?? "—"}</td>
                        <td>{closure.source_attestation_status ?? "—"}</td>
                        <td>{closure.source_attestation_verification_status ?? "—"}</td>
                        <td>{closure.blocker_count ?? 0}</td>
                        <td>{closure.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>


        <Pane title="Evidence bundle closure verification" dense onInspect={() => openInspector({ title: "Paper execution evidence bundle closure verification", rawJson: { evidenceBundleClosureVerifications, latestEvidenceBundleClosureVerification } })}>
          {evidenceBundleClosureVerifications.length === 0 && !latestEvidenceBundleClosureVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No closure verification artifact yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker verify-evidence-bundle-closure
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleClosureVerification ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundleClosureVerification.verification_status) ?? "UNKNOWN"} />
                    <StatusBadge raw={asString(latestEvidenceBundleClosureVerification.trust_banner) ?? "TRUST_RESTRICTED"} />
                    <SeverityBadge severity={asBool(latestEvidenceBundleClosureVerification.closure_artifact_hash_valid) ? "ok" : "warn"}>closure hash</SeverityBadge>
                    <SeverityBadge severity={asBool(latestEvidenceBundleClosureVerification.source_bundle_hash_valid) ? "ok" : "warn"}>bundle hash</SeverityBadge>
                    <SeverityBadge severity={asBool(latestEvidenceBundleClosureVerification.source_attestation_verification_hash_valid) ? "ok" : "warn"}>attest verify hash</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: asString(latestEvidenceBundleClosureVerification.tracking_id) ?? "—" },
                      { k: "verification_sha", v: (asString(latestEvidenceBundleClosureVerification.artifact_sha256) ?? "—").slice(0, 16) },
                      { k: "closure_sha", v: (asString(latestEvidenceBundleClosureVerification.source_closure_declared_sha256) ?? "—").slice(0, 16) },
                      { k: "computed_closure", v: (asString(latestEvidenceBundleClosureVerification.source_closure_computed_sha256) ?? "—").slice(0, 16) },
                      { k: "closure_status", v: asString(latestEvidenceBundleClosureVerification.source_closure_status) ?? "—" },
                      { k: "closure_trust", v: asString(latestEvidenceBundleClosureVerification.source_closure_trust_banner) ?? "—" },
                      { k: "blockers", v: asStringArray(latestEvidenceBundleClosureVerification.blockers).join("; ") || "—" },
                      { k: "warnings", v: asStringArray(latestEvidenceBundleClosureVerification.warnings).join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Tracking</th>
                      <th>Status</th>
                      <th>Trust</th>
                      <th>Closure hash</th>
                      <th>Bundle hash</th>
                      <th>Attest hash</th>
                      <th>Attest verify hash</th>
                      <th>Blockers</th>
                      <th>Artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidenceBundleClosureVerifications.slice(0, 20).map((verification, index) => (
                      <tr key={`${verification.artifact_path ?? "closure-verification"}-${index}`}>
                        <td>{verification.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td>
                        <td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td>
                        <td>{String(verification.closure_artifact_hash_valid ?? false)}</td>
                        <td>{String(verification.source_bundle_hash_valid ?? false)}</td>
                        <td>{String(verification.source_attestation_hash_valid ?? false)}</td>
                        <td>{String(verification.source_attestation_verification_hash_valid ?? false)}</td>
                        <td>{verification.blocker_count ?? 0}</td>
                        <td>{verification.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>


        <Pane title="Evidence-chain export handoff" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain export handoff", rawJson: { evidenceBundleExportManifests, latestEvidenceBundleExportManifest } })}>
          {evidenceBundleExportManifests.length === 0 && !latestEvidenceBundleExportManifest ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No export handoff manifest yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker export-evidence-bundle-chain
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleExportManifest ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundleExportManifest.export_status) ?? "UNKNOWN"} />
                    <StatusBadge raw={asString(latestEvidenceBundleExportManifest.trust_banner) ?? "TRUST_RESTRICTED"} />
                    <SeverityBadge severity={asBool(latestEvidenceBundleExportManifest.closure_verification_artifact_hash_valid) ? "ok" : "warn"}>closure verification hash</SeverityBadge>
                    <SeverityBadge severity={(asNumber(latestEvidenceBundleExportManifest.export_entry_count) ?? 0) === (asNumber(latestEvidenceBundleExportManifest.export_digest_valid_entry_count) ?? -1) ? "ok" : "warn"}>entry digests</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: asString(latestEvidenceBundleExportManifest.tracking_id) ?? "—" },
                      { k: "export_sha", v: (asString(latestEvidenceBundleExportManifest.artifact_sha256) ?? "—").slice(0, 16) },
                      { k: "index_sha", v: (asString(latestEvidenceBundleExportManifest.export_index_sha256) ?? "—").slice(0, 16) },
                      { k: "entries", v: `${countLabel(latestEvidenceBundleExportManifest.export_digest_valid_entry_count)} / ${countLabel(latestEvidenceBundleExportManifest.export_entry_count)}` },
                      { k: "total_size", v: String(asNumber(latestEvidenceBundleExportManifest.total_size_bytes) ?? 0) },
                      { k: "closure_verification", v: asString(latestEvidenceBundleExportManifest.source_closure_verification_status) ?? "—" },
                      { k: "closure_status", v: asString(latestEvidenceBundleExportManifest.source_closure_status) ?? "—" },
                      { k: "blockers", v: asStringArray(latestEvidenceBundleExportManifest.blockers).join("; ") || "—" },
                      { k: "warnings", v: asStringArray(latestEvidenceBundleExportManifest.warnings).join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Tracking</th>
                      <th>Status</th>
                      <th>Trust</th>
                      <th>Entries</th>
                      <th>Valid digests</th>
                      <th>Total bytes</th>
                      <th>Blockers</th>
                      <th>Artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidenceBundleExportManifests.slice(0, 20).map((manifest, index) => (
                      <tr key={`${manifest.artifact_path ?? "export-manifest"}-${index}`}>
                        <td>{manifest.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={manifest.export_status ?? "UNKNOWN"} /></td>
                        <td><StatusBadge raw={manifest.trust_banner ?? "TRUST_RESTRICTED"} /></td>
                        <td>{manifest.export_entry_count ?? 0}</td>
                        <td>{manifest.export_digest_valid_entry_count ?? 0}</td>
                        <td>{manifest.total_size_bytes ?? 0}</td>
                        <td>{manifest.blocker_count ?? 0}</td>
                        <td>{manifest.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>


        <Pane title="Evidence-chain export verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain export verification", rawJson: { evidenceBundleExportVerifications, latestEvidenceBundleExportVerification } })}>
          {evidenceBundleExportVerifications.length === 0 && !latestEvidenceBundleExportVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No export verification artifact yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker verify-evidence-bundle-export
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleExportVerification ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundleExportVerification.verification_status) ?? "UNKNOWN"} />
                    <StatusBadge raw={asString(latestEvidenceBundleExportVerification.trust_banner) ?? "TRUST_RESTRICTED"} />
                    <SeverityBadge severity={asBool(latestEvidenceBundleExportVerification.export_manifest_hash_valid) ? "ok" : "warn"}>manifest hash</SeverityBadge>
                    <SeverityBadge severity={asBool(latestEvidenceBundleExportVerification.export_index_hash_valid) ? "ok" : "warn"}>index hash</SeverityBadge>
                    <SeverityBadge severity={(asNumber(latestEvidenceBundleExportVerification.recomputed_export_entry_count) ?? 0) === (asNumber(latestEvidenceBundleExportVerification.recomputed_export_digest_valid_entry_count) ?? -1) ? "ok" : "warn"}>entry digests</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: asString(latestEvidenceBundleExportVerification.tracking_id) ?? "—" },
                      { k: "verification_sha", v: (asString(latestEvidenceBundleExportVerification.artifact_sha256) ?? "—").slice(0, 16) },
                      { k: "export_status", v: asString(latestEvidenceBundleExportVerification.source_export_manifest_status) ?? "—" },
                      { k: "manifest_sha", v: (asString(latestEvidenceBundleExportVerification.source_export_manifest_declared_sha256) ?? "—").slice(0, 16) },
                      { k: "index_sha", v: (asString(latestEvidenceBundleExportVerification.source_export_index_declared_sha256) ?? "—").slice(0, 16) },
                      { k: "entries", v: `${countLabel(latestEvidenceBundleExportVerification.recomputed_export_digest_valid_entry_count)} / ${countLabel(latestEvidenceBundleExportVerification.recomputed_export_entry_count)}` },
                      { k: "missing_entries", v: countLabel(latestEvidenceBundleExportVerification.missing_entry_count) },
                      { k: "digest_mismatches", v: countLabel(latestEvidenceBundleExportVerification.digest_mismatch_entry_count) },
                      { k: "blockers", v: asStringArray(latestEvidenceBundleExportVerification.blockers).join("; ") || "—" },
                      { k: "warnings", v: asStringArray(latestEvidenceBundleExportVerification.warnings).join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Tracking</th>
                      <th>Status</th>
                      <th>Trust</th>
                      <th>Manifest hash</th>
                      <th>Index hash</th>
                      <th>Valid digests</th>
                      <th>Missing</th>
                      <th>Mismatches</th>
                      <th>Blockers</th>
                      <th>Artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidenceBundleExportVerifications.slice(0, 20).map((verification, index) => (
                      <tr key={`${verification.artifact_path ?? "export-verification"}-${index}`}>
                        <td>{verification.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td>
                        <td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td>
                        <td>{String(verification.export_manifest_hash_valid ?? false)}</td>
                        <td>{String(verification.export_index_hash_valid ?? false)}</td>
                        <td>{verification.recomputed_export_digest_valid_entry_count ?? 0} / {verification.recomputed_export_entry_count ?? 0}</td>
                        <td>{verification.missing_entry_count ?? 0}</td>
                        <td>{verification.digest_mismatch_entry_count ?? 0}</td>
                        <td>{verification.blocker_count ?? 0}</td>
                        <td>{verification.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>


        <Pane title="Evidence-chain retention receipt" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention receipt", rawJson: { evidenceBundleRetentionReceipts, latestEvidenceBundleRetentionReceipt } })}>
          {evidenceBundleRetentionReceipts.length === 0 && !latestEvidenceBundleRetentionReceipt ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No retention receipt artifact yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker receipt-evidence-bundle-retention
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionReceipt ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundleRetentionReceipt.retention_status) ?? "UNKNOWN"} />
                    <StatusBadge raw={asString(latestEvidenceBundleRetentionReceipt.trust_banner) ?? "TRUST_RESTRICTED"} />
                    <SeverityBadge severity={asBool(latestEvidenceBundleRetentionReceipt.export_verification_artifact_hash_valid) ? "ok" : "warn"}>export verification hash</SeverityBadge>
                    <SeverityBadge severity={(asNumber(latestEvidenceBundleRetentionReceipt.retained_entry_count) ?? 0) === (asNumber(latestEvidenceBundleRetentionReceipt.retained_ready_entry_count) ?? -1) ? "ok" : "warn"}>retention entries</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: asString(latestEvidenceBundleRetentionReceipt.tracking_id) ?? "—" },
                      { k: "receipt_sha", v: (asString(latestEvidenceBundleRetentionReceipt.artifact_sha256) ?? "—").slice(0, 16) },
                      { k: "export_verification_status", v: asString(latestEvidenceBundleRetentionReceipt.source_export_verification_status) ?? "—" },
                      { k: "export_manifest_status", v: asString(latestEvidenceBundleRetentionReceipt.source_export_manifest_status) ?? "—" },
                      { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionReceipt.retained_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionReceipt.retained_entry_count)}` },
                      { k: "total_size_bytes", v: countLabel(latestEvidenceBundleRetentionReceipt.total_size_bytes) },
                      { k: "retention_index", v: (asString(latestEvidenceBundleRetentionReceipt.retention_index_sha256) ?? "—").slice(0, 16) },
                      { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionReceipt.blockers).join("; ") || "—" },
                      { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionReceipt.warnings).join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Tracking</th>
                      <th>Status</th>
                      <th>Trust</th>
                      <th>Hash</th>
                      <th>Ready entries</th>
                      <th>Total bytes</th>
                      <th>Blockers</th>
                      <th>Artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidenceBundleRetentionReceipts.slice(0, 20).map((receipt, index) => (
                      <tr key={`${receipt.artifact_path ?? "retention-receipt"}-${index}`}>
                        <td>{receipt.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={receipt.retention_status ?? "UNKNOWN"} /></td>
                        <td><StatusBadge raw={receipt.trust_banner ?? "TRUST_RESTRICTED"} /></td>
                        <td>{String(receipt.export_verification_artifact_hash_valid ?? false)}</td>
                        <td>{receipt.retained_ready_entry_count ?? 0} / {receipt.retained_entry_count ?? 0}</td>
                        <td>{receipt.total_size_bytes ?? 0}</td>
                        <td>{receipt.blocker_count ?? 0}</td>
                        <td>{receipt.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>


        <Pane title="Evidence-chain retention verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention verification", rawJson: { evidenceBundleRetentionVerifications, latestEvidenceBundleRetentionVerification } })}>
          {evidenceBundleRetentionVerifications.length === 0 && !latestEvidenceBundleRetentionVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No retention verification artifact yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker verify-evidence-bundle-retention
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionVerification ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundleRetentionVerification.verification_status) ?? "UNKNOWN"} />
                    <StatusBadge raw={asString(latestEvidenceBundleRetentionVerification.trust_banner) ?? "TRUST_RESTRICTED"} />
                    <SeverityBadge severity={asBool(latestEvidenceBundleRetentionVerification.retention_receipt_hash_valid) ? "ok" : "warn"}>receipt hash</SeverityBadge>
                    <SeverityBadge severity={asBool(latestEvidenceBundleRetentionVerification.retention_index_hash_valid) ? "ok" : "warn"}>retention index</SeverityBadge>
                    <SeverityBadge severity={(asNumber(latestEvidenceBundleRetentionVerification.recomputed_retention_entry_count) ?? 0) === (asNumber(latestEvidenceBundleRetentionVerification.recomputed_retention_ready_entry_count) ?? -1) ? "ok" : "warn"}>retained files</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: asString(latestEvidenceBundleRetentionVerification.tracking_id) ?? "—" },
                      { k: "verification_sha", v: (asString(latestEvidenceBundleRetentionVerification.artifact_sha256) ?? "—").slice(0, 16) },
                      { k: "receipt_status", v: asString(latestEvidenceBundleRetentionVerification.source_retention_receipt_status) ?? "—" },
                      { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionVerification.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionVerification.recomputed_retention_entry_count)}` },
                      { k: "missing", v: countLabel(latestEvidenceBundleRetentionVerification.missing_entry_count) },
                      { k: "mismatched", v: countLabel(latestEvidenceBundleRetentionVerification.digest_mismatch_entry_count) },
                      { k: "receipt_index", v: (asString(latestEvidenceBundleRetentionVerification.source_retention_index_declared_sha256) ?? "—").slice(0, 16) },
                      { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionVerification.blockers).join("; ") || "—" },
                      { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionVerification.warnings).join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Tracking</th>
                      <th>Status</th>
                      <th>Trust</th>
                      <th>Receipt hash</th>
                      <th>Index</th>
                      <th>Ready entries</th>
                      <th>Mismatches</th>
                      <th>Blockers</th>
                      <th>Artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidenceBundleRetentionVerifications.slice(0, 20).map((verification, index) => (
                      <tr key={`${verification.artifact_path ?? "retention-verification"}-${index}`}>
                        <td>{verification.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td>
                        <td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td>
                        <td>{String(verification.retention_receipt_hash_valid ?? false)}</td>
                        <td>{String(verification.retention_index_hash_valid ?? false)}</td>
                        <td>{verification.recomputed_retention_ready_entry_count ?? 0} / {verification.recomputed_retention_entry_count ?? 0}</td>
                        <td>{verification.digest_mismatch_entry_count ?? 0}</td>
                        <td>{verification.blocker_count ?? 0}</td>
                        <td>{verification.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>


        <Pane title="Evidence-chain retention signoff" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention signoff", rawJson: { evidenceBundleRetentionSignoffs, latestEvidenceBundleRetentionSignoff } })}>
          {evidenceBundleRetentionSignoffs.length === 0 && !latestEvidenceBundleRetentionSignoff ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No retention signoff certificate yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker signoff-evidence-bundle-retention
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionSignoff ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundleRetentionSignoff.signoff_status) ?? "UNKNOWN"} />
                    <StatusBadge raw={asString(latestEvidenceBundleRetentionSignoff.trust_banner) ?? "TRUST_RESTRICTED"} />
                    <SeverityBadge severity={asBool(latestEvidenceBundleRetentionSignoff.retention_verification_artifact_hash_valid) ? "ok" : "warn"}>verification hash</SeverityBadge>
                    <SeverityBadge severity={(asNumber(latestEvidenceBundleRetentionSignoff.recomputed_retention_entry_count) ?? 0) === (asNumber(latestEvidenceBundleRetentionSignoff.recomputed_retention_ready_entry_count) ?? -1) ? "ok" : "warn"}>retained files</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: asString(latestEvidenceBundleRetentionSignoff.tracking_id) ?? "—" },
                      { k: "operator", v: asString(latestEvidenceBundleRetentionSignoff.operator_id) ?? "operator" },
                      { k: "signoff_sha", v: (asString(latestEvidenceBundleRetentionSignoff.artifact_sha256) ?? "—").slice(0, 16) },
                      { k: "statement", v: (asString(latestEvidenceBundleRetentionSignoff.signoff_statement_sha256) ?? "—").slice(0, 16) },
                      { k: "verification_status", v: asString(latestEvidenceBundleRetentionSignoff.source_retention_verification_status) ?? "—" },
                      { k: "receipt_status", v: asString(latestEvidenceBundleRetentionSignoff.source_retention_receipt_status) ?? "—" },
                      { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionSignoff.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionSignoff.recomputed_retention_entry_count)}` },
                      { k: "missing", v: countLabel(latestEvidenceBundleRetentionSignoff.missing_entry_count) },
                      { k: "mismatched", v: countLabel(latestEvidenceBundleRetentionSignoff.digest_mismatch_entry_count) },
                      { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionSignoff.blockers).join("; ") || "—" },
                      { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionSignoff.warnings).join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Tracking</th>
                      <th>Status</th>
                      <th>Trust</th>
                      <th>Operator</th>
                      <th>Ready entries</th>
                      <th>Blockers</th>
                      <th>Artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidenceBundleRetentionSignoffs.slice(0, 20).map((signoff, index) => (
                      <tr key={`${signoff.artifact_path ?? "retention-signoff"}-${index}`}>
                        <td>{signoff.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={signoff.signoff_status ?? "UNKNOWN"} /></td>
                        <td><StatusBadge raw={signoff.trust_banner ?? "TRUST_RESTRICTED"} /></td>
                        <td>{signoff.operator_id ?? "operator"}</td>
                        <td>{signoff.recomputed_retention_ready_entry_count ?? 0} / {signoff.recomputed_retention_entry_count ?? 0}</td>
                        <td>{signoff.blocker_count ?? 0}</td>
                        <td>{signoff.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>


        <Pane title="Evidence-chain retention signoff verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention signoff verification", rawJson: { evidenceBundleRetentionSignoffVerifications, latestEvidenceBundleRetentionSignoffVerification } })}>
          {evidenceBundleRetentionSignoffVerifications.length === 0 && !latestEvidenceBundleRetentionSignoffVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No retention signoff verification artifact yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker verify-evidence-bundle-retention-signoff
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionSignoffVerification ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundleRetentionSignoffVerification.verification_status) ?? "UNKNOWN"} />
                    <StatusBadge raw={asString(latestEvidenceBundleRetentionSignoffVerification.trust_banner) ?? "TRUST_RESTRICTED"} />
                    <SeverityBadge severity={asBool(latestEvidenceBundleRetentionSignoffVerification.retention_signoff_artifact_hash_valid) ? "ok" : "warn"}>signoff hash</SeverityBadge>
                    <SeverityBadge severity={asBool(latestEvidenceBundleRetentionSignoffVerification.signoff_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge>
                    <SeverityBadge severity={asBool(latestEvidenceBundleRetentionSignoffVerification.retention_verification_artifact_hash_valid) ? "ok" : "warn"}>source verification</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: asString(latestEvidenceBundleRetentionSignoffVerification.tracking_id) ?? "—" },
                      { k: "operator", v: asString(latestEvidenceBundleRetentionSignoffVerification.operator_id) ?? "operator" },
                      { k: "verification_sha", v: (asString(latestEvidenceBundleRetentionSignoffVerification.artifact_sha256) ?? "—").slice(0, 16) },
                      { k: "signoff_status", v: asString(latestEvidenceBundleRetentionSignoffVerification.source_retention_signoff_status) ?? "—" },
                      { k: "source_verification", v: asString(latestEvidenceBundleRetentionSignoffVerification.source_retention_verification_status) ?? "—" },
                      { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionSignoffVerification.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionSignoffVerification.recomputed_retention_entry_count)}` },
                      { k: "missing", v: countLabel(latestEvidenceBundleRetentionSignoffVerification.missing_entry_count) },
                      { k: "mismatched", v: countLabel(latestEvidenceBundleRetentionSignoffVerification.digest_mismatch_entry_count) },
                      { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionSignoffVerification.blockers).join("; ") || "—" },
                      { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionSignoffVerification.warnings).join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead>
                    <tr>
                      <th>Tracking</th>
                      <th>Status</th>
                      <th>Trust</th>
                      <th>Signoff hash</th>
                      <th>Statement hash</th>
                      <th>Source verification</th>
                      <th>Ready entries</th>
                      <th>Blockers</th>
                      <th>Artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidenceBundleRetentionSignoffVerifications.slice(0, 20).map((verification, index) => (
                      <tr key={`${verification.artifact_path ?? "retention-signoff-verification"}-${index}`}>
                        <td>{verification.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td>
                        <td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td>
                        <td>{String(verification.retention_signoff_artifact_hash_valid ?? false)}</td>
                        <td>{String(verification.signoff_statement_hash_valid ?? false)}</td>
                        <td>{String(verification.retention_verification_artifact_hash_valid ?? false)}</td>
                        <td>{verification.recomputed_retention_ready_entry_count ?? 0} / {verification.recomputed_retention_entry_count ?? 0}</td>
                        <td>{verification.blocker_count ?? 0}</td>
                        <td>{verification.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>


        <Pane title="Evidence-chain retention handoff" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention handoff", rawJson: { evidenceBundleRetentionHandoffs, latestEvidenceBundleRetentionHandoff } })}>
          {evidenceBundleRetentionHandoffs.length === 0 && !latestEvidenceBundleRetentionHandoff ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No final retention handoff capsule yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker handoff-evidence-bundle-retention
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionHandoff ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundleRetentionHandoff.handoff_status) ?? "UNKNOWN"} />
                    <StatusBadge raw={asString(latestEvidenceBundleRetentionHandoff.trust_banner) ?? "TRUST_RESTRICTED"} />
                    <SeverityBadge severity={asBool(latestEvidenceBundleRetentionHandoff.retention_signoff_verification_artifact_hash_valid) ? "ok" : "warn"}>signoff verification hash</SeverityBadge>
                    <SeverityBadge severity={asBool(latestEvidenceBundleRetentionHandoff.retention_signoff_artifact_hash_valid) ? "ok" : "warn"}>signoff hash</SeverityBadge>
                    <SeverityBadge severity={asBool(latestEvidenceBundleRetentionHandoff.signoff_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge>
                    <SeverityBadge severity={(asNumber(latestEvidenceBundleRetentionHandoff.recomputed_retention_entry_count) ?? 0) === (asNumber(latestEvidenceBundleRetentionHandoff.recomputed_retention_ready_entry_count) ?? -1) ? "ok" : "warn"}>retained files</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: asString(latestEvidenceBundleRetentionHandoff.tracking_id) ?? "—" },
                      { k: "custodian", v: asString(latestEvidenceBundleRetentionHandoff.custodian_id) ?? "operator" },
                      { k: "handoff_sha", v: (asString(latestEvidenceBundleRetentionHandoff.artifact_sha256) ?? "—").slice(0, 16) },
                      { k: "statement", v: (asString(latestEvidenceBundleRetentionHandoff.handoff_statement_sha256) ?? "—").slice(0, 16) },
                      { k: "signoff_verification", v: (asString(latestEvidenceBundleRetentionHandoff.source_retention_signoff_verification_declared_sha256) ?? "—").slice(0, 16) },
                      { k: "signoff_status", v: asString(latestEvidenceBundleRetentionHandoff.source_retention_signoff_status) ?? "—" },
                      { k: "retention_verification", v: asString(latestEvidenceBundleRetentionHandoff.source_retention_verification_status) ?? "—" },
                      { k: "receipt_status", v: asString(latestEvidenceBundleRetentionHandoff.source_retention_receipt_status) ?? "—" },
                      { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionHandoff.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionHandoff.recomputed_retention_entry_count)}` },
                      { k: "missing", v: countLabel(latestEvidenceBundleRetentionHandoff.missing_entry_count) },
                      { k: "mismatched", v: countLabel(latestEvidenceBundleRetentionHandoff.digest_mismatch_entry_count) },
                      { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionHandoff.blockers).join("; ") || "—" },
                      { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionHandoff.warnings).join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Custodian</th><th>Ready entries</th><th>Blockers</th><th>Artifact</th></tr></thead>
                  <tbody>
                    {evidenceBundleRetentionHandoffs.slice(0, 20).map((handoff, index) => (
                      <tr key={`${handoff.artifact_path ?? "retention-handoff"}-${index}`}>
                        <td>{handoff.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={handoff.handoff_status ?? "UNKNOWN"} /></td>
                        <td><StatusBadge raw={handoff.trust_banner ?? "TRUST_RESTRICTED"} /></td>
                        <td>{handoff.custodian_id ?? "operator"}</td>
                        <td>{handoff.recomputed_retention_ready_entry_count ?? 0} / {handoff.recomputed_retention_entry_count ?? 0}</td>
                        <td>{handoff.blocker_count ?? 0}</td>
                        <td>{handoff.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>


        <Pane title="Evidence-chain retention handoff verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention handoff verification", rawJson: { evidenceBundleRetentionHandoffVerifications, latestEvidenceBundleRetentionHandoffVerification } })}>
          {evidenceBundleRetentionHandoffVerifications.length === 0 && !latestEvidenceBundleRetentionHandoffVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No retention handoff verification artifact yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>
                strategy-validator-paper-broker verify-evidence-bundle-retention-handoff
              </pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionHandoffVerification ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundleRetentionHandoffVerification.verification_status) ?? "UNKNOWN"} />
                    <StatusBadge raw={asString(latestEvidenceBundleRetentionHandoffVerification.trust_banner) ?? "TRUST_RESTRICTED"} />
                    <SeverityBadge severity={asBool(latestEvidenceBundleRetentionHandoffVerification.retention_handoff_artifact_hash_valid) ? "ok" : "warn"}>handoff hash</SeverityBadge>
                    <SeverityBadge severity={asBool(latestEvidenceBundleRetentionHandoffVerification.handoff_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge>
                    <SeverityBadge severity={asBool(latestEvidenceBundleRetentionHandoffVerification.retention_signoff_verification_artifact_hash_valid) ? "ok" : "warn"}>source signoff verification</SeverityBadge>
                  </div>
                  <TermKV
                    rows={[
                      { k: "tracking_id", v: asString(latestEvidenceBundleRetentionHandoffVerification.tracking_id) ?? "—" },
                      { k: "custodian", v: asString(latestEvidenceBundleRetentionHandoffVerification.custodian_id) ?? "operator" },
                      { k: "verification_sha", v: (asString(latestEvidenceBundleRetentionHandoffVerification.artifact_sha256) ?? "—").slice(0, 16) },
                      { k: "handoff_status", v: asString(latestEvidenceBundleRetentionHandoffVerification.source_retention_handoff_status) ?? "—" },
                      { k: "handoff_statement", v: (asString(latestEvidenceBundleRetentionHandoffVerification.handoff_statement_computed_sha256) ?? "—").slice(0, 16) },
                      { k: "source_signoff_verification", v: asString(latestEvidenceBundleRetentionHandoffVerification.source_retention_signoff_verification_status) ?? "—" },
                      { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionHandoffVerification.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionHandoffVerification.recomputed_retention_entry_count)}` },
                      { k: "missing", v: countLabel(latestEvidenceBundleRetentionHandoffVerification.missing_entry_count) },
                      { k: "mismatched", v: countLabel(latestEvidenceBundleRetentionHandoffVerification.digest_mismatch_entry_count) },
                      { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionHandoffVerification.blockers).join("; ") || "—" },
                      { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionHandoffVerification.warnings).join("; ") || "—" },
                    ]}
                  />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}>
                <table className="dense-table">
                  <thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Handoff hash</th><th>Statement hash</th><th>Source signoff verification</th><th>Ready entries</th><th>Blockers</th><th>Artifact</th></tr></thead>
                  <tbody>
                    {evidenceBundleRetentionHandoffVerifications.slice(0, 20).map((verification, index) => (
                      <tr key={`${verification.artifact_path ?? "retention-handoff-verification"}-${index}`}>
                        <td>{verification.tracking_id ?? "—"}</td>
                        <td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td>
                        <td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td>
                        <td>{String(verification.retention_handoff_artifact_hash_valid ?? false)}</td>
                        <td>{String(verification.handoff_statement_hash_valid ?? false)}</td>
                        <td>{String(verification.retention_signoff_verification_artifact_hash_valid ?? false)}</td>
                        <td>{verification.recomputed_retention_ready_entry_count ?? 0} / {verification.recomputed_retention_entry_count ?? 0}</td>
                        <td>{verification.blocker_count ?? 0}</td>
                        <td>{verification.artifact_path ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </Pane>



        <Pane title="Evidence-chain retention handoff acceptance" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention handoff acceptance", rawJson: { evidenceBundleRetentionHandoffAcceptances, latestEvidenceBundleRetentionHandoffAcceptance } })}>
          {evidenceBundleRetentionHandoffAcceptances.length === 0 && !latestEvidenceBundleRetentionHandoffAcceptance ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}>
              <p className="muted" style={{ margin: 0 }}>No retention handoff acceptance certificate yet.</p>
              <pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker accept-evidence-bundle-retention-handoff</pre>
            </div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionHandoffAcceptance ? (
                <div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}>
                  <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}>
                    <StatusBadge raw={asString(latestEvidenceBundleRetentionHandoffAcceptance.acceptance_status) ?? "UNKNOWN"} />
                    <StatusBadge raw={asString(latestEvidenceBundleRetentionHandoffAcceptance.trust_banner) ?? "TRUST_RESTRICTED"} />
                    <SeverityBadge severity={asBool(latestEvidenceBundleRetentionHandoffAcceptance.retention_handoff_verification_artifact_hash_valid) ? "ok" : "warn"}>handoff verification hash</SeverityBadge>
                    <SeverityBadge severity={asBool(latestEvidenceBundleRetentionHandoffAcceptance.retention_handoff_artifact_hash_valid) ? "ok" : "warn"}>handoff hash</SeverityBadge>
                    <SeverityBadge severity={asBool(latestEvidenceBundleRetentionHandoffAcceptance.handoff_statement_hash_valid) ? "ok" : "warn"}>handoff statement</SeverityBadge>
                  </div>
                  <TermKV rows={[
                    { k: "tracking_id", v: asString(latestEvidenceBundleRetentionHandoffAcceptance.tracking_id) ?? "—" },
                    { k: "custodian", v: asString(latestEvidenceBundleRetentionHandoffAcceptance.accepting_custodian_id) ?? "operator" },
                    { k: "custody_location", v: asString(latestEvidenceBundleRetentionHandoffAcceptance.custody_location) ?? "local-retention" },
                    { k: "acceptance_sha", v: (asString(latestEvidenceBundleRetentionHandoffAcceptance.artifact_sha256) ?? "—").slice(0, 16) },
                    { k: "statement", v: (asString(latestEvidenceBundleRetentionHandoffAcceptance.acceptance_statement_sha256) ?? "—").slice(0, 16) },
                    { k: "source_handoff_verification", v: asString(latestEvidenceBundleRetentionHandoffAcceptance.source_retention_handoff_verification_status) ?? "—" },
                    { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionHandoffAcceptance.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionHandoffAcceptance.recomputed_retention_entry_count)}` },
                    { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionHandoffAcceptance.blockers).join("; ") || "—" },
                    { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionHandoffAcceptance.warnings).join("; ") || "—" },
                  ]} />
                </div>
              ) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Custodian</th><th>Location</th><th>Ready entries</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>
                {evidenceBundleRetentionHandoffAcceptances.slice(0, 20).map((acceptance, index) => (<tr key={`${acceptance.artifact_path ?? "retention-handoff-acceptance"}-${index}`}><td>{acceptance.tracking_id ?? "—"}</td><td><StatusBadge raw={acceptance.acceptance_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={acceptance.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{acceptance.accepting_custodian_id ?? "operator"}</td><td>{acceptance.custody_location ?? "—"}</td><td>{acceptance.recomputed_retention_ready_entry_count ?? 0} / {acceptance.recomputed_retention_entry_count ?? 0}</td><td>{acceptance.blocker_count ?? 0}</td><td>{acceptance.artifact_path ?? "—"}</td></tr>))}
              </tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention handoff acceptance verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention handoff acceptance verification", rawJson: { evidenceBundleRetentionHandoffAcceptanceVerifications, latestEvidenceBundleRetentionHandoffAcceptanceVerification } })}>
          {evidenceBundleRetentionHandoffAcceptanceVerifications.length === 0 && !latestEvidenceBundleRetentionHandoffAcceptanceVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No handoff acceptance verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-handoff-acceptance</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionHandoffAcceptanceVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionHandoffAcceptanceVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionHandoffAcceptanceVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionHandoffAcceptanceVerification.retention_handoff_acceptance_artifact_hash_valid) ? "ok" : "warn"}>acceptance hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionHandoffAcceptanceVerification.acceptance_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionHandoffAcceptanceVerification.retention_handoff_verification_artifact_hash_valid) ? "ok" : "warn"}>source verification</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionHandoffAcceptanceVerification.tracking_id) ?? "—" }, { k: "verification_sha", v: (asString(latestEvidenceBundleRetentionHandoffAcceptanceVerification.artifact_sha256) ?? "—").slice(0, 16) }, { k: "acceptance_status", v: asString(latestEvidenceBundleRetentionHandoffAcceptanceVerification.source_retention_handoff_acceptance_status) ?? "—" }, { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionHandoffAcceptanceVerification.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionHandoffAcceptanceVerification.recomputed_retention_entry_count)}` }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionHandoffAcceptanceVerification.blockers).join("; ") || "—" }, { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionHandoffAcceptanceVerification.warnings).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Acceptance hash</th><th>Statement hash</th><th>Ready entries</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionHandoffAcceptanceVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-handoff-acceptance-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_handoff_acceptance_artifact_hash_valid ?? false)}</td><td>{String(verification.acceptance_statement_hash_valid ?? false)}</td><td>{verification.recomputed_retention_ready_entry_count ?? 0} / {verification.recomputed_retention_entry_count ?? 0}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody register" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody register", rawJson: { evidenceBundleRetentionCustodyRegisters, latestEvidenceBundleRetentionCustodyRegister } })}>
          {evidenceBundleRetentionCustodyRegisters.length === 0 && !latestEvidenceBundleRetentionCustodyRegister ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody register entry yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker register-evidence-bundle-retention-custody</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyRegister ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyRegister.register_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyRegister.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyRegister.retention_handoff_acceptance_verification_artifact_hash_valid) ? "ok" : "warn"}>acceptance verification</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyRegister.acceptance_statement_hash_valid) ? "ok" : "warn"}>acceptance statement</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyRegister.tracking_id) ?? "—" }, { k: "register_id", v: asString(latestEvidenceBundleRetentionCustodyRegister.custody_register_id) ?? "—" }, { k: "registered_by", v: asString(latestEvidenceBundleRetentionCustodyRegister.registered_by) ?? "operator" }, { k: "custody_location", v: asString(latestEvidenceBundleRetentionCustodyRegister.custody_location) ?? "local-retention" }, { k: "register_sha", v: (asString(latestEvidenceBundleRetentionCustodyRegister.artifact_sha256) ?? "—").slice(0, 16) }, { k: "statement", v: (asString(latestEvidenceBundleRetentionCustodyRegister.custody_register_statement_sha256) ?? "—").slice(0, 16) }, { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionCustodyRegister.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionCustodyRegister.recomputed_retention_entry_count)}` }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyRegister.blockers).join("; ") || "—" }, { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionCustodyRegister.warnings).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Register ID</th><th>Location</th><th>Ready entries</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyRegisters.slice(0, 20).map((entry, index) => (<tr key={`${entry.artifact_path ?? "retention-custody-register"}-${index}`}><td>{entry.tracking_id ?? "—"}</td><td><StatusBadge raw={entry.register_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={entry.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{entry.custody_register_id ?? "—"}</td><td>{entry.custody_location ?? "—"}</td><td>{entry.recomputed_retention_ready_entry_count ?? 0} / {entry.recomputed_retention_entry_count ?? 0}</td><td>{entry.blocker_count ?? 0}</td><td>{entry.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody register verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody register verification", rawJson: { evidenceBundleRetentionCustodyRegisterVerifications, latestEvidenceBundleRetentionCustodyRegisterVerification } })}>
          {evidenceBundleRetentionCustodyRegisterVerifications.length === 0 && !latestEvidenceBundleRetentionCustodyRegisterVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody register verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-register</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyRegisterVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyRegisterVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyRegisterVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyRegisterVerification.retention_custody_register_artifact_hash_valid) ? "ok" : "warn"}>register hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyRegisterVerification.custody_register_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyRegisterVerification.tracking_id) ?? "—" }, { k: "register_id", v: asString(latestEvidenceBundleRetentionCustodyRegisterVerification.custody_register_id) ?? "—" }, { k: "verification_sha", v: (asString(latestEvidenceBundleRetentionCustodyRegisterVerification.artifact_sha256) ?? "—").slice(0, 16) }, { k: "register_status", v: asString(latestEvidenceBundleRetentionCustodyRegisterVerification.source_retention_custody_register_status) ?? "—" }, { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionCustodyRegisterVerification.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionCustodyRegisterVerification.recomputed_retention_entry_count)}` }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyRegisterVerification.blockers).join("; ") || "—" }, { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionCustodyRegisterVerification.warnings).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Register hash</th><th>Statement hash</th><th>Ready entries</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyRegisterVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-register-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_register_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_register_statement_hash_valid ?? false)}</td><td>{verification.recomputed_retention_ready_entry_count ?? 0} / {verification.recomputed_retention_entry_count ?? 0}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody seal" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody seal", rawJson: { evidenceBundleRetentionCustodySeals, latestEvidenceBundleRetentionCustodySeal } })}>
          {evidenceBundleRetentionCustodySeals.length === 0 && !latestEvidenceBundleRetentionCustodySeal ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody seal artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker seal-evidence-bundle-retention-custody</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodySeal ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodySeal.seal_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodySeal.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodySeal.retention_custody_register_verification_artifact_hash_valid) ? "ok" : "warn"}>register verification</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodySeal.custody_seal_statement_sha256) ? "ok" : "warn"}>seal statement</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodySeal.tracking_id) ?? "—" }, { k: "seal_id", v: asString(latestEvidenceBundleRetentionCustodySeal.custody_seal_id) ?? "—" }, { k: "sealed_by", v: asString(latestEvidenceBundleRetentionCustodySeal.sealed_by) ?? "operator" }, { k: "custody_location", v: asString(latestEvidenceBundleRetentionCustodySeal.custody_location) ?? "local-retention" }, { k: "seal_sha", v: (asString(latestEvidenceBundleRetentionCustodySeal.artifact_sha256) ?? "—").slice(0, 16) }, { k: "statement", v: (asString(latestEvidenceBundleRetentionCustodySeal.custody_seal_statement_sha256) ?? "—").slice(0, 16) }, { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionCustodySeal.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionCustodySeal.recomputed_retention_entry_count)}` }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodySeal.blockers).join("; ") || "—" }, { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionCustodySeal.warnings).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Seal ID</th><th>Location</th><th>Ready entries</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodySeals.slice(0, 20).map((entry, index) => (<tr key={`${entry.artifact_path ?? "retention-custody-seal"}-${index}`}><td>{entry.tracking_id ?? "—"}</td><td><StatusBadge raw={entry.seal_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={entry.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{entry.custody_seal_id ?? "—"}</td><td>{entry.custody_location ?? "—"}</td><td>{entry.recomputed_retention_ready_entry_count ?? 0} / {entry.recomputed_retention_entry_count ?? 0}</td><td>{entry.blocker_count ?? 0}</td><td>{entry.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody seal verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody seal verification", rawJson: { evidenceBundleRetentionCustodySealVerifications, latestEvidenceBundleRetentionCustodySealVerification } })}>
          {evidenceBundleRetentionCustodySealVerifications.length === 0 && !latestEvidenceBundleRetentionCustodySealVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody seal verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-seal</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodySealVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodySealVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodySealVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodySealVerification.retention_custody_seal_artifact_hash_valid) ? "ok" : "warn"}>seal hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodySealVerification.custody_seal_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodySealVerification.tracking_id) ?? "—" }, { k: "seal_id", v: asString(latestEvidenceBundleRetentionCustodySealVerification.custody_seal_id) ?? "—" }, { k: "verification_sha", v: (asString(latestEvidenceBundleRetentionCustodySealVerification.artifact_sha256) ?? "—").slice(0, 16) }, { k: "seal_status", v: asString(latestEvidenceBundleRetentionCustodySealVerification.source_retention_custody_seal_status) ?? "—" }, { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionCustodySealVerification.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionCustodySealVerification.recomputed_retention_entry_count)}` }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodySealVerification.blockers).join("; ") || "—" }, { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionCustodySealVerification.warnings).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Seal hash</th><th>Statement hash</th><th>Ready entries</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodySealVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-seal-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_seal_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_seal_statement_hash_valid ?? false)}</td><td>{verification.recomputed_retention_ready_entry_count ?? 0} / {verification.recomputed_retention_entry_count ?? 0}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody audit" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody audit", rawJson: { evidenceBundleRetentionCustodyAudits, latestEvidenceBundleRetentionCustodyAudit } })}>
          {evidenceBundleRetentionCustodyAudits.length === 0 && !latestEvidenceBundleRetentionCustodyAudit ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody audit artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker audit-evidence-bundle-retention-custody</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyAudit ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyAudit.audit_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyAudit.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyAudit.retention_custody_seal_verification_artifact_hash_valid) ? "ok" : "warn"}>seal verification</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyAudit.custody_audit_statement_sha256) ? "ok" : "warn"}>audit statement</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyAudit.tracking_id) ?? "—" }, { k: "audit_id", v: asString(latestEvidenceBundleRetentionCustodyAudit.custody_audit_id) ?? "—" }, { k: "audited_by", v: asString(latestEvidenceBundleRetentionCustodyAudit.audited_by) ?? "operator" }, { k: "custody_location", v: asString(latestEvidenceBundleRetentionCustodyAudit.custody_location) ?? "local-retention" }, { k: "audit_sha", v: (asString(latestEvidenceBundleRetentionCustodyAudit.artifact_sha256) ?? "—").slice(0, 16) }, { k: "statement", v: (asString(latestEvidenceBundleRetentionCustodyAudit.custody_audit_statement_sha256) ?? "—").slice(0, 16) }, { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionCustodyAudit.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionCustodyAudit.recomputed_retention_entry_count)}` }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyAudit.blockers).join("; ") || "—" }, { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionCustodyAudit.warnings).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Audit ID</th><th>Location</th><th>Ready entries</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyAudits.slice(0, 20).map((entry, index) => (<tr key={`${entry.artifact_path ?? "retention-custody-audit"}-${index}`}><td>{entry.tracking_id ?? "—"}</td><td><StatusBadge raw={entry.audit_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={entry.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{entry.custody_audit_id ?? "—"}</td><td>{entry.custody_location ?? "—"}</td><td>{entry.recomputed_retention_ready_entry_count ?? 0} / {entry.recomputed_retention_entry_count ?? 0}</td><td>{entry.blocker_count ?? 0}</td><td>{entry.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody audit verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody audit verification", rawJson: { evidenceBundleRetentionCustodyAuditVerifications, latestEvidenceBundleRetentionCustodyAuditVerification } })}>
          {evidenceBundleRetentionCustodyAuditVerifications.length === 0 && !latestEvidenceBundleRetentionCustodyAuditVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody audit verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-audit</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyAuditVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyAuditVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyAuditVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyAuditVerification.retention_custody_audit_artifact_hash_valid) ? "ok" : "warn"}>audit hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyAuditVerification.custody_audit_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyAuditVerification.tracking_id) ?? "—" }, { k: "audit_id", v: asString(latestEvidenceBundleRetentionCustodyAuditVerification.custody_audit_id) ?? "—" }, { k: "verification_sha", v: (asString(latestEvidenceBundleRetentionCustodyAuditVerification.artifact_sha256) ?? "—").slice(0, 16) }, { k: "audit_status", v: asString(latestEvidenceBundleRetentionCustodyAuditVerification.source_retention_custody_audit_status) ?? "—" }, { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionCustodyAuditVerification.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionCustodyAuditVerification.recomputed_retention_entry_count)}` }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyAuditVerification.blockers).join("; ") || "—" }, { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionCustodyAuditVerification.warnings).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Audit hash</th><th>Statement hash</th><th>Ready entries</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyAuditVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-audit-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_audit_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_audit_statement_hash_valid ?? false)}</td><td>{verification.recomputed_retention_ready_entry_count ?? 0} / {verification.recomputed_retention_entry_count ?? 0}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody continuity" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody continuity", rawJson: { evidenceBundleRetentionCustodyContinuities, latestEvidenceBundleRetentionCustodyContinuity } })}>
          {evidenceBundleRetentionCustodyContinuities.length === 0 && !latestEvidenceBundleRetentionCustodyContinuity ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody continuity attestation yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker attest-evidence-bundle-retention-custody-continuity</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyContinuity ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyContinuity.continuity_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyContinuity.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyContinuity.retention_custody_audit_verification_artifact_hash_valid) ? "ok" : "warn"}>audit verification</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyContinuity.custody_continuity_statement_sha256) ? "ok" : "warn"}>continuity statement</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyContinuity.tracking_id) ?? "—" }, { k: "continuity_id", v: asString(latestEvidenceBundleRetentionCustodyContinuity.custody_continuity_id) ?? "—" }, { k: "attested_by", v: asString(latestEvidenceBundleRetentionCustodyContinuity.attested_by) ?? "operator" }, { k: "custody_location", v: asString(latestEvidenceBundleRetentionCustodyContinuity.custody_location) ?? "local-retention" }, { k: "continuity_sha", v: (asString(latestEvidenceBundleRetentionCustodyContinuity.artifact_sha256) ?? "—").slice(0, 16) }, { k: "statement", v: (asString(latestEvidenceBundleRetentionCustodyContinuity.custody_continuity_statement_sha256) ?? "—").slice(0, 16) }, { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionCustodyContinuity.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionCustodyContinuity.recomputed_retention_entry_count)}` }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyContinuity.blockers).join("; ") || "—" }, { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionCustodyContinuity.warnings).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Continuity ID</th><th>Location</th><th>Ready entries</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyContinuities.slice(0, 20).map((entry, index) => (<tr key={`${entry.artifact_path ?? "retention-custody-continuity"}-${index}`}><td>{entry.tracking_id ?? "—"}</td><td><StatusBadge raw={entry.continuity_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={entry.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{entry.custody_continuity_id ?? "—"}</td><td>{entry.custody_location ?? "—"}</td><td>{entry.recomputed_retention_ready_entry_count ?? 0} / {entry.recomputed_retention_entry_count ?? 0}</td><td>{entry.blocker_count ?? 0}</td><td>{entry.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody continuity verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody continuity verification", rawJson: { evidenceBundleRetentionCustodyContinuityVerifications, latestEvidenceBundleRetentionCustodyContinuityVerification } })}>
          {evidenceBundleRetentionCustodyContinuityVerifications.length === 0 && !latestEvidenceBundleRetentionCustodyContinuityVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody continuity verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-continuity</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyContinuityVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyContinuityVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyContinuityVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyContinuityVerification.retention_custody_continuity_artifact_hash_valid) ? "ok" : "warn"}>continuity hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyContinuityVerification.custody_continuity_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyContinuityVerification.tracking_id) ?? "—" }, { k: "continuity_id", v: asString(latestEvidenceBundleRetentionCustodyContinuityVerification.custody_continuity_id) ?? "—" }, { k: "verification_sha", v: (asString(latestEvidenceBundleRetentionCustodyContinuityVerification.artifact_sha256) ?? "—").slice(0, 16) }, { k: "continuity_status", v: asString(latestEvidenceBundleRetentionCustodyContinuityVerification.source_retention_custody_continuity_status) ?? "—" }, { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionCustodyContinuityVerification.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionCustodyContinuityVerification.recomputed_retention_entry_count)}` }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyContinuityVerification.blockers).join("; ") || "—" }, { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionCustodyContinuityVerification.warnings).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Continuity hash</th><th>Statement hash</th><th>Ready entries</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyContinuityVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-continuity-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_continuity_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_continuity_statement_hash_valid ?? false)}</td><td>{verification.recomputed_retention_ready_entry_count ?? 0} / {verification.recomputed_retention_entry_count ?? 0}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody review" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody review", rawJson: { evidenceBundleRetentionCustodyReviews, latestEvidenceBundleRetentionCustodyReview } })}>
          {evidenceBundleRetentionCustodyReviews.length === 0 && !latestEvidenceBundleRetentionCustodyReview ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody review artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker review-evidence-bundle-retention-custody</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyReview ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyReview.review_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyReview.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyReview.retention_custody_continuity_verification_artifact_hash_valid) ? "ok" : "warn"}>continuity verification</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyReview.custody_review_statement_sha256) ? "ok" : "warn"}>review statement</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyReview.tracking_id) ?? "—" }, { k: "review_id", v: asString(latestEvidenceBundleRetentionCustodyReview.custody_review_id) ?? "—" }, { k: "reviewed_by", v: asString(latestEvidenceBundleRetentionCustodyReview.reviewed_by) ?? "operator" }, { k: "custody_location", v: asString(latestEvidenceBundleRetentionCustodyReview.custody_location) ?? "local-retention" }, { k: "review_sha", v: (asString(latestEvidenceBundleRetentionCustodyReview.artifact_sha256) ?? "—").slice(0, 16) }, { k: "statement", v: (asString(latestEvidenceBundleRetentionCustodyReview.custody_review_statement_sha256) ?? "—").slice(0, 16) }, { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionCustodyReview.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionCustodyReview.recomputed_retention_entry_count)}` }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyReview.blockers).join("; ") || "—" }, { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionCustodyReview.warnings).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Review ID</th><th>Location</th><th>Ready entries</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyReviews.slice(0, 20).map((entry, index) => (<tr key={`${entry.artifact_path ?? "retention-custody-review"}-${index}`}><td>{entry.tracking_id ?? "—"}</td><td><StatusBadge raw={entry.review_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={entry.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{entry.custody_review_id ?? "—"}</td><td>{entry.custody_location ?? "—"}</td><td>{entry.recomputed_retention_ready_entry_count ?? 0} / {entry.recomputed_retention_entry_count ?? 0}</td><td>{entry.blocker_count ?? 0}</td><td>{entry.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody review verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody review verification", rawJson: { evidenceBundleRetentionCustodyReviewVerifications, latestEvidenceBundleRetentionCustodyReviewVerification } })}>
          {evidenceBundleRetentionCustodyReviewVerifications.length === 0 && !latestEvidenceBundleRetentionCustodyReviewVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody review verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-review</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyReviewVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyReviewVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyReviewVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyReviewVerification.retention_custody_review_artifact_hash_valid) ? "ok" : "warn"}>review hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyReviewVerification.custody_review_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyReviewVerification.tracking_id) ?? "—" }, { k: "review_id", v: asString(latestEvidenceBundleRetentionCustodyReviewVerification.custody_review_id) ?? "—" }, { k: "verification_sha", v: (asString(latestEvidenceBundleRetentionCustodyReviewVerification.artifact_sha256) ?? "—").slice(0, 16) }, { k: "review_status", v: asString(latestEvidenceBundleRetentionCustodyReviewVerification.source_retention_custody_review_status) ?? "—" }, { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionCustodyReviewVerification.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionCustodyReviewVerification.recomputed_retention_entry_count)}` }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyReviewVerification.blockers).join("; ") || "—" }, { k: "warnings", v: asStringArray(latestEvidenceBundleRetentionCustodyReviewVerification.warnings).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Review hash</th><th>Statement hash</th><th>Ready entries</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyReviewVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-review-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_review_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_review_statement_hash_valid ?? false)}</td><td>{verification.recomputed_retention_ready_entry_count ?? 0} / {verification.recomputed_retention_entry_count ?? 0}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>


        <Pane title="Evidence-chain retention custody renewal" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody renewal", rawJson: { evidenceBundleRetentionCustodyRenewals, latestEvidenceBundleRetentionCustodyRenewal } })}>
          {evidenceBundleRetentionCustodyRenewals.length === 0 && !latestEvidenceBundleRetentionCustodyRenewal ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody renewal artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker renew-evidence-bundle-retention-custody</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyRenewal ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyRenewal.renewal_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyRenewal.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyRenewal.retention_custody_review_verification_artifact_hash_valid) ? "ok" : "warn"}>review verification</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyRenewal.tracking_id) ?? "—" }, { k: "renewal_id", v: asString(latestEvidenceBundleRetentionCustodyRenewal.custody_renewal_id) ?? "—" }, { k: "renewed_by", v: asString(latestEvidenceBundleRetentionCustodyRenewal.renewed_by) ?? "operator" }, { k: "interval_days", v: String(latestEvidenceBundleRetentionCustodyRenewal.renewal_interval_days ?? "—") }, { k: "entries", v: `${countLabel(latestEvidenceBundleRetentionCustodyRenewal.recomputed_retention_ready_entry_count)} / ${countLabel(latestEvidenceBundleRetentionCustodyRenewal.recomputed_retention_entry_count)}` }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyRenewal.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Renewal ID</th><th>Interval</th><th>Ready entries</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyRenewals.slice(0, 20).map((entry, index) => (<tr key={`${entry.artifact_path ?? "retention-custody-renewal"}-${index}`}><td>{entry.tracking_id ?? "—"}</td><td><StatusBadge raw={entry.renewal_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={entry.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{entry.custody_renewal_id ?? "—"}</td><td>{entry.renewal_interval_days ?? "—"}</td><td>{entry.recomputed_retention_ready_entry_count ?? 0} / {entry.recomputed_retention_entry_count ?? 0}</td><td>{entry.blocker_count ?? 0}</td><td>{entry.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody renewal verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody renewal verification", rawJson: { evidenceBundleRetentionCustodyRenewalVerifications, latestEvidenceBundleRetentionCustodyRenewalVerification } })}>
          {evidenceBundleRetentionCustodyRenewalVerifications.length === 0 && !latestEvidenceBundleRetentionCustodyRenewalVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody renewal verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-renewal</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyRenewalVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyRenewalVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyRenewalVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyRenewalVerification.retention_custody_renewal_artifact_hash_valid) ? "ok" : "warn"}>renewal hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyRenewalVerification.custody_renewal_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyRenewalVerification.tracking_id) ?? "—" }, { k: "renewal_id", v: asString(latestEvidenceBundleRetentionCustodyRenewalVerification.custody_renewal_id) ?? "—" }, { k: "verification_sha", v: (asString(latestEvidenceBundleRetentionCustodyRenewalVerification.artifact_sha256) ?? "—").slice(0, 16) }, { k: "renewal_status", v: asString(latestEvidenceBundleRetentionCustodyRenewalVerification.source_retention_custody_renewal_status) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyRenewalVerification.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Renewal hash</th><th>Statement hash</th><th>Ready entries</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyRenewalVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-renewal-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_renewal_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_renewal_statement_hash_valid ?? false)}</td><td>{verification.recomputed_retention_ready_entry_count ?? 0} / {verification.recomputed_retention_entry_count ?? 0}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody renewal schedule" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody renewal schedule", rawJson: { evidenceBundleRetentionCustodySchedules, latestEvidenceBundleRetentionCustodySchedule } })}>
          {evidenceBundleRetentionCustodySchedules.length === 0 && !latestEvidenceBundleRetentionCustodySchedule ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody renewal schedule artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker schedule-evidence-bundle-retention-custody-renewal</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodySchedule ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodySchedule.schedule_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodySchedule.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodySchedule.retention_custody_renewal_verification_artifact_hash_valid) ? "ok" : "warn"}>renewal verification</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodySchedule.tracking_id) ?? "—" }, { k: "schedule_id", v: asString(latestEvidenceBundleRetentionCustodySchedule.custody_schedule_id) ?? "—" }, { k: "due_at", v: asString(latestEvidenceBundleRetentionCustodySchedule.next_renewal_due_at_utc) ?? "—" }, { k: "reminder_days", v: String(latestEvidenceBundleRetentionCustodySchedule.reminder_days_before_due ?? "—") }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodySchedule.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Due</th><th>Interval</th><th>Reminder</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodySchedules.slice(0, 20).map((entry, index) => (<tr key={`${entry.artifact_path ?? "retention-custody-schedule"}-${index}`}><td>{entry.tracking_id ?? "—"}</td><td><StatusBadge raw={entry.schedule_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={entry.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{entry.next_renewal_due_at_utc ?? "—"}</td><td>{entry.renewal_interval_days ?? "—"}</td><td>{entry.reminder_days_before_due ?? "—"}</td><td>{entry.blocker_count ?? 0}</td><td>{entry.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody renewal schedule verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody renewal schedule verification", rawJson: { evidenceBundleRetentionCustodyScheduleVerifications, latestEvidenceBundleRetentionCustodyScheduleVerification } })}>
          {evidenceBundleRetentionCustodyScheduleVerifications.length === 0 && !latestEvidenceBundleRetentionCustodyScheduleVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody renewal schedule verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-schedule</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyScheduleVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyScheduleVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyScheduleVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyScheduleVerification.retention_custody_schedule_artifact_hash_valid) ? "ok" : "warn"}>schedule hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyScheduleVerification.custody_schedule_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyScheduleVerification.tracking_id) ?? "—" }, { k: "schedule_id", v: asString(latestEvidenceBundleRetentionCustodyScheduleVerification.custody_schedule_id) ?? "—" }, { k: "due_at", v: asString(latestEvidenceBundleRetentionCustodyScheduleVerification.next_renewal_due_at_utc) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyScheduleVerification.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Schedule hash</th><th>Statement hash</th><th>Due</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyScheduleVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-schedule-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_schedule_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_schedule_statement_hash_valid ?? false)}</td><td>{verification.next_renewal_due_at_utc ?? "—"}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>



        <Pane title="Evidence-chain retention custody renewal notice" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody renewal notice", rawJson: { evidenceBundleRetentionCustodyNotices, latestEvidenceBundleRetentionCustodyNotice } })}>
          {evidenceBundleRetentionCustodyNotices.length === 0 && !latestEvidenceBundleRetentionCustodyNotice ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody renewal notice artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker notice-evidence-bundle-retention-custody-renewal</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyNotice ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyNotice.notice_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyNotice.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyNotice.retention_custody_schedule_verification_artifact_hash_valid) ? "ok" : "warn"}>schedule verification</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyNotice.tracking_id) ?? "—" }, { k: "notice_id", v: asString(latestEvidenceBundleRetentionCustodyNotice.custody_notice_id) ?? "—" }, { k: "due_at", v: asString(latestEvidenceBundleRetentionCustodyNotice.next_renewal_due_at_utc) ?? "—" }, { k: "days_until_due", v: String(latestEvidenceBundleRetentionCustodyNotice.days_until_due ?? "—") }, { k: "message", v: asString(latestEvidenceBundleRetentionCustodyNotice.notice_message) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyNotice.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Due</th><th>Days</th><th>Message</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyNotices.slice(0, 20).map((entry, index) => (<tr key={`${entry.artifact_path ?? "retention-custody-notice"}-${index}`}><td>{entry.tracking_id ?? "—"}</td><td><StatusBadge raw={entry.notice_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={entry.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{entry.next_renewal_due_at_utc ?? "—"}</td><td>{entry.days_until_due ?? "—"}</td><td>{entry.notice_message ?? "—"}</td><td>{entry.blocker_count ?? 0}</td><td>{entry.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody renewal notice verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody renewal notice verification", rawJson: { evidenceBundleRetentionCustodyNoticeVerifications, latestEvidenceBundleRetentionCustodyNoticeVerification } })}>
          {evidenceBundleRetentionCustodyNoticeVerifications.length === 0 && !latestEvidenceBundleRetentionCustodyNoticeVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody renewal notice verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-notice</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyNoticeVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyNoticeVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyNoticeVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyNoticeVerification.retention_custody_notice_artifact_hash_valid) ? "ok" : "warn"}>notice hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyNoticeVerification.custody_notice_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyNoticeVerification.tracking_id) ?? "—" }, { k: "notice_id", v: asString(latestEvidenceBundleRetentionCustodyNoticeVerification.custody_notice_id) ?? "—" }, { k: "due_at", v: asString(latestEvidenceBundleRetentionCustodyNoticeVerification.next_renewal_due_at_utc) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyNoticeVerification.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Notice hash</th><th>Statement hash</th><th>Due</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyNoticeVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-notice-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_notice_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_notice_statement_hash_valid ?? false)}</td><td>{verification.next_renewal_due_at_utc ?? "—"}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>



        <Pane title="Evidence-chain retention custody renewal notice acknowledgment" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody renewal notice acknowledgment", rawJson: { evidenceBundleRetentionCustodyAcknowledgments, latestEvidenceBundleRetentionCustodyAcknowledgment } })}>
          {evidenceBundleRetentionCustodyAcknowledgments.length === 0 && !latestEvidenceBundleRetentionCustodyAcknowledgment ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody renewal notice acknowledgment artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker acknowledge-evidence-bundle-retention-custody-notice</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyAcknowledgment ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyAcknowledgment.acknowledgment_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyAcknowledgment.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyAcknowledgment.retention_custody_notice_verification_artifact_hash_valid) ? "ok" : "warn"}>notice verification</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyAcknowledgment.tracking_id) ?? "—" }, { k: "acknowledgment_id", v: asString(latestEvidenceBundleRetentionCustodyAcknowledgment.custody_acknowledgment_id) ?? "—" }, { k: "notice_id", v: asString(latestEvidenceBundleRetentionCustodyAcknowledgment.custody_notice_id) ?? "—" }, { k: "due_at", v: asString(latestEvidenceBundleRetentionCustodyAcknowledgment.next_renewal_due_at_utc) ?? "—" }, { k: "acknowledged_by", v: asString(latestEvidenceBundleRetentionCustodyAcknowledgment.acknowledged_by) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyAcknowledgment.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Notice</th><th>Due</th><th>Acknowledged by</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyAcknowledgments.slice(0, 20).map((entry, index) => (<tr key={`${entry.artifact_path ?? "retention-custody-acknowledgment"}-${index}`}><td>{entry.tracking_id ?? "—"}</td><td><StatusBadge raw={entry.acknowledgment_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={entry.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{entry.custody_notice_id ?? "—"}</td><td>{entry.next_renewal_due_at_utc ?? "—"}</td><td>{entry.acknowledged_by ?? "—"}</td><td>{entry.blocker_count ?? 0}</td><td>{entry.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody renewal notice acknowledgment verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody renewal notice acknowledgment verification", rawJson: { evidenceBundleRetentionCustodyAcknowledgmentVerifications, latestEvidenceBundleRetentionCustodyAcknowledgmentVerification } })}>
          {evidenceBundleRetentionCustodyAcknowledgmentVerifications.length === 0 && !latestEvidenceBundleRetentionCustodyAcknowledgmentVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody renewal notice acknowledgment verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-acknowledgment</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyAcknowledgmentVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyAcknowledgmentVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyAcknowledgmentVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyAcknowledgmentVerification.retention_custody_acknowledgment_artifact_hash_valid) ? "ok" : "warn"}>ack hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyAcknowledgmentVerification.custody_acknowledgment_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyAcknowledgmentVerification.tracking_id) ?? "—" }, { k: "acknowledgment_id", v: asString(latestEvidenceBundleRetentionCustodyAcknowledgmentVerification.custody_acknowledgment_id) ?? "—" }, { k: "notice_id", v: asString(latestEvidenceBundleRetentionCustodyAcknowledgmentVerification.custody_notice_id) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyAcknowledgmentVerification.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Ack hash</th><th>Statement hash</th><th>Notice</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyAcknowledgmentVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-acknowledgment-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_acknowledgment_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_acknowledgment_statement_hash_valid ?? false)}</td><td>{verification.custody_notice_id ?? "—"}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody renewal completion" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody renewal completion", rawJson: { evidenceBundleRetentionCustodyCompletions, latestEvidenceBundleRetentionCustodyCompletion } })}>
          {evidenceBundleRetentionCustodyCompletions.length === 0 && !latestEvidenceBundleRetentionCustodyCompletion ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody renewal completion artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker complete-evidence-bundle-retention-custody-renewal</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyCompletion ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyCompletion.completion_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyCompletion.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyCompletion.retention_custody_acknowledgment_verification_artifact_hash_valid) ? "ok" : "warn"}>ack verification</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyCompletion.tracking_id) ?? "—" }, { k: "completion_id", v: asString(latestEvidenceBundleRetentionCustodyCompletion.custody_completion_id) ?? "—" }, { k: "acknowledgment_id", v: asString(latestEvidenceBundleRetentionCustodyCompletion.custody_acknowledgment_id) ?? "—" }, { k: "due_at", v: asString(latestEvidenceBundleRetentionCustodyCompletion.next_renewal_due_at_utc) ?? "—" }, { k: "completed_by", v: asString(latestEvidenceBundleRetentionCustodyCompletion.completed_by) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyCompletion.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Ack</th><th>Due</th><th>Completed by</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyCompletions.slice(0, 20).map((entry, index) => (<tr key={`${entry.artifact_path ?? "retention-custody-completion"}-${index}`}><td>{entry.tracking_id ?? "—"}</td><td><StatusBadge raw={entry.completion_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={entry.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{entry.custody_acknowledgment_id ?? "—"}</td><td>{entry.next_renewal_due_at_utc ?? "—"}</td><td>{entry.completed_by ?? "—"}</td><td>{entry.blocker_count ?? 0}</td><td>{entry.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody renewal completion verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody renewal completion verification", rawJson: { evidenceBundleRetentionCustodyCompletionVerifications, latestEvidenceBundleRetentionCustodyCompletionVerification } })}>
          {evidenceBundleRetentionCustodyCompletionVerifications.length === 0 && !latestEvidenceBundleRetentionCustodyCompletionVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody renewal completion verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-completion</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyCompletionVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyCompletionVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyCompletionVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyCompletionVerification.retention_custody_completion_artifact_hash_valid) ? "ok" : "warn"}>completion hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyCompletionVerification.custody_completion_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyCompletionVerification.tracking_id) ?? "—" }, { k: "completion_id", v: asString(latestEvidenceBundleRetentionCustodyCompletionVerification.custody_completion_id) ?? "—" }, { k: "acknowledgment_id", v: asString(latestEvidenceBundleRetentionCustodyCompletionVerification.custody_acknowledgment_id) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyCompletionVerification.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Completion hash</th><th>Statement hash</th><th>Ack</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyCompletionVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-completion-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_completion_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_completion_statement_hash_valid ?? false)}</td><td>{verification.custody_acknowledgment_id ?? "—"}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>


        <Pane title="Evidence-chain retention custody renewal closeout" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody renewal closeout", rawJson: { evidenceBundleRetentionCustodyCloseouts, latestEvidenceBundleRetentionCustodyCloseout } })}>
          {evidenceBundleRetentionCustodyCloseouts.length === 0 && !latestEvidenceBundleRetentionCustodyCloseout ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody renewal closeout artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker closeout-evidence-bundle-retention-custody-renewal</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyCloseout ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyCloseout.closeout_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyCloseout.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyCloseout.retention_custody_completion_verification_artifact_hash_valid) ? "ok" : "warn"}>completion verification</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyCloseout.tracking_id) ?? "—" }, { k: "closeout_id", v: asString(latestEvidenceBundleRetentionCustodyCloseout.custody_closeout_id) ?? "—" }, { k: "completion_id", v: asString(latestEvidenceBundleRetentionCustodyCloseout.custody_completion_id) ?? "—" }, { k: "due_at", v: asString(latestEvidenceBundleRetentionCustodyCloseout.next_renewal_due_at_utc) ?? "—" }, { k: "closed_out_by", v: asString(latestEvidenceBundleRetentionCustodyCloseout.closed_out_by) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyCloseout.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Completion</th><th>Due</th><th>Closed out by</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyCloseouts.slice(0, 20).map((entry, index) => (<tr key={`${entry.artifact_path ?? "retention-custody-closeout"}-${index}`}><td>{entry.tracking_id ?? "—"}</td><td><StatusBadge raw={entry.closeout_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={entry.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{entry.custody_completion_id ?? "—"}</td><td>{entry.next_renewal_due_at_utc ?? "—"}</td><td>{entry.closed_out_by ?? "—"}</td><td>{entry.blocker_count ?? 0}</td><td>{entry.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody closeout verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody closeout verification", rawJson: { evidenceBundleRetentionCustodyCloseoutVerifications, latestEvidenceBundleRetentionCustodyCloseoutVerification } })}>
          {evidenceBundleRetentionCustodyCloseoutVerifications.length === 0 && !latestEvidenceBundleRetentionCustodyCloseoutVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody closeout verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-closeout</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyCloseoutVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyCloseoutVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyCloseoutVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyCloseoutVerification.retention_custody_closeout_artifact_hash_valid) ? "ok" : "warn"}>closeout hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyCloseoutVerification.custody_closeout_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyCloseoutVerification.tracking_id) ?? "—" }, { k: "closeout_id", v: asString(latestEvidenceBundleRetentionCustodyCloseoutVerification.custody_closeout_id) ?? "—" }, { k: "completion_id", v: asString(latestEvidenceBundleRetentionCustodyCloseoutVerification.custody_completion_id) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyCloseoutVerification.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Closeout hash</th><th>Statement hash</th><th>Completion</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyCloseoutVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-closeout-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_closeout_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_closeout_statement_hash_valid ?? false)}</td><td>{verification.custody_completion_id ?? "—"}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody archive" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody archive", rawJson: { evidenceBundleRetentionCustodyArchives, latestEvidenceBundleRetentionCustodyArchive } })}>
          {evidenceBundleRetentionCustodyArchives.length === 0 && !latestEvidenceBundleRetentionCustodyArchive ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody archive artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker archive-evidence-bundle-retention-custody-closeout</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyArchive ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyArchive.archive_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyArchive.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyArchive.retention_custody_closeout_verification_artifact_hash_valid) ? "ok" : "warn"}>closeout verification</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyArchive.tracking_id) ?? "—" }, { k: "archive_id", v: asString(latestEvidenceBundleRetentionCustodyArchive.custody_archive_id) ?? "—" }, { k: "closeout_id", v: asString(latestEvidenceBundleRetentionCustodyArchive.custody_closeout_id) ?? "—" }, { k: "archived_by", v: asString(latestEvidenceBundleRetentionCustodyArchive.archived_by) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyArchive.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Archive</th><th>Closeout</th><th>Archived by</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyArchives.slice(0, 20).map((entry, index) => (<tr key={`${entry.artifact_path ?? "retention-custody-archive"}-${index}`}><td>{entry.tracking_id ?? "—"}</td><td><StatusBadge raw={entry.archive_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={entry.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{entry.custody_archive_id ?? "—"}</td><td>{entry.custody_closeout_id ?? "—"}</td><td>{entry.archived_by ?? "—"}</td><td>{entry.blocker_count ?? 0}</td><td>{entry.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody archive verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody archive verification", rawJson: { evidenceBundleRetentionCustodyArchiveVerifications, latestEvidenceBundleRetentionCustodyArchiveVerification } })}>
          {evidenceBundleRetentionCustodyArchiveVerifications.length === 0 && !latestEvidenceBundleRetentionCustodyArchiveVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody archive verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-archive</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyArchiveVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyArchiveVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyArchiveVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyArchiveVerification.retention_custody_archive_artifact_hash_valid) ? "ok" : "warn"}>archive hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyArchiveVerification.custody_archive_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyArchiveVerification.tracking_id) ?? "—" }, { k: "archive_id", v: asString(latestEvidenceBundleRetentionCustodyArchiveVerification.custody_archive_id) ?? "—" }, { k: "closeout_id", v: asString(latestEvidenceBundleRetentionCustodyArchiveVerification.custody_closeout_id) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyArchiveVerification.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Archive hash</th><th>Statement hash</th><th>Archive</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyArchiveVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-archive-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_archive_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_archive_statement_hash_valid ?? false)}</td><td>{verification.custody_archive_id ?? "—"}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody retrieval" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody retrieval", rawJson: { evidenceBundleRetentionCustodyRetrievals, latestEvidenceBundleRetentionCustodyRetrieval } })}>
          {evidenceBundleRetentionCustodyRetrievals.length === 0 && !latestEvidenceBundleRetentionCustodyRetrieval ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody retrieval artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker retrieve-evidence-bundle-retention-custody-archive</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyRetrieval ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyRetrieval.retrieval_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyRetrieval.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyRetrieval.retention_custody_archive_verification_artifact_hash_valid) ? "ok" : "warn"}>archive verification</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyRetrieval.tracking_id) ?? "—" }, { k: "retrieval_id", v: asString(latestEvidenceBundleRetentionCustodyRetrieval.custody_retrieval_id) ?? "—" }, { k: "archive_id", v: asString(latestEvidenceBundleRetentionCustodyRetrieval.custody_archive_id) ?? "—" }, { k: "retrieved_by", v: asString(latestEvidenceBundleRetentionCustodyRetrieval.retrieved_by) ?? "—" }, { k: "purpose", v: asString(latestEvidenceBundleRetentionCustodyRetrieval.retrieval_purpose) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyRetrieval.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Retrieval</th><th>Archive</th><th>Retrieved by</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyRetrievals.slice(0, 20).map((entry, index) => (<tr key={`${entry.artifact_path ?? "retention-custody-retrieval"}-${index}`}><td>{entry.tracking_id ?? "—"}</td><td><StatusBadge raw={entry.retrieval_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={entry.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{entry.custody_retrieval_id ?? "—"}</td><td>{entry.custody_archive_id ?? "—"}</td><td>{entry.retrieved_by ?? "—"}</td><td>{entry.blocker_count ?? 0}</td><td>{entry.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody retrieval verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody retrieval verification", rawJson: { evidenceBundleRetentionCustodyRetrievalVerifications, latestEvidenceBundleRetentionCustodyRetrievalVerification } })}>
          {evidenceBundleRetentionCustodyRetrievalVerifications.length === 0 && !latestEvidenceBundleRetentionCustodyRetrievalVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody retrieval verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-retrieval</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyRetrievalVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyRetrievalVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyRetrievalVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyRetrievalVerification.retention_custody_retrieval_artifact_hash_valid) ? "ok" : "warn"}>retrieval hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyRetrievalVerification.custody_retrieval_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyRetrievalVerification.tracking_id) ?? "—" }, { k: "retrieval_id", v: asString(latestEvidenceBundleRetentionCustodyRetrievalVerification.custody_retrieval_id) ?? "—" }, { k: "archive_id", v: asString(latestEvidenceBundleRetentionCustodyRetrievalVerification.custody_archive_id) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyRetrievalVerification.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Retrieval hash</th><th>Statement hash</th><th>Retrieval</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyRetrievalVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-retrieval-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_retrieval_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_retrieval_statement_hash_valid ?? false)}</td><td>{verification.custody_retrieval_id ?? "—"}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody return" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody return", rawJson: { evidenceBundleRetentionCustodyReturns, latestEvidenceBundleRetentionCustodyReturn } })}>
          {evidenceBundleRetentionCustodyReturns.length === 0 && !latestEvidenceBundleRetentionCustodyReturn ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody return artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker return-evidence-bundle-retention-custody-retrieval</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyReturn ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyReturn.return_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyReturn.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asNumber(latestEvidenceBundleRetentionCustodyReturn.blocker_count) ? "warn" : "neutral"}>return evidence</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyReturn.tracking_id) ?? "—" }, { k: "return_id", v: asString(latestEvidenceBundleRetentionCustodyReturn.custody_return_id) ?? "—" }, { k: "retrieval_id", v: asString(latestEvidenceBundleRetentionCustodyReturn.custody_retrieval_id) ?? "—" }, { k: "returned_by", v: asString(latestEvidenceBundleRetentionCustodyReturn.returned_by) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyReturn.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Return</th><th>Returned by</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyReturns.slice(0, 20).map((row, index) => (<tr key={`${row.artifact_path ?? "retention-custody-return"}-${index}`}><td>{row.tracking_id ?? "—"}</td><td><StatusBadge raw={row.return_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={row.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{row.custody_return_id ?? "—"}</td><td>{row.returned_by ?? "—"}</td><td>{row.blocker_count ?? 0}</td><td>{row.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody return verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody return verification", rawJson: { evidenceBundleRetentionCustodyReturnVerifications, latestEvidenceBundleRetentionCustodyReturnVerification } })}>
          {evidenceBundleRetentionCustodyReturnVerifications.length === 0 && !latestEvidenceBundleRetentionCustodyReturnVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody return verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-return</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyReturnVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyReturnVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyReturnVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyReturnVerification.retention_custody_return_artifact_hash_valid) ? "ok" : "warn"}>return hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyReturnVerification.custody_return_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyReturnVerification.tracking_id) ?? "—" }, { k: "return_id", v: asString(latestEvidenceBundleRetentionCustodyReturnVerification.custody_return_id) ?? "—" }, { k: "source_status", v: asString(latestEvidenceBundleRetentionCustodyReturnVerification.source_retention_custody_return_status) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyReturnVerification.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Return hash</th><th>Statement hash</th><th>Return</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyReturnVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-return-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_return_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_return_statement_hash_valid ?? false)}</td><td>{verification.custody_return_id ?? "—"}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody redeposit" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody redeposit", rawJson: { evidenceBundleRetentionCustodyRedeposits, latestEvidenceBundleRetentionCustodyRedeposit } })}>
          {evidenceBundleRetentionCustodyRedeposits.length === 0 && !latestEvidenceBundleRetentionCustodyRedeposit ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody redeposit artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker redeposit-evidence-bundle-retention-custody-return</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyRedeposit ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyRedeposit.redeposit_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyRedeposit.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asNumber(latestEvidenceBundleRetentionCustodyRedeposit.blocker_count) ? "warn" : "neutral"}>redeposit evidence</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyRedeposit.tracking_id) ?? "—" }, { k: "redeposit_id", v: asString(latestEvidenceBundleRetentionCustodyRedeposit.custody_redeposit_id) ?? "—" }, { k: "return_id", v: asString(latestEvidenceBundleRetentionCustodyRedeposit.custody_return_id) ?? "—" }, { k: "redeposited_by", v: asString(latestEvidenceBundleRetentionCustodyRedeposit.redeposited_by) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyRedeposit.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Redeposit</th><th>Return</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyRedeposits.slice(0, 20).map((row, index) => (<tr key={`${row.artifact_path ?? "retention-custody-redeposit"}-${index}`}><td>{row.tracking_id ?? "—"}</td><td><StatusBadge raw={row.redeposit_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={row.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{row.custody_redeposit_id ?? "—"}</td><td>{row.custody_return_id ?? "—"}</td><td>{row.blocker_count ?? 0}</td><td>{row.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody redeposit verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody redeposit verification", rawJson: { evidenceBundleRetentionCustodyRedepositVerifications, latestEvidenceBundleRetentionCustodyRedepositVerification } })}>
          {evidenceBundleRetentionCustodyRedepositVerifications.length === 0 && !latestEvidenceBundleRetentionCustodyRedepositVerification ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody redeposit verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-redeposit</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyRedepositVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyRedepositVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyRedepositVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyRedepositVerification.retention_custody_redeposit_artifact_hash_valid) ? "ok" : "warn"}>redeposit hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyRedepositVerification.custody_redeposit_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyRedepositVerification.tracking_id) ?? "—" }, { k: "redeposit_id", v: asString(latestEvidenceBundleRetentionCustodyRedepositVerification.custody_redeposit_id) ?? "—" }, { k: "source_status", v: asString(latestEvidenceBundleRetentionCustodyRedepositVerification.source_retention_custody_redeposit_status) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyRedepositVerification.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Redeposit hash</th><th>Statement hash</th><th>Redeposit</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyRedepositVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-redeposit-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_redeposit_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_redeposit_statement_hash_valid ?? false)}</td><td>{verification.custody_redeposit_id ?? "—"}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody inventory" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody inventory", rawJson: { evidenceBundleRetentionCustodyInventories, latestEvidenceBundleRetentionCustodyInventory } })}>
          {evidenceBundleRetentionCustodyInventories.length === 0 ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody inventory artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker inventory-evidence-bundle-retention-custody-redeposit</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyInventory ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyInventory.inventory_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyInventory.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asNumber(latestEvidenceBundleRetentionCustodyInventory.blocker_count) ? "warn" : "neutral"}>inventory evidence</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyInventory.tracking_id) ?? "—" }, { k: "inventory_id", v: asString(latestEvidenceBundleRetentionCustodyInventory.custody_inventory_id) ?? "—" }, { k: "redeposit_id", v: asString(latestEvidenceBundleRetentionCustodyInventory.custody_redeposit_id) ?? "—" }, { k: "inventoried_by", v: asString(latestEvidenceBundleRetentionCustodyInventory.inventoried_by) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyInventory.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Inventory</th><th>Redeposit</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyInventories.slice(0, 20).map((row, index) => (<tr key={`${row.artifact_path ?? "retention-custody-inventory"}-${index}`}><td>{row.tracking_id ?? "—"}</td><td><StatusBadge raw={row.inventory_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={row.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{row.custody_inventory_id ?? "—"}</td><td>{row.custody_redeposit_id ?? "—"}</td><td>{row.blocker_count ?? 0}</td><td>{row.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody inventory verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody inventory verification", rawJson: { evidenceBundleRetentionCustodyInventoryVerifications, latestEvidenceBundleRetentionCustodyInventoryVerification } })}>
          {evidenceBundleRetentionCustodyInventoryVerifications.length === 0 ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody inventory verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-inventory</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyInventoryVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyInventoryVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyInventoryVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyInventoryVerification.retention_custody_inventory_artifact_hash_valid) ? "ok" : "warn"}>inventory hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyInventoryVerification.custody_inventory_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyInventoryVerification.tracking_id) ?? "—" }, { k: "inventory_id", v: asString(latestEvidenceBundleRetentionCustodyInventoryVerification.custody_inventory_id) ?? "—" }, { k: "source_status", v: asString(latestEvidenceBundleRetentionCustodyInventoryVerification.source_retention_custody_inventory_status) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyInventoryVerification.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Inventory hash</th><th>Statement hash</th><th>Inventory</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyInventoryVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-inventory-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_inventory_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_inventory_statement_hash_valid ?? false)}</td><td>{verification.custody_inventory_id ?? "—"}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>


        <Pane title="Evidence-chain retention custody reconciliation" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody reconciliation", rawJson: { evidenceBundleRetentionCustodyReconciliations, latestEvidenceBundleRetentionCustodyReconciliation } })}>
          {evidenceBundleRetentionCustodyReconciliations.length === 0 ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody reconciliation artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker reconcile-evidence-bundle-retention-custody-inventory</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyReconciliation ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyReconciliation.reconciliation_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyReconciliation.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asNumber(latestEvidenceBundleRetentionCustodyReconciliation.blocker_count) ? "warn" : "neutral"}>reconciliation evidence</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyReconciliation.tracking_id) ?? "—" }, { k: "reconciliation_id", v: asString(latestEvidenceBundleRetentionCustodyReconciliation.custody_reconciliation_id) ?? "—" }, { k: "inventory_id", v: asString(latestEvidenceBundleRetentionCustodyReconciliation.custody_inventory_id) ?? "—" }, { k: "reconciled_by", v: asString(latestEvidenceBundleRetentionCustodyReconciliation.reconciled_by) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyReconciliation.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Reconciliation</th><th>Inventory</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyReconciliations.slice(0, 20).map((row, index) => (<tr key={`${row.artifact_path ?? "retention-custody-reconciliation"}-${index}`}><td>{row.tracking_id ?? "—"}</td><td><StatusBadge raw={row.reconciliation_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={row.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{row.custody_reconciliation_id ?? "—"}</td><td>{row.custody_inventory_id ?? "—"}</td><td>{row.blocker_count ?? 0}</td><td>{row.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody reconciliation verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody reconciliation verification", rawJson: { evidenceBundleRetentionCustodyReconciliationVerifications, latestEvidenceBundleRetentionCustodyReconciliationVerification } })}>
          {evidenceBundleRetentionCustodyReconciliationVerifications.length === 0 ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody reconciliation verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-reconciliation</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyReconciliationVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyReconciliationVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyReconciliationVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyReconciliationVerification.retention_custody_reconciliation_artifact_hash_valid) ? "ok" : "warn"}>reconciliation hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyReconciliationVerification.custody_reconciliation_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyReconciliationVerification.tracking_id) ?? "—" }, { k: "reconciliation_id", v: asString(latestEvidenceBundleRetentionCustodyReconciliationVerification.custody_reconciliation_id) ?? "—" }, { k: "source_status", v: asString(latestEvidenceBundleRetentionCustodyReconciliationVerification.source_retention_custody_reconciliation_status) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyReconciliationVerification.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Reconciliation hash</th><th>Statement hash</th><th>Reconciliation</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyReconciliationVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-reconciliation-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_reconciliation_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_reconciliation_statement_hash_valid ?? false)}</td><td>{verification.custody_reconciliation_id ?? "—"}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody certification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody certification", rawJson: { evidenceBundleRetentionCustodyCertifications, latestEvidenceBundleRetentionCustodyCertification } })}>
          {evidenceBundleRetentionCustodyCertifications.length === 0 ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody certification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker certify-evidence-bundle-retention-custody-reconciliation</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyCertification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyCertification.certification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyCertification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asNumber(latestEvidenceBundleRetentionCustodyCertification.blocker_count) ? "warn" : "neutral"}>certification evidence</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyCertification.tracking_id) ?? "—" }, { k: "certification_id", v: asString(latestEvidenceBundleRetentionCustodyCertification.custody_certification_id) ?? "—" }, { k: "reconciliation_id", v: asString(latestEvidenceBundleRetentionCustodyCertification.custody_reconciliation_id) ?? "—" }, { k: "certified_by", v: asString(latestEvidenceBundleRetentionCustodyCertification.certified_by) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyCertification.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Certification</th><th>Reconciliation</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyCertifications.slice(0, 20).map((row, index) => (<tr key={`${row.artifact_path ?? "retention-custody-certification"}-${index}`}><td>{row.tracking_id ?? "—"}</td><td><StatusBadge raw={row.certification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={row.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{row.custody_certification_id ?? "—"}</td><td>{row.custody_reconciliation_id ?? "—"}</td><td>{row.blocker_count ?? 0}</td><td>{row.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody certification verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody certification verification", rawJson: { evidenceBundleRetentionCustodyCertificationVerifications, latestEvidenceBundleRetentionCustodyCertificationVerification } })}>
          {evidenceBundleRetentionCustodyCertificationVerifications.length === 0 ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody certification verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-certification</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyCertificationVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyCertificationVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyCertificationVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyCertificationVerification.retention_custody_certification_artifact_hash_valid) ? "ok" : "warn"}>certification hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyCertificationVerification.custody_certification_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyCertificationVerification.tracking_id) ?? "—" }, { k: "certification_id", v: asString(latestEvidenceBundleRetentionCustodyCertificationVerification.custody_certification_id) ?? "—" }, { k: "source_status", v: asString(latestEvidenceBundleRetentionCustodyCertificationVerification.source_retention_custody_certification_status) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyCertificationVerification.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Certification hash</th><th>Statement hash</th><th>Certification</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyCertificationVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-certification-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_certification_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_certification_statement_hash_valid ?? false)}</td><td>{verification.custody_certification_id ?? "—"}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody attestation" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody attestation", rawJson: { evidenceBundleRetentionCustodyAttestations, latestEvidenceBundleRetentionCustodyAttestation } })}>
          {evidenceBundleRetentionCustodyAttestations.length === 0 ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody attestation artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker attest-evidence-bundle-retention-custody-certification</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyAttestation ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyAttestation.attestation_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyAttestation.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asNumber(latestEvidenceBundleRetentionCustodyAttestation.blocker_count) ? "warn" : "neutral"}>attestation evidence</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyAttestation.tracking_id) ?? "—" }, { k: "attestation_id", v: asString(latestEvidenceBundleRetentionCustodyAttestation.custody_attestation_id) ?? "—" }, { k: "certification_id", v: asString(latestEvidenceBundleRetentionCustodyAttestation.custody_certification_id) ?? "—" }, { k: "attested_by", v: asString(latestEvidenceBundleRetentionCustodyAttestation.attested_by) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyAttestation.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Attestation</th><th>Certification</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyAttestations.slice(0, 20).map((row, index) => (<tr key={`${row.artifact_path ?? "retention-custody-attestation"}-${index}`}><td>{row.tracking_id ?? "—"}</td><td><StatusBadge raw={row.attestation_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={row.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{row.custody_attestation_id ?? "—"}</td><td>{row.custody_certification_id ?? "—"}</td><td>{row.blocker_count ?? 0}</td><td>{row.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Evidence-chain retention custody attestation verification" dense onInspect={() => openInspector({ title: "Paper execution evidence-chain retention custody attestation verification", rawJson: { evidenceBundleRetentionCustodyAttestationVerifications, latestEvidenceBundleRetentionCustodyAttestationVerification } })}>
          {evidenceBundleRetentionCustodyAttestationVerifications.length === 0 ? (
            <div style={{ display: "grid", gap: "0.5rem", fontSize: "11px" }}><p className="muted" style={{ margin: 0 }}>No retention custody attestation verification artifact yet.</p><pre className="json-preview" style={{ margin: 0, fontSize: "10px" }}>strategy-validator-paper-broker verify-evidence-bundle-retention-custody-attestation</pre></div>
          ) : (
            <div style={{ display: "grid", gap: "0.75rem" }}>
              {latestEvidenceBundleRetentionCustodyAttestationVerification ? (<div className="panel" style={{ padding: "0.65rem", fontSize: "11px" }}><div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", alignItems: "center", marginBottom: "0.5rem" }}><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyAttestationVerification.verification_status) ?? "UNKNOWN"} /><StatusBadge raw={asString(latestEvidenceBundleRetentionCustodyAttestationVerification.trust_banner) ?? "TRUST_RESTRICTED"} /><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyAttestationVerification.retention_custody_attestation_artifact_hash_valid) ? "ok" : "warn"}>attestation hash</SeverityBadge><SeverityBadge severity={asBool(latestEvidenceBundleRetentionCustodyAttestationVerification.custody_attestation_statement_hash_valid) ? "ok" : "warn"}>statement hash</SeverityBadge></div><TermKV rows={[{ k: "tracking_id", v: asString(latestEvidenceBundleRetentionCustodyAttestationVerification.tracking_id) ?? "—" }, { k: "attestation_id", v: asString(latestEvidenceBundleRetentionCustodyAttestationVerification.custody_attestation_id) ?? "—" }, { k: "source_status", v: asString(latestEvidenceBundleRetentionCustodyAttestationVerification.source_retention_custody_attestation_status) ?? "—" }, { k: "blockers", v: asStringArray(latestEvidenceBundleRetentionCustodyAttestationVerification.blockers).join("; ") || "—" }]} /></div>) : null}
              <div style={{ overflowX: "auto" }}><table className="dense-table"><thead><tr><th>Tracking</th><th>Status</th><th>Trust</th><th>Attestation hash</th><th>Statement hash</th><th>Attestation</th><th>Blockers</th><th>Artifact</th></tr></thead><tbody>{evidenceBundleRetentionCustodyAttestationVerifications.slice(0, 20).map((verification, index) => (<tr key={`${verification.artifact_path ?? "retention-custody-attestation-verification"}-${index}`}><td>{verification.tracking_id ?? "—"}</td><td><StatusBadge raw={verification.verification_status ?? "UNKNOWN"} /></td><td><StatusBadge raw={verification.trust_banner ?? "TRUST_RESTRICTED"} /></td><td>{String(verification.retention_custody_attestation_artifact_hash_valid ?? false)}</td><td>{String(verification.custody_attestation_statement_hash_valid ?? false)}</td><td>{verification.custody_attestation_id ?? "—"}</td><td>{verification.blocker_count ?? 0}</td><td>{verification.artifact_path ?? "—"}</td></tr>))}</tbody></table></div>
            </div>
          )}
        </Pane>

        <Pane title="Paper order journal" dense onInspect={() => openInspector({ title: "Paper order journal", rawJson: { journal } })}>
          {journal.length === 0 ? (
            <p className="muted">No paper broker submission artifacts found under artifacts/paper_broker.</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table className="dense-table">
                <thead>
                  <tr>
                    <th>Tracking</th>
                    <th>Kind</th>
                    <th>Status</th>
                    <th>OK</th>
                    <th>Dry run</th>
                    <th>Broker order</th>
                    <th>Digest</th>
                    <th>Selection SHA</th>
                    <th>Guard</th>
                    <th>Freshness</th>
                    <th>Replay match</th>
                    <th>Dry-run match</th>
                    <th>Artifact</th>
                  </tr>
                </thead>
                <tbody>
                  {journal.slice(0, 20).map((entry, index) => (
                    <tr key={`${entry.artifact_path}-${index}`}>
                      <td>{entry.tracking_id}</td>
                      <td>{entry.artifact_kind ?? "SUBMISSION"}</td>
                      <td>{entry.status ?? "—"}</td>
                      <td>{String(entry.ok ?? "—")}</td>
                      <td>{String(entry.dry_run ?? "—")}</td>
                      <td>{entry.broker_order_id ?? "—"}</td>
                      <td>{entry.digest_prefix ?? "—"}</td>
                      <td>{(entry.source_selection_artifact_sha256 ?? "—").slice(0, 16)}</td>
                      <td>{entry.submission_guard_status ?? "—"}</td>
                      <td>{entry.evidence_freshness_status ?? "—"}</td>
                      <td>{String(entry.selected_intent_match ?? "—")}</td>
                      <td>{String(entry.linked_dry_run_match ?? "—")}</td>
                      <td>{entry.artifact_path}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Pane>

        <Pane title="Recommended operator actions" dense>
          <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: "11px" }}>
            {(root?.recommended_actions ?? []).map((action) => (
              <li key={action}>{action}</li>
            ))}
          </ul>
          {root?.degraded?.length ? (
            <p className="muted" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
              Degraded: {root.degraded.join(", ")}
            </p>
          ) : null}
        </Pane>
      </div>
    </main>
  );
}
