"""Paper execution retention custody notice/acknowledgment contract models."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *
from strategy_validator.contracts.paper_execution_evidence_bundle import *
from strategy_validator.contracts.paper_execution_retention import *
from strategy_validator.contracts.paper_execution_retention_custody_chain import *


class PaperExecutionEvidenceBundleRetentionCustodyNoticeArtifact(BaseModel):
    """Read-only operator notice for scheduled paper evidence retention custody renewal."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_notice/v1"] = "paper_execution_evidence_bundle_retention_custody_notice/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    notice_authority: Literal["READ_ONLY_RETENTION_CUSTODY_NOTICE"] = "READ_ONLY_RETENTION_CUSTODY_NOTICE"
    notice_status: Literal["NOTICE_DUE", "NOTICE_PENDING", "NOTICE_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_notice_id: str | None = None
    notified_by: str | None = None
    custody_location: str | None = None
    notice_generated_for_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    reminder_window_starts_at_utc: str | None = None
    days_until_due: int = 0
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    notice_message: str | None = None
    notice_note: str | None = None
    source_retention_custody_schedule_verification_artifact_path: str | None = None
    source_retention_custody_schedule_verification_declared_sha256: str | None = None
    source_retention_custody_schedule_verification_computed_sha256: str | None = None
    source_retention_custody_schedule_verification_status: str | None = None
    source_retention_custody_schedule_verification_trust_banner: str | None = None
    retention_custody_schedule_verification_artifact_hash_valid: bool = False
    source_retention_custody_schedule_status: str | None = None
    retention_custody_schedule_artifact_hash_valid: bool = False
    custody_schedule_id: str | None = None
    custody_schedule_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_notice_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_notice_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyNoticeView(BaseModel):
    """Read-plane summary of paper evidence retention custody renewal notices."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_notice_view/v1"] = "paper_execution_evidence_bundle_retention_custody_notice_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    notice_status: Literal["NOTICE_DUE", "NOTICE_PENDING", "NOTICE_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_notice_id: str | None = None
    notified_by: str | None = None
    custody_location: str | None = None
    notice_generated_for_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    reminder_window_starts_at_utc: str | None = None
    days_until_due: int = 0
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    notice_message: str | None = None
    notice_note: str | None = None
    source_retention_custody_schedule_verification_artifact_path: str | None = None
    source_retention_custody_schedule_verification_status: str | None = None
    retention_custody_schedule_verification_artifact_hash_valid: bool = False
    source_retention_custody_schedule_status: str | None = None
    retention_custody_schedule_artifact_hash_valid: bool = False
    custody_schedule_id: str | None = None
    custody_schedule_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_notice_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyNoticeVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody renewal notices."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_notice_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_notice_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    notice_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_NOTICE_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_NOTICE_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_notice_artifact_path: str | None = None
    source_retention_custody_notice_declared_sha256: str | None = None
    source_retention_custody_notice_computed_sha256: str | None = None
    source_retention_custody_notice_status: str | None = None
    source_retention_custody_notice_trust_banner: str | None = None
    retention_custody_notice_artifact_hash_valid: bool = False
    custody_notice_id: str | None = None
    notified_by: str | None = None
    custody_location: str | None = None
    notice_generated_for_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    reminder_window_starts_at_utc: str | None = None
    days_until_due: int = 0
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    notice_message: str | None = None
    notice_note: str | None = None
    custody_notice_statement_declared_sha256: str | None = None
    custody_notice_statement_computed_sha256: str | None = None
    custody_notice_statement_hash_valid: bool = False
    source_retention_custody_schedule_verification_artifact_path: str | None = None
    source_retention_custody_schedule_verification_status: str | None = None
    retention_custody_schedule_verification_artifact_hash_valid: bool = False
    source_retention_custody_schedule_status: str | None = None
    retention_custody_schedule_artifact_hash_valid: bool = False
    custody_schedule_id: str | None = None
    custody_schedule_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_notice_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyNoticeVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody renewal notice verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_notice_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_notice_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_notice_artifact_path: str | None = None
    source_retention_custody_notice_status: str | None = None
    retention_custody_notice_artifact_hash_valid: bool = False
    custody_notice_id: str | None = None
    notified_by: str | None = None
    custody_location: str | None = None
    notice_generated_for_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    reminder_window_starts_at_utc: str | None = None
    days_until_due: int = 0
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    notice_message: str | None = None
    custody_notice_statement_hash_valid: bool = False
    source_retention_custody_schedule_verification_artifact_path: str | None = None
    source_retention_custody_schedule_verification_status: str | None = None
    retention_custody_schedule_verification_artifact_hash_valid: bool = False
    source_retention_custody_schedule_status: str | None = None
    retention_custody_schedule_artifact_hash_valid: bool = False
    custody_schedule_id: str | None = None
    custody_schedule_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentArtifact(BaseModel):
    """Read-only operator acknowledgment of a verified paper evidence retention custody renewal notice."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_acknowledgment/v1"] = "paper_execution_evidence_bundle_retention_custody_acknowledgment/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    acknowledgment_authority: Literal["READ_ONLY_RETENTION_CUSTODY_ACKNOWLEDGMENT"] = "READ_ONLY_RETENTION_CUSTODY_ACKNOWLEDGMENT"
    acknowledgment_status: Literal["ACKNOWLEDGED", "ACKNOWLEDGED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_acknowledgment_id: str | None = None
    acknowledged_by: str | None = None
    custody_location: str | None = None
    acknowledged_at_utc: str | None = None
    acknowledgment_note: str | None = None
    source_retention_custody_notice_verification_artifact_path: str | None = None
    source_retention_custody_notice_verification_declared_sha256: str | None = None
    source_retention_custody_notice_verification_computed_sha256: str | None = None
    source_retention_custody_notice_verification_status: str | None = None
    source_retention_custody_notice_verification_trust_banner: str | None = None
    retention_custody_notice_verification_artifact_hash_valid: bool = False
    source_retention_custody_notice_status: str | None = None
    retention_custody_notice_artifact_hash_valid: bool = False
    custody_notice_id: str | None = None
    custody_notice_statement_hash_valid: bool = False
    notice_generated_for_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    reminder_window_starts_at_utc: str | None = None
    days_until_due: int = 0
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    notice_message: str | None = None
    custody_schedule_id: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_acknowledgment_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_acknowledgment_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentView(BaseModel):
    """Read-plane summary of paper evidence retention custody renewal notice acknowledgments."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_acknowledgment_view/v1"] = "paper_execution_evidence_bundle_retention_custody_acknowledgment_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    acknowledgment_status: Literal["ACKNOWLEDGED", "ACKNOWLEDGED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_acknowledgment_id: str | None = None
    acknowledged_by: str | None = None
    custody_location: str | None = None
    acknowledged_at_utc: str | None = None
    acknowledgment_note: str | None = None
    source_retention_custody_notice_verification_artifact_path: str | None = None
    source_retention_custody_notice_verification_status: str | None = None
    retention_custody_notice_verification_artifact_hash_valid: bool = False
    source_retention_custody_notice_status: str | None = None
    retention_custody_notice_artifact_hash_valid: bool = False
    custody_notice_id: str | None = None
    custody_notice_statement_hash_valid: bool = False
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_acknowledgment_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody renewal notice acknowledgments."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_acknowledgment_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_acknowledgment_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    no_files_copied: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    acknowledgment_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_ACKNOWLEDGMENT_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_ACKNOWLEDGMENT_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_acknowledgment_artifact_path: str | None = None
    source_retention_custody_acknowledgment_declared_sha256: str | None = None
    source_retention_custody_acknowledgment_computed_sha256: str | None = None
    source_retention_custody_acknowledgment_status: str | None = None
    source_retention_custody_acknowledgment_trust_banner: str | None = None
    retention_custody_acknowledgment_artifact_hash_valid: bool = False
    custody_acknowledgment_id: str | None = None
    acknowledged_by: str | None = None
    custody_location: str | None = None
    acknowledged_at_utc: str | None = None
    acknowledgment_note: str | None = None
    custody_acknowledgment_statement_declared_sha256: str | None = None
    custody_acknowledgment_statement_computed_sha256: str | None = None
    custody_acknowledgment_statement_hash_valid: bool = False
    source_retention_custody_notice_verification_artifact_path: str | None = None
    source_retention_custody_notice_verification_status: str | None = None
    retention_custody_notice_verification_artifact_hash_valid: bool = False
    source_retention_custody_notice_status: str | None = None
    retention_custody_notice_artifact_hash_valid: bool = False
    custody_notice_id: str | None = None
    custody_notice_statement_hash_valid: bool = False
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_acknowledgment_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody renewal acknowledgment verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_acknowledgment_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_acknowledgment_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_acknowledgment_artifact_path: str | None = None
    source_retention_custody_acknowledgment_status: str | None = None
    retention_custody_acknowledgment_artifact_hash_valid: bool = False
    custody_acknowledgment_id: str | None = None
    acknowledged_by: str | None = None
    custody_location: str | None = None
    acknowledged_at_utc: str | None = None
    custody_acknowledgment_statement_hash_valid: bool = False
    source_retention_custody_notice_verification_artifact_path: str | None = None
    source_retention_custody_notice_verification_status: str | None = None
    retention_custody_notice_verification_artifact_hash_valid: bool = False
    source_retention_custody_notice_status: str | None = None
    retention_custody_notice_artifact_hash_valid: bool = False
    custody_notice_id: str | None = None
    custody_notice_statement_hash_valid: bool = False
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


__all__ = (
    "PaperExecutionEvidenceBundleRetentionCustodyNoticeArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyNoticeView",
    "PaperExecutionEvidenceBundleRetentionCustodyNoticeVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyNoticeVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentView",
    "PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentVerificationView",
)
