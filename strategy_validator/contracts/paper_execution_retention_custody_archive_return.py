"""Paper execution retention custody return/redeposit contract models."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *
from strategy_validator.contracts.paper_execution_evidence_bundle import *
from strategy_validator.contracts.paper_execution_retention import *
from strategy_validator.contracts.paper_execution_retention_custody_chain import *
from strategy_validator.contracts.paper_execution_retention_custody_renewal import *


class PaperExecutionEvidenceBundleRetentionCustodyReturnArtifact(BaseModel):
    """Read-only return record for verified retrieved paper evidence retention custody."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_return/v1"] = "paper_execution_evidence_bundle_retention_custody_return/v1"
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
    return_authority: Literal["READ_ONLY_RETENTION_CUSTODY_RETURN"] = "READ_ONLY_RETENTION_CUSTODY_RETURN"
    return_status: Literal["RETURNED", "RETURNED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_return_id: str | None = None
    returned_by: str | None = None
    return_reason: str | None = None
    custody_location: str | None = None
    returned_at_utc: str | None = None
    return_note: str | None = None
    source_retention_custody_retrieval_verification_artifact_path: str | None = None
    source_retention_custody_retrieval_verification_declared_sha256: str | None = None
    source_retention_custody_retrieval_verification_computed_sha256: str | None = None
    source_retention_custody_retrieval_verification_status: str | None = None
    source_retention_custody_retrieval_verification_trust_banner: str | None = None
    retention_custody_retrieval_verification_artifact_hash_valid: bool = False
    source_retention_custody_retrieval_status: str | None = None
    retention_custody_retrieval_artifact_hash_valid: bool = False
    custody_retrieval_id: str | None = None
    custody_retrieval_statement_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_return_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_return_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyReturnView(BaseModel):
    """Read-plane summary of paper evidence retention custody return records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_return_view/v1"] = "paper_execution_evidence_bundle_retention_custody_return_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    return_status: Literal["RETURNED", "RETURNED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_return_id: str | None = None
    returned_by: str | None = None
    return_reason: str | None = None
    custody_location: str | None = None
    returned_at_utc: str | None = None
    return_note: str | None = None
    source_retention_custody_retrieval_verification_artifact_path: str | None = None
    source_retention_custody_retrieval_verification_status: str | None = None
    retention_custody_retrieval_verification_artifact_hash_valid: bool = False
    source_retention_custody_retrieval_status: str | None = None
    retention_custody_retrieval_artifact_hash_valid: bool = False
    custody_retrieval_id: str | None = None
    custody_retrieval_statement_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_return_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyReturnVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody return records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_return_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_return_verification/v1"
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
    return_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_RETURN_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_RETURN_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_return_artifact_path: str | None = None
    source_retention_custody_return_declared_sha256: str | None = None
    source_retention_custody_return_computed_sha256: str | None = None
    source_retention_custody_return_status: str | None = None
    source_retention_custody_return_trust_banner: str | None = None
    retention_custody_return_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
    returned_by: str | None = None
    return_reason: str | None = None
    custody_location: str | None = None
    returned_at_utc: str | None = None
    return_note: str | None = None
    custody_return_statement_declared_sha256: str | None = None
    custody_return_statement_computed_sha256: str | None = None
    custody_return_statement_hash_valid: bool = False
    source_retention_custody_retrieval_verification_artifact_path: str | None = None
    source_retention_custody_retrieval_verification_status: str | None = None
    retention_custody_retrieval_verification_artifact_hash_valid: bool = False
    source_retention_custody_retrieval_status: str | None = None
    retention_custody_retrieval_artifact_hash_valid: bool = False
    custody_retrieval_id: str | None = None
    custody_retrieval_statement_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
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
    def _retention_custody_return_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyReturnVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody return verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_return_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_return_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_return_artifact_path: str | None = None
    source_retention_custody_return_status: str | None = None
    retention_custody_return_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
    returned_by: str | None = None
    return_reason: str | None = None
    custody_location: str | None = None
    returned_at_utc: str | None = None
    custody_return_statement_hash_valid: bool = False
    source_retention_custody_retrieval_verification_artifact_path: str | None = None
    source_retention_custody_retrieval_verification_status: str | None = None
    retention_custody_retrieval_verification_artifact_hash_valid: bool = False
    source_retention_custody_retrieval_status: str | None = None
    retention_custody_retrieval_artifact_hash_valid: bool = False
    custody_retrieval_id: str | None = None
    custody_retrieval_statement_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
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


class PaperExecutionEvidenceBundleRetentionCustodyRedepositArtifact(BaseModel):
    """Read-only redeposit record for verified retrieved paper evidence retention custody."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_redeposit/v1"] = "paper_execution_evidence_bundle_retention_custody_redeposit/v1"
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
    redeposit_authority: Literal["READ_ONLY_RETENTION_CUSTODY_REDEPOSIT"] = "READ_ONLY_RETENTION_CUSTODY_REDEPOSIT"
    redeposit_status: Literal["REDEPOSITED", "REDEPOSITED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_redeposit_id: str | None = None
    redeposited_by: str | None = None
    redeposit_reason: str | None = None
    custody_location: str | None = None
    redeposited_at_utc: str | None = None
    redeposit_note: str | None = None
    source_retention_custody_return_verification_artifact_path: str | None = None
    source_retention_custody_return_verification_declared_sha256: str | None = None
    source_retention_custody_return_verification_computed_sha256: str | None = None
    source_retention_custody_return_verification_status: str | None = None
    source_retention_custody_return_verification_trust_banner: str | None = None
    retention_custody_return_verification_artifact_hash_valid: bool = False
    source_retention_custody_return_status: str | None = None
    retention_custody_return_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
    custody_return_statement_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_redeposit_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_redeposit_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyRedepositView(BaseModel):
    """Read-plane summary of paper evidence retention custody redeposit records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_redeposit_view/v1"] = "paper_execution_evidence_bundle_retention_custody_redeposit_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    redeposit_status: Literal["REDEPOSITED", "REDEPOSITED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_redeposit_id: str | None = None
    redeposited_by: str | None = None
    redeposit_reason: str | None = None
    custody_location: str | None = None
    redeposited_at_utc: str | None = None
    redeposit_note: str | None = None
    source_retention_custody_return_verification_artifact_path: str | None = None
    source_retention_custody_return_verification_status: str | None = None
    retention_custody_return_verification_artifact_hash_valid: bool = False
    source_retention_custody_return_status: str | None = None
    retention_custody_return_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
    custody_return_statement_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_redeposit_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyRedepositVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody redeposit records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_redeposit_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_redeposit_verification/v1"
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
    redeposit_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_REDEPOSIT_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_REDEPOSIT_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_redeposit_artifact_path: str | None = None
    source_retention_custody_redeposit_declared_sha256: str | None = None
    source_retention_custody_redeposit_computed_sha256: str | None = None
    source_retention_custody_redeposit_status: str | None = None
    source_retention_custody_redeposit_trust_banner: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    redeposited_by: str | None = None
    redeposit_reason: str | None = None
    custody_location: str | None = None
    redeposited_at_utc: str | None = None
    redeposit_note: str | None = None
    custody_redeposit_statement_declared_sha256: str | None = None
    custody_redeposit_statement_computed_sha256: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
    source_retention_custody_return_verification_artifact_path: str | None = None
    source_retention_custody_return_verification_status: str | None = None
    retention_custody_return_verification_artifact_hash_valid: bool = False
    source_retention_custody_return_status: str | None = None
    retention_custody_return_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
    custody_return_statement_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
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
    def _retention_custody_redeposit_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyRedepositVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody return verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_redeposit_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_redeposit_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_redeposit_artifact_path: str | None = None
    source_retention_custody_redeposit_status: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    redeposited_by: str | None = None
    redeposit_reason: str | None = None
    custody_location: str | None = None
    redeposited_at_utc: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
    source_retention_custody_return_verification_artifact_path: str | None = None
    source_retention_custody_return_verification_status: str | None = None
    retention_custody_return_verification_artifact_hash_valid: bool = False
    source_retention_custody_return_status: str | None = None
    retention_custody_return_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
    custody_return_statement_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
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
    "PaperExecutionEvidenceBundleRetentionCustodyReturnArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyReturnView",
    "PaperExecutionEvidenceBundleRetentionCustodyReturnVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyReturnVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyRedepositArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyRedepositView",
    "PaperExecutionEvidenceBundleRetentionCustodyRedepositVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyRedepositVerificationView",
)
