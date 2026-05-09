"""Paper execution evidence-bundle retention operator signoff and verification contracts."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *
from strategy_validator.contracts.paper_execution_evidence_bundle import *

class PaperExecutionEvidenceBundleRetentionSignoffArtifact(BaseModel):
    """Read-only operator signoff certificate for a verified retention receipt."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_signoff/v1"] = "paper_execution_evidence_bundle_retention_signoff/v1"
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
    signoff_authority: Literal["READ_ONLY_OPERATOR_SIGNOFF"] = "READ_ONLY_OPERATOR_SIGNOFF"
    signoff_status: Literal["SIGNED_OFF", "SIGNED_OFF_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    operator_id: str = "operator"
    decision_note: str | None = None
    source_retention_verification_artifact_path: str | None = None
    source_retention_verification_declared_sha256: str | None = None
    source_retention_verification_computed_sha256: str | None = None
    source_retention_verification_status: str | None = None
    source_retention_verification_trust_banner: str | None = None
    retention_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    source_retention_entry_count: int = 0
    source_retention_ready_entry_count: int = 0
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    checklist: list[str] = Field(default_factory=list)
    signoff_statement_sha256: str | None = None
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_signoff_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v

class PaperExecutionEvidenceBundleRetentionSignoffView(BaseModel):
    """Read-plane summary of paper retention signoff certificates."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_signoff_view/v1"] = "paper_execution_evidence_bundle_retention_signoff_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    signoff_status: Literal["SIGNED_OFF", "SIGNED_OFF_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    operator_id: str | None = None
    decision_note: str | None = None
    source_retention_verification_artifact_path: str | None = None
    source_retention_verification_declared_sha256: str | None = None
    source_retention_verification_status: str | None = None
    source_retention_verification_trust_banner: str | None = None
    retention_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    signoff_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

class PaperExecutionEvidenceBundleRetentionSignoffVerificationArtifact(BaseModel):
    """Read-only verifier for a paper retention signoff certificate."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_signoff_verification/v1"] = "paper_execution_evidence_bundle_retention_signoff_verification/v1"
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
    signoff_verification_authority: Literal["READ_ONLY_SIGNOFF_VERIFICATION"] = "READ_ONLY_SIGNOFF_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_signoff_artifact_path: str | None = None
    source_retention_signoff_declared_sha256: str | None = None
    source_retention_signoff_computed_sha256: str | None = None
    source_retention_signoff_status: str | None = None
    source_retention_signoff_trust_banner: str | None = None
    retention_signoff_artifact_hash_valid: bool = False
    operator_id: str | None = None
    decision_note: str | None = None
    signoff_statement_declared_sha256: str | None = None
    signoff_statement_computed_sha256: str | None = None
    signoff_statement_hash_valid: bool = False
    source_retention_verification_artifact_path: str | None = None
    source_retention_verification_declared_sha256: str | None = None
    source_retention_verification_computed_sha256: str | None = None
    source_retention_verification_recomputed_sha256: str | None = None
    source_retention_verification_status: str | None = None
    source_retention_verification_trust_banner: str | None = None
    retention_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    source_retention_entry_count: int = 0
    source_retention_ready_entry_count: int = 0
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
    def _retention_signoff_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v

class PaperExecutionEvidenceBundleRetentionSignoffVerificationView(BaseModel):
    """Read-plane summary of retention signoff verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_signoff_verification_view/v1"] = "paper_execution_evidence_bundle_retention_signoff_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_signoff_artifact_path: str | None = None
    source_retention_signoff_declared_sha256: str | None = None
    source_retention_signoff_computed_sha256: str | None = None
    source_retention_signoff_status: str | None = None
    source_retention_signoff_trust_banner: str | None = None
    retention_signoff_artifact_hash_valid: bool = False
    operator_id: str | None = None
    decision_note: str | None = None
    signoff_statement_declared_sha256: str | None = None
    signoff_statement_computed_sha256: str | None = None
    signoff_statement_hash_valid: bool = False
    source_retention_verification_artifact_path: str | None = None
    source_retention_verification_declared_sha256: str | None = None
    source_retention_verification_status: str | None = None
    source_retention_verification_trust_banner: str | None = None
    retention_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
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
    "PaperExecutionEvidenceBundleRetentionSignoffArtifact",
    "PaperExecutionEvidenceBundleRetentionSignoffView",
    "PaperExecutionEvidenceBundleRetentionSignoffVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionSignoffVerificationView",
)
