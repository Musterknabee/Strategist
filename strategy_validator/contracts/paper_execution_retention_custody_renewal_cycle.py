"""Paper execution retention custody renewal/schedule contract models."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *
from strategy_validator.contracts.paper_execution_evidence_bundle import *
from strategy_validator.contracts.paper_execution_retention import *
from strategy_validator.contracts.paper_execution_retention_custody_chain import *


class PaperExecutionEvidenceBundleRetentionCustodyRenewalArtifact(BaseModel):
    """Read-only renewal certificate for verified paper evidence retention custody reviews."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_renewal/v1"] = "paper_execution_evidence_bundle_retention_custody_renewal/v1"
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
    renewal_authority: Literal["READ_ONLY_RETENTION_CUSTODY_RENEWAL"] = "READ_ONLY_RETENTION_CUSTODY_RENEWAL"
    renewal_status: Literal["RENEWED", "RENEWAL_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_renewal_id: str | None = None
    renewed_by: str | None = None
    custody_location: str | None = None
    renewal_interval_days: int = 30
    renewal_note: str | None = None
    source_retention_custody_review_verification_artifact_path: str | None = None
    source_retention_custody_review_verification_declared_sha256: str | None = None
    source_retention_custody_review_verification_computed_sha256: str | None = None
    source_retention_custody_review_verification_status: str | None = None
    source_retention_custody_review_verification_trust_banner: str | None = None
    retention_custody_review_verification_artifact_hash_valid: bool = False
    source_retention_custody_review_status: str | None = None
    retention_custody_review_artifact_hash_valid: bool = False
    custody_review_id: str | None = None
    custody_review_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_renewal_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_renewal_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyRenewalView(BaseModel):
    """Read-plane summary of paper evidence retention custody renewal certificates."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_renewal_view/v1"] = "paper_execution_evidence_bundle_retention_custody_renewal_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    renewal_status: Literal["RENEWED", "RENEWAL_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_renewal_id: str | None = None
    renewed_by: str | None = None
    custody_location: str | None = None
    renewal_interval_days: int = 30
    renewal_note: str | None = None
    source_retention_custody_review_verification_artifact_path: str | None = None
    source_retention_custody_review_verification_status: str | None = None
    retention_custody_review_verification_artifact_hash_valid: bool = False
    source_retention_custody_review_status: str | None = None
    retention_custody_review_artifact_hash_valid: bool = False
    custody_review_id: str | None = None
    custody_review_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_renewal_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyRenewalVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody renewal certificates."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_renewal_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_renewal_verification/v1"
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
    renewal_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_RENEWAL_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_RENEWAL_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_renewal_artifact_path: str | None = None
    source_retention_custody_renewal_declared_sha256: str | None = None
    source_retention_custody_renewal_computed_sha256: str | None = None
    source_retention_custody_renewal_status: str | None = None
    source_retention_custody_renewal_trust_banner: str | None = None
    retention_custody_renewal_artifact_hash_valid: bool = False
    custody_renewal_id: str | None = None
    renewed_by: str | None = None
    custody_location: str | None = None
    renewal_interval_days: int = 30
    renewal_note: str | None = None
    custody_renewal_statement_declared_sha256: str | None = None
    custody_renewal_statement_computed_sha256: str | None = None
    custody_renewal_statement_hash_valid: bool = False
    source_retention_custody_review_verification_artifact_path: str | None = None
    source_retention_custody_review_verification_status: str | None = None
    retention_custody_review_verification_artifact_hash_valid: bool = False
    source_retention_custody_review_status: str | None = None
    retention_custody_review_artifact_hash_valid: bool = False
    custody_review_id: str | None = None
    custody_review_statement_hash_valid: bool = False
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
    def _retention_custody_renewal_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyRenewalVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody renewal verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_renewal_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_renewal_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_renewal_artifact_path: str | None = None
    source_retention_custody_renewal_status: str | None = None
    retention_custody_renewal_artifact_hash_valid: bool = False
    custody_renewal_id: str | None = None
    renewed_by: str | None = None
    custody_location: str | None = None
    renewal_interval_days: int = 30
    renewal_note: str | None = None
    custody_renewal_statement_hash_valid: bool = False
    source_retention_custody_review_verification_artifact_path: str | None = None
    source_retention_custody_review_verification_status: str | None = None
    retention_custody_review_verification_artifact_hash_valid: bool = False
    source_retention_custody_review_status: str | None = None
    retention_custody_review_artifact_hash_valid: bool = False
    custody_review_id: str | None = None
    custody_review_statement_hash_valid: bool = False
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


class PaperExecutionEvidenceBundleRetentionCustodyScheduleArtifact(BaseModel):
    """Read-only schedule for the next verified paper evidence retention custody renewal."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_schedule/v1"] = "paper_execution_evidence_bundle_retention_custody_schedule/v1"
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
    schedule_authority: Literal["READ_ONLY_RETENTION_CUSTODY_SCHEDULE"] = "READ_ONLY_RETENTION_CUSTODY_SCHEDULE"
    schedule_status: Literal["SCHEDULED", "SCHEDULE_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_schedule_id: str | None = None
    scheduled_by: str | None = None
    custody_location: str | None = None
    schedule_start_at_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    schedule_note: str | None = None
    source_retention_custody_renewal_verification_artifact_path: str | None = None
    source_retention_custody_renewal_verification_declared_sha256: str | None = None
    source_retention_custody_renewal_verification_computed_sha256: str | None = None
    source_retention_custody_renewal_verification_status: str | None = None
    source_retention_custody_renewal_verification_trust_banner: str | None = None
    retention_custody_renewal_verification_artifact_hash_valid: bool = False
    source_retention_custody_renewal_status: str | None = None
    retention_custody_renewal_artifact_hash_valid: bool = False
    custody_renewal_id: str | None = None
    custody_renewal_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_schedule_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_schedule_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyScheduleView(BaseModel):
    """Read-plane summary of paper evidence retention custody renewal schedules."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_schedule_view/v1"] = "paper_execution_evidence_bundle_retention_custody_schedule_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    schedule_status: Literal["SCHEDULED", "SCHEDULE_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_schedule_id: str | None = None
    scheduled_by: str | None = None
    custody_location: str | None = None
    schedule_start_at_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    schedule_note: str | None = None
    source_retention_custody_renewal_verification_artifact_path: str | None = None
    source_retention_custody_renewal_verification_status: str | None = None
    retention_custody_renewal_verification_artifact_hash_valid: bool = False
    source_retention_custody_renewal_status: str | None = None
    retention_custody_renewal_artifact_hash_valid: bool = False
    custody_renewal_id: str | None = None
    custody_renewal_statement_hash_valid: bool = False
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_schedule_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyScheduleVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody renewal schedules."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_schedule_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_schedule_verification/v1"
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
    schedule_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_SCHEDULE_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_SCHEDULE_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_schedule_artifact_path: str | None = None
    source_retention_custody_schedule_declared_sha256: str | None = None
    source_retention_custody_schedule_computed_sha256: str | None = None
    source_retention_custody_schedule_status: str | None = None
    source_retention_custody_schedule_trust_banner: str | None = None
    retention_custody_schedule_artifact_hash_valid: bool = False
    custody_schedule_id: str | None = None
    scheduled_by: str | None = None
    custody_location: str | None = None
    schedule_start_at_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    schedule_note: str | None = None
    custody_schedule_statement_declared_sha256: str | None = None
    custody_schedule_statement_computed_sha256: str | None = None
    custody_schedule_statement_hash_valid: bool = False
    source_retention_custody_renewal_verification_artifact_path: str | None = None
    source_retention_custody_renewal_verification_status: str | None = None
    retention_custody_renewal_verification_artifact_hash_valid: bool = False
    source_retention_custody_renewal_status: str | None = None
    retention_custody_renewal_artifact_hash_valid: bool = False
    custody_renewal_id: str | None = None
    custody_renewal_statement_hash_valid: bool = False
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
    def _retention_custody_schedule_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyScheduleVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody renewal schedule verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_schedule_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_schedule_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_schedule_artifact_path: str | None = None
    source_retention_custody_schedule_status: str | None = None
    retention_custody_schedule_artifact_hash_valid: bool = False
    custody_schedule_id: str | None = None
    scheduled_by: str | None = None
    custody_location: str | None = None
    schedule_start_at_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    renewal_interval_days: int = 30
    reminder_days_before_due: int = 7
    custody_schedule_statement_hash_valid: bool = False
    source_retention_custody_renewal_verification_artifact_path: str | None = None
    source_retention_custody_renewal_verification_status: str | None = None
    retention_custody_renewal_verification_artifact_hash_valid: bool = False
    source_retention_custody_renewal_status: str | None = None
    retention_custody_renewal_artifact_hash_valid: bool = False
    custody_renewal_id: str | None = None
    custody_renewal_statement_hash_valid: bool = False
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
    "PaperExecutionEvidenceBundleRetentionCustodyRenewalArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyRenewalView",
    "PaperExecutionEvidenceBundleRetentionCustodyRenewalVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyRenewalVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyScheduleArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyScheduleView",
    "PaperExecutionEvidenceBundleRetentionCustodyScheduleVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyScheduleVerificationView",
)
