"""Paper execution retention custody completion/closeout contract models."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *
from strategy_validator.contracts.paper_execution_evidence_bundle import *
from strategy_validator.contracts.paper_execution_retention import *
from strategy_validator.contracts.paper_execution_retention_custody_chain import *


class PaperExecutionEvidenceBundleRetentionCustodyCompletionArtifact(BaseModel):
    """Read-only completion record for an acknowledged paper evidence retention custody renewal."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_completion/v1"] = "paper_execution_evidence_bundle_retention_custody_completion/v1"
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
    completion_authority: Literal["READ_ONLY_RETENTION_CUSTODY_COMPLETION"] = "READ_ONLY_RETENTION_CUSTODY_COMPLETION"
    completion_status: Literal["COMPLETED", "COMPLETED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_completion_id: str | None = None
    completed_by: str | None = None
    custody_location: str | None = None
    completed_at_utc: str | None = None
    completion_note: str | None = None
    source_retention_custody_acknowledgment_verification_artifact_path: str | None = None
    source_retention_custody_acknowledgment_verification_declared_sha256: str | None = None
    source_retention_custody_acknowledgment_verification_computed_sha256: str | None = None
    source_retention_custody_acknowledgment_verification_status: str | None = None
    source_retention_custody_acknowledgment_verification_trust_banner: str | None = None
    retention_custody_acknowledgment_verification_artifact_hash_valid: bool = False
    source_retention_custody_acknowledgment_status: str | None = None
    retention_custody_acknowledgment_artifact_hash_valid: bool = False
    custody_acknowledgment_id: str | None = None
    custody_acknowledgment_statement_hash_valid: bool = False
    acknowledged_by: str | None = None
    acknowledged_at_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_completion_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_completion_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyCompletionView(BaseModel):
    """Read-plane summary of paper evidence retention custody completion records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_completion_view/v1"] = "paper_execution_evidence_bundle_retention_custody_completion_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    completion_status: Literal["COMPLETED", "COMPLETED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_completion_id: str | None = None
    completed_by: str | None = None
    custody_location: str | None = None
    completed_at_utc: str | None = None
    completion_note: str | None = None
    source_retention_custody_acknowledgment_verification_artifact_path: str | None = None
    source_retention_custody_acknowledgment_verification_status: str | None = None
    retention_custody_acknowledgment_verification_artifact_hash_valid: bool = False
    source_retention_custody_acknowledgment_status: str | None = None
    retention_custody_acknowledgment_artifact_hash_valid: bool = False
    custody_acknowledgment_id: str | None = None
    custody_acknowledgment_statement_hash_valid: bool = False
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_completion_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyCompletionVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody completion records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_completion_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_completion_verification/v1"
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
    completion_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_COMPLETION_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_COMPLETION_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_completion_artifact_path: str | None = None
    source_retention_custody_completion_declared_sha256: str | None = None
    source_retention_custody_completion_computed_sha256: str | None = None
    source_retention_custody_completion_status: str | None = None
    source_retention_custody_completion_trust_banner: str | None = None
    retention_custody_completion_artifact_hash_valid: bool = False
    custody_completion_id: str | None = None
    completed_by: str | None = None
    custody_location: str | None = None
    completed_at_utc: str | None = None
    completion_note: str | None = None
    custody_completion_statement_declared_sha256: str | None = None
    custody_completion_statement_computed_sha256: str | None = None
    custody_completion_statement_hash_valid: bool = False
    source_retention_custody_acknowledgment_verification_artifact_path: str | None = None
    source_retention_custody_acknowledgment_verification_status: str | None = None
    retention_custody_acknowledgment_verification_artifact_hash_valid: bool = False
    source_retention_custody_acknowledgment_status: str | None = None
    retention_custody_acknowledgment_artifact_hash_valid: bool = False
    custody_acknowledgment_id: str | None = None
    custody_acknowledgment_statement_hash_valid: bool = False
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
    def _retention_custody_completion_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyCompletionVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody completion verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_completion_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_completion_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_completion_artifact_path: str | None = None
    source_retention_custody_completion_status: str | None = None
    retention_custody_completion_artifact_hash_valid: bool = False
    custody_completion_id: str | None = None
    completed_by: str | None = None
    custody_location: str | None = None
    completed_at_utc: str | None = None
    custody_completion_statement_hash_valid: bool = False
    source_retention_custody_acknowledgment_verification_artifact_path: str | None = None
    source_retention_custody_acknowledgment_verification_status: str | None = None
    retention_custody_acknowledgment_verification_artifact_hash_valid: bool = False
    source_retention_custody_acknowledgment_status: str | None = None
    retention_custody_acknowledgment_artifact_hash_valid: bool = False
    custody_acknowledgment_id: str | None = None
    custody_acknowledgment_statement_hash_valid: bool = False
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


class PaperExecutionEvidenceBundleRetentionCustodyCloseoutArtifact(BaseModel):
    """Read-only closeout record for a verified paper evidence retention custody renewal completion."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_closeout/v1"] = "paper_execution_evidence_bundle_retention_custody_closeout/v1"
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
    closeout_authority: Literal["READ_ONLY_RETENTION_CUSTODY_CLOSEOUT"] = "READ_ONLY_RETENTION_CUSTODY_CLOSEOUT"
    closeout_status: Literal["CLOSED", "CLOSED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_closeout_id: str | None = None
    closed_out_by: str | None = None
    custody_location: str | None = None
    closed_out_at_utc: str | None = None
    closeout_note: str | None = None
    source_retention_custody_completion_verification_artifact_path: str | None = None
    source_retention_custody_completion_verification_declared_sha256: str | None = None
    source_retention_custody_completion_verification_computed_sha256: str | None = None
    source_retention_custody_completion_verification_status: str | None = None
    source_retention_custody_completion_verification_trust_banner: str | None = None
    retention_custody_completion_verification_artifact_hash_valid: bool = False
    source_retention_custody_completion_status: str | None = None
    retention_custody_completion_artifact_hash_valid: bool = False
    custody_completion_id: str | None = None
    custody_completion_statement_hash_valid: bool = False
    completed_by: str | None = None
    completed_at_utc: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_closeout_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_closeout_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyCloseoutView(BaseModel):
    """Read-plane summary of paper evidence retention custody closeout records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_closeout_view/v1"] = "paper_execution_evidence_bundle_retention_custody_closeout_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    closeout_status: Literal["CLOSED", "CLOSED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_closeout_id: str | None = None
    closed_out_by: str | None = None
    custody_location: str | None = None
    closed_out_at_utc: str | None = None
    closeout_note: str | None = None
    source_retention_custody_completion_verification_artifact_path: str | None = None
    source_retention_custody_completion_verification_status: str | None = None
    retention_custody_completion_verification_artifact_hash_valid: bool = False
    source_retention_custody_completion_status: str | None = None
    retention_custody_completion_artifact_hash_valid: bool = False
    custody_completion_id: str | None = None
    custody_completion_statement_hash_valid: bool = False
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_closeout_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyCloseoutVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody closeout records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_closeout_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_closeout_verification/v1"
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
    closeout_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_CLOSEOUT_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_CLOSEOUT_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_closeout_artifact_path: str | None = None
    source_retention_custody_closeout_declared_sha256: str | None = None
    source_retention_custody_closeout_computed_sha256: str | None = None
    source_retention_custody_closeout_status: str | None = None
    source_retention_custody_closeout_trust_banner: str | None = None
    retention_custody_closeout_artifact_hash_valid: bool = False
    custody_closeout_id: str | None = None
    closed_out_by: str | None = None
    custody_location: str | None = None
    closed_out_at_utc: str | None = None
    closeout_note: str | None = None
    custody_closeout_statement_declared_sha256: str | None = None
    custody_closeout_statement_computed_sha256: str | None = None
    custody_closeout_statement_hash_valid: bool = False
    source_retention_custody_completion_verification_artifact_path: str | None = None
    source_retention_custody_completion_verification_status: str | None = None
    retention_custody_completion_verification_artifact_hash_valid: bool = False
    source_retention_custody_completion_status: str | None = None
    retention_custody_completion_artifact_hash_valid: bool = False
    custody_completion_id: str | None = None
    custody_completion_statement_hash_valid: bool = False
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
    def _retention_custody_closeout_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyCloseoutVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody closeout verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_closeout_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_closeout_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_closeout_artifact_path: str | None = None
    source_retention_custody_closeout_status: str | None = None
    retention_custody_closeout_artifact_hash_valid: bool = False
    custody_closeout_id: str | None = None
    closed_out_by: str | None = None
    custody_location: str | None = None
    closed_out_at_utc: str | None = None
    custody_closeout_statement_hash_valid: bool = False
    source_retention_custody_completion_verification_artifact_path: str | None = None
    source_retention_custody_completion_verification_status: str | None = None
    retention_custody_completion_verification_artifact_hash_valid: bool = False
    source_retention_custody_completion_status: str | None = None
    retention_custody_completion_artifact_hash_valid: bool = False
    custody_completion_id: str | None = None
    custody_completion_statement_hash_valid: bool = False
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
    "PaperExecutionEvidenceBundleRetentionCustodyCompletionArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyCompletionView",
    "PaperExecutionEvidenceBundleRetentionCustodyCompletionVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyCompletionVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyCloseoutArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyCloseoutView",
    "PaperExecutionEvidenceBundleRetentionCustodyCloseoutVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyCloseoutVerificationView",
)
