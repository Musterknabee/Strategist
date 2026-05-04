"""Daily operator run contracts."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class DailyOperatorRunComponent(BaseModel):
    schema_version: Literal["daily_operator_run_component/v1"] = "daily_operator_run_component/v1"
    component_id: str
    title: str
    source_route: str
    status: Literal["OK", "WARNING", "BLOCKED", "NOT_PRESENT"] = "WARNING"
    posture: str = "UNKNOWN"
    summary: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class DailyOperatorRunSummary(BaseModel):
    schema_version: Literal["daily_operator_run_summary/v1"] = "daily_operator_run_summary/v1"
    component_count: int = 0
    ok_count: int = 0
    warning_count: int = 0
    blocked_count: int = 0
    not_present_count: int = 0
    provider_action_required_count: int = 0
    strategy_intake_count: int = 0
    backtest_strategy_count: int = 0
    graveyard_entry_count: int = 0
    evidence_chain_issue_count: int = 0
    operator_run_step_count: int = 0
    paper_execution_intent_count: int = 0
    paper_execution_dry_run_blocked_count: int = 0
    paper_execution_journal_entry_count: int = 0
    paper_execution_dry_run_artifact_count: int = 0
    paper_execution_selected_intent_count: int = 0
    paper_execution_selected_replay_matched_count: int = 0
    paper_execution_freshness_blocker_count: int = 0
    paper_execution_submission_receipt_count: int = 0
    paper_execution_submission_guard_blocker_count: int = 0
    paper_execution_latest_submission_guard_passed_count: int = 0
    paper_execution_order_status_artifact_count: int = 0
    paper_execution_order_status_blocker_count: int = 0
    paper_execution_latest_order_filled_count: int = 0
    paper_execution_position_snapshot_count: int = 0
    paper_execution_position_reconciliation_blocker_count: int = 0
    paper_execution_position_reconciled_count: int = 0
    paper_execution_timeline_event_count: int = 0
    paper_execution_timeline_blocker_count: int = 0
    paper_execution_timeline_trusted_event_count: int = 0
    paper_execution_timeline_complete_count: int = 0
    paper_execution_evidence_bundle_count: int = 0
    paper_execution_evidence_bundle_blocker_count: int = 0
    paper_execution_latest_bundle_trusted_count: int = 0
    paper_execution_evidence_bundle_verification_count: int = 0
    paper_execution_evidence_bundle_verification_blocker_count: int = 0
    paper_execution_latest_bundle_verified_count: int = 0
    paper_execution_evidence_bundle_drift_count: int = 0
    paper_execution_evidence_bundle_drift_blocker_count: int = 0
    paper_execution_latest_bundle_drifted_count: int = 0
    paper_execution_evidence_bundle_rotation_count: int = 0
    paper_execution_evidence_bundle_rotation_blocker_count: int = 0
    paper_execution_latest_bundle_rotation_required_count: int = 0
    paper_execution_evidence_bundle_rotation_execution_count: int = 0
    paper_execution_evidence_bundle_rotation_execution_blocker_count: int = 0
    paper_execution_latest_bundle_rotation_execution_passed_count: int = 0
    paper_execution_evidence_bundle_attestation_count: int = 0
    paper_execution_evidence_bundle_attestation_blocker_count: int = 0
    paper_execution_evidence_bundle_attestation_verification_count: int = 0
    paper_execution_evidence_bundle_attestation_verification_blocker_count: int = 0
    paper_execution_latest_bundle_attestation_verified_count: int = 0
    paper_execution_latest_bundle_attested_count: int = 0
    paper_execution_evidence_bundle_closure_count: int = 0
    paper_execution_evidence_bundle_closure_blocker_count: int = 0
    paper_execution_latest_bundle_closure_ready_count: int = 0
    paper_execution_evidence_bundle_closure_verification_count: int = 0
    paper_execution_evidence_bundle_closure_verification_blocker_count: int = 0
    paper_execution_latest_bundle_closure_verified_count: int = 0
    paper_execution_evidence_bundle_export_manifest_count: int = 0
    paper_execution_evidence_bundle_export_manifest_blocker_count: int = 0
    paper_execution_latest_bundle_export_ready_count: int = 0
    paper_execution_evidence_bundle_export_verification_count: int = 0
    paper_execution_evidence_bundle_export_verification_blocker_count: int = 0
    paper_execution_latest_bundle_export_verified_count: int = 0
    paper_execution_evidence_bundle_retention_receipt_count: int = 0
    paper_execution_evidence_bundle_retention_receipt_blocker_count: int = 0
    paper_execution_latest_bundle_retention_ready_count: int = 0
    paper_execution_evidence_bundle_retention_verification_count: int = 0
    paper_execution_evidence_bundle_retention_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_verified_count: int = 0
    paper_execution_evidence_bundle_retention_signoff_count: int = 0
    paper_execution_evidence_bundle_retention_signoff_blocker_count: int = 0
    paper_execution_latest_bundle_retention_signed_off_count: int = 0
    paper_execution_evidence_bundle_retention_signoff_verification_count: int = 0
    paper_execution_evidence_bundle_retention_signoff_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_signoff_verified_count: int = 0
    paper_execution_evidence_bundle_retention_handoff_count: int = 0
    paper_execution_evidence_bundle_retention_handoff_blocker_count: int = 0
    paper_execution_latest_bundle_retention_handoff_ready_count: int = 0
    paper_execution_evidence_bundle_retention_handoff_verification_count: int = 0
    paper_execution_evidence_bundle_retention_handoff_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_handoff_verified_count: int = 0
    paper_execution_evidence_bundle_retention_handoff_acceptance_count: int = 0
    paper_execution_evidence_bundle_retention_handoff_acceptance_blocker_count: int = 0
    paper_execution_latest_bundle_retention_handoff_accepted_count: int = 0
    paper_execution_evidence_bundle_retention_handoff_acceptance_verification_count: int = 0
    paper_execution_evidence_bundle_retention_handoff_acceptance_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_handoff_acceptance_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_register_count: int = 0
    paper_execution_evidence_bundle_retention_custody_register_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_registered_count: int = 0
    paper_execution_evidence_bundle_retention_custody_register_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_register_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_register_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_seal_count: int = 0
    paper_execution_evidence_bundle_retention_custody_seal_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_sealed_count: int = 0
    paper_execution_evidence_bundle_retention_custody_seal_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_seal_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_seal_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_audit_count: int = 0
    paper_execution_evidence_bundle_retention_custody_audit_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_audited_count: int = 0
    paper_execution_evidence_bundle_retention_custody_audit_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_audit_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_audit_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_continuity_count: int = 0
    paper_execution_evidence_bundle_retention_custody_continuity_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_continuity_attested_count: int = 0
    paper_execution_evidence_bundle_retention_custody_continuity_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_continuity_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_continuity_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_review_count: int = 0
    paper_execution_evidence_bundle_retention_custody_review_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_reviewed_count: int = 0
    paper_execution_evidence_bundle_retention_custody_review_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_review_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_review_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_renewal_count: int = 0
    paper_execution_evidence_bundle_retention_custody_renewal_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_renewed_count: int = 0
    paper_execution_evidence_bundle_retention_custody_renewal_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_renewal_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_renewal_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_schedule_count: int = 0
    paper_execution_evidence_bundle_retention_custody_schedule_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_scheduled_count: int = 0
    paper_execution_evidence_bundle_retention_custody_schedule_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_schedule_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_schedule_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_notice_count: int = 0
    paper_execution_evidence_bundle_retention_custody_notice_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_notice_ready_count: int = 0
    paper_execution_evidence_bundle_retention_custody_notice_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_notice_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_notice_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_acknowledgment_count: int = 0
    paper_execution_evidence_bundle_retention_custody_acknowledgment_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_acknowledged_count: int = 0
    paper_execution_evidence_bundle_retention_custody_acknowledgment_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_acknowledgment_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_acknowledgment_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_completion_count: int = 0
    paper_execution_evidence_bundle_retention_custody_completion_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_completed_count: int = 0
    paper_execution_evidence_bundle_retention_custody_completion_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_completion_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_completion_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_closeout_count: int = 0
    paper_execution_evidence_bundle_retention_custody_closeout_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_closed_out_count: int = 0
    paper_execution_evidence_bundle_retention_custody_closeout_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_closeout_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_closeout_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_archive_count: int = 0
    paper_execution_evidence_bundle_retention_custody_archive_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_archived_count: int = 0
    paper_execution_evidence_bundle_retention_custody_archive_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_archive_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_archive_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_retrieval_count: int = 0
    paper_execution_evidence_bundle_retention_custody_retrieval_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_retrieved_count: int = 0
    paper_execution_evidence_bundle_retention_custody_retrieval_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_retrieval_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_retrieval_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_return_count: int = 0
    paper_execution_evidence_bundle_retention_custody_return_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_returned_count: int = 0
    paper_execution_evidence_bundle_retention_custody_return_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_return_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_return_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_redeposit_count: int = 0
    paper_execution_evidence_bundle_retention_custody_redeposit_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_redeposited_count: int = 0
    paper_execution_evidence_bundle_retention_custody_redeposit_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_redeposit_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_redeposit_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_inventory_count: int = 0
    paper_execution_evidence_bundle_retention_custody_inventory_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_inventoried_count: int = 0
    paper_execution_evidence_bundle_retention_custody_inventory_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_inventory_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_inventory_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_reconciliation_count: int = 0
    paper_execution_evidence_bundle_retention_custody_reconciliation_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_reconciled_count: int = 0
    paper_execution_evidence_bundle_retention_custody_reconciliation_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_reconciliation_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_reconciliation_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_certification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_certification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_certified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_certification_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_certification_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_certification_verified_count: int = 0
    paper_execution_evidence_bundle_retention_custody_attestation_count: int = 0
    paper_execution_evidence_bundle_retention_custody_attestation_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_attested_count: int = 0
    paper_execution_evidence_bundle_retention_custody_attestation_verification_count: int = 0
    paper_execution_evidence_bundle_retention_custody_attestation_verification_blocker_count: int = 0
    paper_execution_latest_bundle_retention_custody_attestation_verified_count: int = 0
    model_config = {"extra": "forbid"}


class DailyOperatorRunPayload(BaseModel):
    schema_version: Literal["ui_daily_operator_run/v1"] = "ui_daily_operator_run/v1"
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_broker_orders: bool = True
    no_order_controls: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    status: Literal["COMPLETE", "RESTRICTED", "BLOCKED", "EMPTY"] = "RESTRICTED"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    summary: DailyOperatorRunSummary = Field(default_factory=DailyOperatorRunSummary)
    components: list[DailyOperatorRunComponent] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    source_routes: list[str] = Field(default_factory=list)
    disclaimer: str = "Daily operator run is a read-plane briefing. It does not authorize live trading, broker orders, deployment approval, or strategy promotion."
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


__all__ = ["DailyOperatorRunComponent", "DailyOperatorRunPayload", "DailyOperatorRunSummary"]
