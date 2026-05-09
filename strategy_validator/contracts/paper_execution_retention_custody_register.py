"""Paper execution retention custody register/seal contract models."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *
from strategy_validator.contracts.paper_execution_evidence_bundle import *
from strategy_validator.contracts.paper_execution_retention import *


class PaperExecutionEvidenceBundleRetentionCustodyRegisterArtifact(BaseModel):
    """Read-only custody register entry for accepted paper evidence retention."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_register/v1"] = "paper_execution_evidence_bundle_retention_custody_register/v1"
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
    register_authority: Literal["READ_ONLY_RETENTION_CUSTODY_REGISTER"] = "READ_ONLY_RETENTION_CUSTODY_REGISTER"
    register_status: Literal["REGISTERED", "REGISTERED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_register_id: str | None = None
    registered_by: str | None = None
    custody_location: str | None = None
    register_note: str | None = None
    source_retention_handoff_acceptance_verification_artifact_path: str | None = None
    source_retention_handoff_acceptance_verification_declared_sha256: str | None = None
    source_retention_handoff_acceptance_verification_computed_sha256: str | None = None
    source_retention_handoff_acceptance_verification_status: str | None = None
    source_retention_handoff_acceptance_verification_trust_banner: str | None = None
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    source_retention_handoff_acceptance_artifact_path: str | None = None
    source_retention_handoff_acceptance_status: str | None = None
    source_retention_handoff_acceptance_trust_banner: str | None = None
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_register_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_register_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyRegisterView(BaseModel):
    """Read-plane summary of paper evidence retention custody register entries."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_register_view/v1"] = "paper_execution_evidence_bundle_retention_custody_register_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    register_status: Literal["REGISTERED", "REGISTERED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_register_id: str | None = None
    registered_by: str | None = None
    custody_location: str | None = None
    register_note: str | None = None
    source_retention_handoff_acceptance_verification_artifact_path: str | None = None
    source_retention_handoff_acceptance_verification_declared_sha256: str | None = None
    source_retention_handoff_acceptance_verification_status: str | None = None
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    source_retention_handoff_acceptance_status: str | None = None
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_register_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody register entries."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_register_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_register_verification/v1"
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
    register_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_REGISTER_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_REGISTER_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_register_artifact_path: str | None = None
    source_retention_custody_register_declared_sha256: str | None = None
    source_retention_custody_register_computed_sha256: str | None = None
    source_retention_custody_register_status: str | None = None
    source_retention_custody_register_trust_banner: str | None = None
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    registered_by: str | None = None
    custody_location: str | None = None
    register_note: str | None = None
    custody_register_statement_declared_sha256: str | None = None
    custody_register_statement_computed_sha256: str | None = None
    custody_register_statement_hash_valid: bool = False
    source_retention_handoff_acceptance_verification_artifact_path: str | None = None
    source_retention_handoff_acceptance_verification_declared_sha256: str | None = None
    source_retention_handoff_acceptance_verification_status: str | None = None
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
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
    def _retention_custody_register_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody register verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_register_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_register_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_register_artifact_path: str | None = None
    source_retention_custody_register_declared_sha256: str | None = None
    source_retention_custody_register_computed_sha256: str | None = None
    source_retention_custody_register_status: str | None = None
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    registered_by: str | None = None
    custody_location: str | None = None
    register_note: str | None = None
    custody_register_statement_declared_sha256: str | None = None
    custody_register_statement_computed_sha256: str | None = None
    custody_register_statement_hash_valid: bool = False
    source_retention_handoff_acceptance_verification_artifact_path: str | None = None
    source_retention_handoff_acceptance_verification_declared_sha256: str | None = None
    source_retention_handoff_acceptance_verification_status: str | None = None
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
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


class PaperExecutionEvidenceBundleRetentionCustodySealArtifact(BaseModel):
    """Read-only final seal for verified paper evidence retention custody."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_seal/v1"] = "paper_execution_evidence_bundle_retention_custody_seal/v1"
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
    seal_authority: Literal["READ_ONLY_RETENTION_CUSTODY_SEAL"] = "READ_ONLY_RETENTION_CUSTODY_SEAL"
    seal_status: Literal["SEALED", "SEALED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_seal_id: str | None = None
    sealed_by: str | None = None
    custody_location: str | None = None
    seal_note: str | None = None
    source_retention_custody_register_verification_artifact_path: str | None = None
    source_retention_custody_register_verification_declared_sha256: str | None = None
    source_retention_custody_register_verification_computed_sha256: str | None = None
    source_retention_custody_register_verification_status: str | None = None
    source_retention_custody_register_verification_trust_banner: str | None = None
    retention_custody_register_verification_artifact_hash_valid: bool = False
    source_retention_custody_register_artifact_path: str | None = None
    source_retention_custody_register_status: str | None = None
    source_retention_custody_register_trust_banner: str | None = None
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    source_retention_handoff_acceptance_verification_artifact_path: str | None = None
    source_retention_handoff_acceptance_verification_status: str | None = None
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_seal_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_seal_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodySealView(BaseModel):
    """Read-plane summary of paper evidence retention custody seals."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_seal_view/v1"] = "paper_execution_evidence_bundle_retention_custody_seal_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    seal_status: Literal["SEALED", "SEALED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_seal_id: str | None = None
    sealed_by: str | None = None
    custody_location: str | None = None
    seal_note: str | None = None
    source_retention_custody_register_verification_artifact_path: str | None = None
    source_retention_custody_register_verification_declared_sha256: str | None = None
    source_retention_custody_register_verification_status: str | None = None
    retention_custody_register_verification_artifact_hash_valid: bool = False
    source_retention_custody_register_status: str | None = None
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_seal_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodySealVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody seals."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_seal_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_seal_verification/v1"
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
    seal_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_SEAL_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_SEAL_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_seal_artifact_path: str | None = None
    source_retention_custody_seal_declared_sha256: str | None = None
    source_retention_custody_seal_computed_sha256: str | None = None
    source_retention_custody_seal_status: str | None = None
    source_retention_custody_seal_trust_banner: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    sealed_by: str | None = None
    custody_location: str | None = None
    seal_note: str | None = None
    custody_seal_statement_declared_sha256: str | None = None
    custody_seal_statement_computed_sha256: str | None = None
    custody_seal_statement_hash_valid: bool = False
    source_retention_custody_register_verification_artifact_path: str | None = None
    source_retention_custody_register_verification_declared_sha256: str | None = None
    source_retention_custody_register_verification_status: str | None = None
    retention_custody_register_verification_artifact_hash_valid: bool = False
    source_retention_custody_register_status: str | None = None
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
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
    def _retention_custody_seal_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodySealVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody seal verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_seal_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_seal_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_seal_artifact_path: str | None = None
    source_retention_custody_seal_declared_sha256: str | None = None
    source_retention_custody_seal_computed_sha256: str | None = None
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    sealed_by: str | None = None
    custody_location: str | None = None
    seal_note: str | None = None
    custody_seal_statement_declared_sha256: str | None = None
    custody_seal_statement_computed_sha256: str | None = None
    custody_seal_statement_hash_valid: bool = False
    source_retention_custody_register_verification_artifact_path: str | None = None
    source_retention_custody_register_verification_declared_sha256: str | None = None
    source_retention_custody_register_verification_status: str | None = None
    retention_custody_register_verification_artifact_hash_valid: bool = False
    source_retention_custody_register_status: str | None = None
    retention_custody_register_artifact_hash_valid: bool = False
    custody_register_id: str | None = None
    custody_register_statement_hash_valid: bool = False
    retention_handoff_acceptance_verification_artifact_hash_valid: bool = False
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    acceptance_statement_hash_valid: bool = False
    retention_handoff_verification_artifact_hash_valid: bool = False
    retention_handoff_artifact_hash_valid: bool = False
    handoff_statement_hash_valid: bool = False
    retention_signoff_verification_artifact_hash_valid: bool = False
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
    "PaperExecutionEvidenceBundleRetentionCustodyRegisterArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyRegisterView",
    "PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodySealArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodySealView",
    "PaperExecutionEvidenceBundleRetentionCustodySealVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodySealVerificationView",
)
