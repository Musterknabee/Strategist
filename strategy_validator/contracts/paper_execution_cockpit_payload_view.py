"""Paper execution cockpit aggregate payload contract."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *
from strategy_validator.contracts.paper_execution_evidence_bundle import *
from strategy_validator.contracts.paper_execution_retention import *
from strategy_validator.contracts.paper_execution_retention_custody_chain import *
from strategy_validator.contracts.paper_execution_retention_custody_renewal import *
from strategy_validator.contracts.paper_execution_retention_custody_archive import *
from strategy_validator.contracts.paper_execution_cockpit_summary import PaperExecutionSummary


class PaperExecutionCockpitPayload(BaseModel):
    schema_version: Literal["ui_paper_execution_cockpit/v1"] = "ui_paper_execution_cockpit/v1"
    generated_at_utc: datetime
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_browser_orders: bool = True
    no_network_calls: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    paper_submission_authority: Literal["CLI_ONLY"] = "CLI_ONLY"
    scan_root: str
    broker_artifact_path: str | None = None
    degraded: list[str] = Field(default_factory=list)
    summary: PaperExecutionSummary
    broker_status: dict[str, Any] = Field(default_factory=dict)
    latest_tracking: dict[str, Any] | None = None
    candidate_intents: list[PaperExecutionIntentPreview] = Field(default_factory=list)
    selected_intent: PaperExecutionIntentSelectionArtifact | None = None
    dry_run_command_hint: str | None = None
    dry_run_results: list[dict[str, Any]] = Field(default_factory=list)
    freshness_gate: PaperExecutionFreshnessGate = Field(default_factory=PaperExecutionFreshnessGate)
    journal_entries: list[PaperExecutionJournalEntry] = Field(default_factory=list)
    submission_receipts: list[PaperExecutionSubmissionReceiptView] = Field(default_factory=list)
    order_statuses: list[PaperExecutionOrderStatusView] = Field(default_factory=list)
    account_position_snapshot: PaperExecutionAccountPositionSnapshotArtifact | None = None
    position_reconciliation: PaperExecutionPositionReconciliationView = Field(default_factory=PaperExecutionPositionReconciliationView)
    execution_timeline: list[PaperExecutionTimelineEntry] = Field(default_factory=list)
    execution_timeline_summary: PaperExecutionTimelineSummary = Field(default_factory=PaperExecutionTimelineSummary)
    evidence_bundles: list[PaperExecutionEvidenceBundleView] = Field(default_factory=list)
    latest_evidence_bundle: PaperExecutionEvidenceBundleView | None = None
    evidence_bundle_verifications: list[PaperExecutionEvidenceBundleVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_verification: PaperExecutionEvidenceBundleVerificationView | None = None
    evidence_bundle_drifts: list[PaperExecutionEvidenceBundleDriftView] = Field(default_factory=list)
    latest_evidence_bundle_drift: PaperExecutionEvidenceBundleDriftView | None = None
    evidence_bundle_rotations: list[PaperExecutionEvidenceBundleRotationView] = Field(default_factory=list)
    latest_evidence_bundle_rotation: PaperExecutionEvidenceBundleRotationView | None = None
    evidence_bundle_rotation_executions: list[PaperExecutionEvidenceBundleRotationExecutionView] = Field(default_factory=list)
    latest_evidence_bundle_rotation_execution: PaperExecutionEvidenceBundleRotationExecutionView | None = None
    evidence_bundle_attestations: list[PaperExecutionEvidenceBundleAttestationView] = Field(default_factory=list)
    latest_evidence_bundle_attestation: PaperExecutionEvidenceBundleAttestationView | None = None
    evidence_bundle_attestation_verifications: list[PaperExecutionEvidenceBundleAttestationVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_attestation_verification: PaperExecutionEvidenceBundleAttestationVerificationView | None = None
    evidence_bundle_closures: list[PaperExecutionEvidenceBundleClosureView] = Field(default_factory=list)
    latest_evidence_bundle_closure: PaperExecutionEvidenceBundleClosureView | None = None
    evidence_bundle_closure_verifications: list[PaperExecutionEvidenceBundleClosureVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_closure_verification: PaperExecutionEvidenceBundleClosureVerificationView | None = None
    evidence_bundle_export_manifests: list[PaperExecutionEvidenceBundleExportManifestView] = Field(default_factory=list)
    latest_evidence_bundle_export_manifest: PaperExecutionEvidenceBundleExportManifestView | None = None
    evidence_bundle_export_verifications: list[PaperExecutionEvidenceBundleExportVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_export_verification: PaperExecutionEvidenceBundleExportVerificationView | None = None
    evidence_bundle_retention_receipts: list[PaperExecutionEvidenceBundleRetentionReceiptView] = Field(default_factory=list)
    latest_evidence_bundle_retention_receipt: PaperExecutionEvidenceBundleRetentionReceiptView | None = None
    evidence_bundle_retention_verifications: list[PaperExecutionEvidenceBundleRetentionVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_verification: PaperExecutionEvidenceBundleRetentionVerificationView | None = None
    evidence_bundle_retention_signoffs: list[PaperExecutionEvidenceBundleRetentionSignoffView] = Field(default_factory=list)
    latest_evidence_bundle_retention_signoff: PaperExecutionEvidenceBundleRetentionSignoffView | None = None
    evidence_bundle_retention_signoff_verifications: list[PaperExecutionEvidenceBundleRetentionSignoffVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_signoff_verification: PaperExecutionEvidenceBundleRetentionSignoffVerificationView | None = None
    evidence_bundle_retention_handoffs: list[PaperExecutionEvidenceBundleRetentionHandoffView] = Field(default_factory=list)
    latest_evidence_bundle_retention_handoff: PaperExecutionEvidenceBundleRetentionHandoffView | None = None
    evidence_bundle_retention_handoff_verifications: list[PaperExecutionEvidenceBundleRetentionHandoffVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_handoff_verification: PaperExecutionEvidenceBundleRetentionHandoffVerificationView | None = None
    evidence_bundle_retention_handoff_acceptances: list[PaperExecutionEvidenceBundleRetentionHandoffAcceptanceView] = Field(default_factory=list)
    latest_evidence_bundle_retention_handoff_acceptance: PaperExecutionEvidenceBundleRetentionHandoffAcceptanceView | None = None
    evidence_bundle_retention_handoff_acceptance_verifications: list[PaperExecutionEvidenceBundleRetentionHandoffAcceptanceVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_handoff_acceptance_verification: PaperExecutionEvidenceBundleRetentionHandoffAcceptanceVerificationView | None = None
    evidence_bundle_retention_custody_registers: list[PaperExecutionEvidenceBundleRetentionCustodyRegisterView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_register: PaperExecutionEvidenceBundleRetentionCustodyRegisterView | None = None
    evidence_bundle_retention_custody_register_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_register_verification: PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationView | None = None
    evidence_bundle_retention_custody_seals: list[PaperExecutionEvidenceBundleRetentionCustodySealView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_seal: PaperExecutionEvidenceBundleRetentionCustodySealView | None = None
    evidence_bundle_retention_custody_seal_verifications: list[PaperExecutionEvidenceBundleRetentionCustodySealVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_seal_verification: PaperExecutionEvidenceBundleRetentionCustodySealVerificationView | None = None
    evidence_bundle_retention_custody_audits: list[PaperExecutionEvidenceBundleRetentionCustodyAuditView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_audit: PaperExecutionEvidenceBundleRetentionCustodyAuditView | None = None
    evidence_bundle_retention_custody_audit_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyAuditVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_audit_verification: PaperExecutionEvidenceBundleRetentionCustodyAuditVerificationView | None = None
    evidence_bundle_retention_custody_continuities: list[PaperExecutionEvidenceBundleRetentionCustodyContinuityView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_continuity: PaperExecutionEvidenceBundleRetentionCustodyContinuityView | None = None
    evidence_bundle_retention_custody_continuity_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_continuity_verification: PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationView | None = None
    evidence_bundle_retention_custody_reviews: list[PaperExecutionEvidenceBundleRetentionCustodyReviewView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_review: PaperExecutionEvidenceBundleRetentionCustodyReviewView | None = None
    evidence_bundle_retention_custody_review_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyReviewVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_review_verification: PaperExecutionEvidenceBundleRetentionCustodyReviewVerificationView | None = None
    evidence_bundle_retention_custody_renewals: list[PaperExecutionEvidenceBundleRetentionCustodyRenewalView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_renewal: PaperExecutionEvidenceBundleRetentionCustodyRenewalView | None = None
    evidence_bundle_retention_custody_renewal_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyRenewalVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_renewal_verification: PaperExecutionEvidenceBundleRetentionCustodyRenewalVerificationView | None = None
    evidence_bundle_retention_custody_schedules: list[PaperExecutionEvidenceBundleRetentionCustodyScheduleView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_schedule: PaperExecutionEvidenceBundleRetentionCustodyScheduleView | None = None
    evidence_bundle_retention_custody_schedule_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyScheduleVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_schedule_verification: PaperExecutionEvidenceBundleRetentionCustodyScheduleVerificationView | None = None
    evidence_bundle_retention_custody_notices: list[PaperExecutionEvidenceBundleRetentionCustodyNoticeView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_notice: PaperExecutionEvidenceBundleRetentionCustodyNoticeView | None = None
    evidence_bundle_retention_custody_notice_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyNoticeVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_notice_verification: PaperExecutionEvidenceBundleRetentionCustodyNoticeVerificationView | None = None
    evidence_bundle_retention_custody_acknowledgments: list[PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_acknowledgment: PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentView | None = None
    evidence_bundle_retention_custody_acknowledgment_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_acknowledgment_verification: PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentVerificationView | None = None
    evidence_bundle_retention_custody_completions: list[PaperExecutionEvidenceBundleRetentionCustodyCompletionView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_completion: PaperExecutionEvidenceBundleRetentionCustodyCompletionView | None = None
    evidence_bundle_retention_custody_completion_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyCompletionVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_completion_verification: PaperExecutionEvidenceBundleRetentionCustodyCompletionVerificationView | None = None
    evidence_bundle_retention_custody_closeouts: list[PaperExecutionEvidenceBundleRetentionCustodyCloseoutView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_closeout: PaperExecutionEvidenceBundleRetentionCustodyCloseoutView | None = None
    evidence_bundle_retention_custody_closeout_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyCloseoutVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_closeout_verification: PaperExecutionEvidenceBundleRetentionCustodyCloseoutVerificationView | None = None
    evidence_bundle_retention_custody_archives: list[PaperExecutionEvidenceBundleRetentionCustodyArchiveView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_archive: PaperExecutionEvidenceBundleRetentionCustodyArchiveView | None = None
    evidence_bundle_retention_custody_archive_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyArchiveVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_archive_verification: PaperExecutionEvidenceBundleRetentionCustodyArchiveVerificationView | None = None
    evidence_bundle_retention_custody_retrievals: list[PaperExecutionEvidenceBundleRetentionCustodyRetrievalView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_retrieval: PaperExecutionEvidenceBundleRetentionCustodyRetrievalView | None = None
    evidence_bundle_retention_custody_retrieval_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyRetrievalVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_retrieval_verification: PaperExecutionEvidenceBundleRetentionCustodyRetrievalVerificationView | None = None
    evidence_bundle_retention_custody_returns: list[PaperExecutionEvidenceBundleRetentionCustodyReturnView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_return: PaperExecutionEvidenceBundleRetentionCustodyReturnView | None = None
    evidence_bundle_retention_custody_return_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyReturnVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_return_verification: PaperExecutionEvidenceBundleRetentionCustodyReturnVerificationView | None = None
    evidence_bundle_retention_custody_redeposits: list[PaperExecutionEvidenceBundleRetentionCustodyRedepositView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_redeposit: PaperExecutionEvidenceBundleRetentionCustodyRedepositView | None = None
    evidence_bundle_retention_custody_redeposit_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyRedepositVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_redeposit_verification: PaperExecutionEvidenceBundleRetentionCustodyRedepositVerificationView | None = None
    evidence_bundle_retention_custody_inventories: list[PaperExecutionEvidenceBundleRetentionCustodyInventoryView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_inventory: PaperExecutionEvidenceBundleRetentionCustodyInventoryView | None = None
    evidence_bundle_retention_custody_inventory_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyInventoryVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_inventory_verification: PaperExecutionEvidenceBundleRetentionCustodyInventoryVerificationView | None = None
    evidence_bundle_retention_custody_reconciliations: list[PaperExecutionEvidenceBundleRetentionCustodyReconciliationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_reconciliation: PaperExecutionEvidenceBundleRetentionCustodyReconciliationView | None = None
    evidence_bundle_retention_custody_reconciliation_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyReconciliationVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_reconciliation_verification: PaperExecutionEvidenceBundleRetentionCustodyReconciliationVerificationView | None = None
    evidence_bundle_retention_custody_certifications: list[PaperExecutionEvidenceBundleRetentionCustodyCertificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_certification: PaperExecutionEvidenceBundleRetentionCustodyCertificationView | None = None
    evidence_bundle_retention_custody_certification_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyCertificationVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_certification_verification: PaperExecutionEvidenceBundleRetentionCustodyCertificationVerificationView | None = None
    evidence_bundle_retention_custody_attestations: list[PaperExecutionEvidenceBundleRetentionCustodyAttestationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_attestation: PaperExecutionEvidenceBundleRetentionCustodyAttestationView | None = None
    evidence_bundle_retention_custody_attestation_verifications: list[PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationView] = Field(default_factory=list)
    latest_evidence_bundle_retention_custody_attestation_verification: PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationView | None = None
    recommended_actions: list[str] = Field(default_factory=list)
    disclaimer: str = "Paper execution cockpit is a read-plane preview. Browser/API routes do not submit orders. Use the paper-broker CLI on a trusted host for authenticated paper-only submissions."

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v



__all__ = (
    "PaperExecutionCockpitPayload",
)
