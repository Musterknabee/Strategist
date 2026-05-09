"""Paper execution retention custody archive/retrieval contract models."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *
from strategy_validator.contracts.paper_execution_evidence_bundle import *
from strategy_validator.contracts.paper_execution_retention import *
from strategy_validator.contracts.paper_execution_retention_custody_chain import *
from strategy_validator.contracts.paper_execution_retention_custody_renewal import *


class PaperExecutionEvidenceBundleRetentionCustodyArchiveArtifact(BaseModel):
    """Read-only archive record for a verified paper evidence retention custody closeout."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_archive/v1"] = "paper_execution_evidence_bundle_retention_custody_archive/v1"
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
    archive_authority: Literal["READ_ONLY_RETENTION_CUSTODY_ARCHIVE"] = "READ_ONLY_RETENTION_CUSTODY_ARCHIVE"
    archive_status: Literal["ARCHIVED", "ARCHIVED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_archive_id: str | None = None
    archived_by: str | None = None
    custody_location: str | None = None
    archived_at_utc: str | None = None
    archive_note: str | None = None
    source_retention_custody_closeout_verification_artifact_path: str | None = None
    source_retention_custody_closeout_verification_declared_sha256: str | None = None
    source_retention_custody_closeout_verification_computed_sha256: str | None = None
    source_retention_custody_closeout_verification_status: str | None = None
    source_retention_custody_closeout_verification_trust_banner: str | None = None
    retention_custody_closeout_verification_artifact_hash_valid: bool = False
    source_retention_custody_closeout_status: str | None = None
    retention_custody_closeout_artifact_hash_valid: bool = False
    custody_closeout_id: str | None = None
    custody_closeout_statement_hash_valid: bool = False
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_archive_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_archive_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyArchiveView(BaseModel):
    """Read-plane summary of paper evidence retention custody archive records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_archive_view/v1"] = "paper_execution_evidence_bundle_retention_custody_archive_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    archive_status: Literal["ARCHIVED", "ARCHIVED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_archive_id: str | None = None
    archived_by: str | None = None
    custody_location: str | None = None
    archived_at_utc: str | None = None
    archive_note: str | None = None
    source_retention_custody_closeout_verification_artifact_path: str | None = None
    source_retention_custody_closeout_verification_status: str | None = None
    retention_custody_closeout_verification_artifact_hash_valid: bool = False
    source_retention_custody_closeout_status: str | None = None
    retention_custody_closeout_artifact_hash_valid: bool = False
    custody_closeout_id: str | None = None
    custody_closeout_statement_hash_valid: bool = False
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_archive_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyArchiveVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody archive records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_archive_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_archive_verification/v1"
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
    archive_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_ARCHIVE_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_ARCHIVE_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_archive_artifact_path: str | None = None
    source_retention_custody_archive_declared_sha256: str | None = None
    source_retention_custody_archive_computed_sha256: str | None = None
    source_retention_custody_archive_status: str | None = None
    source_retention_custody_archive_trust_banner: str | None = None
    retention_custody_archive_artifact_hash_valid: bool = False
    custody_archive_id: str | None = None
    archived_by: str | None = None
    custody_location: str | None = None
    archived_at_utc: str | None = None
    archive_note: str | None = None
    custody_archive_statement_declared_sha256: str | None = None
    custody_archive_statement_computed_sha256: str | None = None
    custody_archive_statement_hash_valid: bool = False
    source_retention_custody_closeout_verification_artifact_path: str | None = None
    source_retention_custody_closeout_verification_status: str | None = None
    retention_custody_closeout_verification_artifact_hash_valid: bool = False
    source_retention_custody_closeout_status: str | None = None
    retention_custody_closeout_artifact_hash_valid: bool = False
    custody_closeout_id: str | None = None
    custody_closeout_statement_hash_valid: bool = False
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
    def _retention_custody_archive_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyArchiveVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody archive verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_archive_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_archive_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_archive_artifact_path: str | None = None
    source_retention_custody_archive_status: str | None = None
    retention_custody_archive_artifact_hash_valid: bool = False
    custody_archive_id: str | None = None
    archived_by: str | None = None
    custody_location: str | None = None
    archived_at_utc: str | None = None
    custody_archive_statement_hash_valid: bool = False
    source_retention_custody_closeout_verification_artifact_path: str | None = None
    source_retention_custody_closeout_verification_status: str | None = None
    retention_custody_closeout_verification_artifact_hash_valid: bool = False
    source_retention_custody_closeout_status: str | None = None
    retention_custody_closeout_artifact_hash_valid: bool = False
    custody_closeout_id: str | None = None
    custody_closeout_statement_hash_valid: bool = False
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


class PaperExecutionEvidenceBundleRetentionCustodyRetrievalArtifact(BaseModel):
    """Read-only retrieval record for verified archived paper evidence retention custody."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_retrieval/v1"] = "paper_execution_evidence_bundle_retention_custody_retrieval/v1"
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
    retrieval_authority: Literal["READ_ONLY_RETENTION_CUSTODY_RETRIEVAL"] = "READ_ONLY_RETENTION_CUSTODY_RETRIEVAL"
    retrieval_status: Literal["RETRIEVED", "RETRIEVED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_retrieval_id: str | None = None
    retrieved_by: str | None = None
    retrieval_purpose: str | None = None
    custody_location: str | None = None
    retrieved_at_utc: str | None = None
    retrieval_note: str | None = None
    source_retention_custody_archive_verification_artifact_path: str | None = None
    source_retention_custody_archive_verification_declared_sha256: str | None = None
    source_retention_custody_archive_verification_computed_sha256: str | None = None
    source_retention_custody_archive_verification_status: str | None = None
    source_retention_custody_archive_verification_trust_banner: str | None = None
    retention_custody_archive_verification_artifact_hash_valid: bool = False
    source_retention_custody_archive_status: str | None = None
    retention_custody_archive_artifact_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_archive_statement_hash_valid: bool = False
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_retrieval_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_retrieval_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyRetrievalView(BaseModel):
    """Read-plane summary of paper evidence retention custody retrieval records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_retrieval_view/v1"] = "paper_execution_evidence_bundle_retention_custody_retrieval_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    retrieval_status: Literal["RETRIEVED", "RETRIEVED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_retrieval_id: str | None = None
    retrieved_by: str | None = None
    retrieval_purpose: str | None = None
    custody_location: str | None = None
    retrieved_at_utc: str | None = None
    retrieval_note: str | None = None
    source_retention_custody_archive_verification_artifact_path: str | None = None
    source_retention_custody_archive_verification_status: str | None = None
    retention_custody_archive_verification_artifact_hash_valid: bool = False
    source_retention_custody_archive_status: str | None = None
    retention_custody_archive_artifact_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_archive_statement_hash_valid: bool = False
    custody_closeout_id: str | None = None
    custody_completion_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_retrieval_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyRetrievalVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody retrieval records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_retrieval_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_retrieval_verification/v1"
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
    retrieval_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_RETRIEVAL_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_RETRIEVAL_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_retrieval_artifact_path: str | None = None
    source_retention_custody_retrieval_declared_sha256: str | None = None
    source_retention_custody_retrieval_computed_sha256: str | None = None
    source_retention_custody_retrieval_status: str | None = None
    source_retention_custody_retrieval_trust_banner: str | None = None
    retention_custody_retrieval_artifact_hash_valid: bool = False
    custody_retrieval_id: str | None = None
    retrieved_by: str | None = None
    retrieval_purpose: str | None = None
    custody_location: str | None = None
    retrieved_at_utc: str | None = None
    retrieval_note: str | None = None
    custody_retrieval_statement_declared_sha256: str | None = None
    custody_retrieval_statement_computed_sha256: str | None = None
    custody_retrieval_statement_hash_valid: bool = False
    source_retention_custody_archive_verification_artifact_path: str | None = None
    source_retention_custody_archive_verification_status: str | None = None
    retention_custody_archive_verification_artifact_hash_valid: bool = False
    source_retention_custody_archive_status: str | None = None
    retention_custody_archive_artifact_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_archive_statement_hash_valid: bool = False
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
    def _retention_custody_retrieval_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyRetrievalVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody retrieval verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_retrieval_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_retrieval_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_retrieval_artifact_path: str | None = None
    source_retention_custody_retrieval_status: str | None = None
    retention_custody_retrieval_artifact_hash_valid: bool = False
    custody_retrieval_id: str | None = None
    retrieved_by: str | None = None
    retrieval_purpose: str | None = None
    custody_location: str | None = None
    retrieved_at_utc: str | None = None
    custody_retrieval_statement_hash_valid: bool = False
    source_retention_custody_archive_verification_artifact_path: str | None = None
    source_retention_custody_archive_verification_status: str | None = None
    retention_custody_archive_verification_artifact_hash_valid: bool = False
    source_retention_custody_archive_status: str | None = None
    retention_custody_archive_artifact_hash_valid: bool = False
    custody_archive_id: str | None = None
    custody_archive_statement_hash_valid: bool = False
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
    "PaperExecutionEvidenceBundleRetentionCustodyArchiveArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyArchiveView",
    "PaperExecutionEvidenceBundleRetentionCustodyArchiveVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyArchiveVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyRetrievalArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyRetrievalView",
    "PaperExecutionEvidenceBundleRetentionCustodyRetrievalVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyRetrievalVerificationView",
)
