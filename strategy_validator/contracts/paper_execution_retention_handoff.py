"""Paper execution evidence-bundle retention handoff, acceptance, and verification contracts."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *
from strategy_validator.contracts.paper_execution_evidence_bundle import *

class PaperExecutionEvidenceBundleRetentionHandoffArtifact(BaseModel):
    """Read-only custody handoff capsule for verified paper evidence retention."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_handoff/v1"] = "paper_execution_evidence_bundle_retention_handoff/v1"
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
    handoff_authority: Literal["READ_ONLY_RETENTION_HANDOFF"] = "READ_ONLY_RETENTION_HANDOFF"
    handoff_status: Literal["READY_FOR_HANDOFF", "READY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custodian_id: str | None = None
    handoff_note: str | None = None
    source_retention_signoff_verification_artifact_path: str | None = None
    source_retention_signoff_verification_declared_sha256: str | None = None
    source_retention_signoff_verification_computed_sha256: str | None = None
    source_retention_signoff_verification_status: str | None = None
    source_retention_signoff_verification_trust_banner: str | None = None
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_signoff_artifact_path: str | None = None
    source_retention_signoff_status: str | None = None
    source_retention_signoff_trust_banner: str | None = None
    retention_signoff_artifact_hash_valid: bool = False
    signoff_statement_hash_valid: bool = False
    source_retention_verification_artifact_path: str | None = None
    source_retention_verification_status: str | None = None
    retention_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    handoff_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_handoff_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v

class PaperExecutionEvidenceBundleRetentionHandoffView(BaseModel):
    """Read-plane summary of paper evidence retention handoff capsules."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_handoff_view/v1"] = "paper_execution_evidence_bundle_retention_handoff_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    handoff_status: Literal["READY_FOR_HANDOFF", "READY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custodian_id: str | None = None
    handoff_note: str | None = None
    source_retention_signoff_verification_artifact_path: str | None = None
    source_retention_signoff_verification_declared_sha256: str | None = None
    source_retention_signoff_verification_status: str | None = None
    source_retention_signoff_verification_trust_banner: str | None = None
    retention_signoff_verification_artifact_hash_valid: bool = False
    source_retention_signoff_artifact_path: str | None = None
    source_retention_signoff_status: str | None = None
    source_retention_signoff_trust_banner: str | None = None
    retention_signoff_artifact_hash_valid: bool = False
    signoff_statement_hash_valid: bool = False
    source_retention_verification_artifact_path: str | None = None
    source_retention_verification_status: str | None = None
    retention_verification_artifact_hash_valid: bool = False
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    handoff_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

class PaperExecutionEvidenceBundleRetentionHandoffVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention handoff capsules."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_handoff_verification/v1"] = "paper_execution_evidence_bundle_retention_handoff_verification/v1"
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
    handoff_verification_authority: Literal["READ_ONLY_RETENTION_HANDOFF_VERIFICATION"] = "READ_ONLY_RETENTION_HANDOFF_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_handoff_artifact_path: str | None = None
    source_retention_handoff_declared_sha256: str | None = None
    source_retention_handoff_computed_sha256: str | None = None
    source_retention_handoff_status: str | None = None
    source_retention_handoff_trust_banner: str | None = None
    retention_handoff_artifact_hash_valid: bool = False
    custodian_id: str | None = None
    handoff_note: str | None = None
    handoff_statement_declared_sha256: str | None = None
    handoff_statement_computed_sha256: str | None = None
    handoff_statement_hash_valid: bool = False
    source_retention_signoff_verification_artifact_path: str | None = None
    source_retention_signoff_verification_declared_sha256: str | None = None
    source_retention_signoff_verification_computed_sha256: str | None = None
    source_retention_signoff_verification_recomputed_sha256: str | None = None
    source_retention_signoff_verification_status: str | None = None
    source_retention_signoff_verification_trust_banner: str | None = None
    retention_signoff_verification_artifact_hash_valid: bool = False
    retention_signoff_artifact_hash_valid: bool = False
    signoff_statement_hash_valid: bool = False
    retention_verification_artifact_hash_valid: bool = False
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
    def _retention_handoff_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v

class PaperExecutionEvidenceBundleRetentionHandoffVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention handoff verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_handoff_verification_view/v1"] = "paper_execution_evidence_bundle_retention_handoff_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_handoff_artifact_path: str | None = None
    source_retention_handoff_declared_sha256: str | None = None
    source_retention_handoff_computed_sha256: str | None = None
    source_retention_handoff_status: str | None = None
    source_retention_handoff_trust_banner: str | None = None
    retention_handoff_artifact_hash_valid: bool = False
    custodian_id: str | None = None
    handoff_note: str | None = None
    handoff_statement_declared_sha256: str | None = None
    handoff_statement_computed_sha256: str | None = None
    handoff_statement_hash_valid: bool = False
    source_retention_signoff_verification_artifact_path: str | None = None
    source_retention_signoff_verification_declared_sha256: str | None = None
    source_retention_signoff_verification_status: str | None = None
    source_retention_signoff_verification_trust_banner: str | None = None
    retention_signoff_verification_artifact_hash_valid: bool = False
    retention_signoff_artifact_hash_valid: bool = False
    signoff_statement_hash_valid: bool = False
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

class PaperExecutionEvidenceBundleRetentionHandoffAcceptanceArtifact(BaseModel):
    """Read-only custodian acceptance certificate for paper evidence retention handoff."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_handoff_acceptance/v1"] = "paper_execution_evidence_bundle_retention_handoff_acceptance/v1"
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
    acceptance_authority: Literal["READ_ONLY_RETENTION_HANDOFF_ACCEPTANCE"] = "READ_ONLY_RETENTION_HANDOFF_ACCEPTANCE"
    acceptance_status: Literal["ACCEPTED_FOR_CUSTODY", "ACCEPTED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    accepting_custodian_id: str | None = None
    custody_location: str | None = None
    acceptance_note: str | None = None
    source_retention_handoff_verification_artifact_path: str | None = None
    source_retention_handoff_verification_declared_sha256: str | None = None
    source_retention_handoff_verification_computed_sha256: str | None = None
    source_retention_handoff_verification_status: str | None = None
    source_retention_handoff_verification_trust_banner: str | None = None
    retention_handoff_verification_artifact_hash_valid: bool = False
    source_retention_handoff_artifact_path: str | None = None
    source_retention_handoff_status: str | None = None
    source_retention_handoff_trust_banner: str | None = None
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
    acceptance_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_handoff_acceptance_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v

class PaperExecutionEvidenceBundleRetentionHandoffAcceptanceView(BaseModel):
    """Read-plane summary of paper evidence retention handoff acceptance certificates."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_handoff_acceptance_view/v1"] = "paper_execution_evidence_bundle_retention_handoff_acceptance_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    acceptance_status: Literal["ACCEPTED_FOR_CUSTODY", "ACCEPTED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    accepting_custodian_id: str | None = None
    custody_location: str | None = None
    acceptance_note: str | None = None
    source_retention_handoff_verification_artifact_path: str | None = None
    source_retention_handoff_verification_declared_sha256: str | None = None
    source_retention_handoff_verification_status: str | None = None
    source_retention_handoff_verification_trust_banner: str | None = None
    retention_handoff_verification_artifact_hash_valid: bool = False
    source_retention_handoff_artifact_path: str | None = None
    source_retention_handoff_status: str | None = None
    source_retention_handoff_trust_banner: str | None = None
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
    acceptance_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}

class PaperExecutionEvidenceBundleRetentionHandoffAcceptanceVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention handoff acceptance certificates."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_handoff_acceptance_verification/v1"] = "paper_execution_evidence_bundle_retention_handoff_acceptance_verification/v1"
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
    acceptance_verification_authority: Literal["READ_ONLY_RETENTION_HANDOFF_ACCEPTANCE_VERIFICATION"] = "READ_ONLY_RETENTION_HANDOFF_ACCEPTANCE_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_handoff_acceptance_artifact_path: str | None = None
    source_retention_handoff_acceptance_declared_sha256: str | None = None
    source_retention_handoff_acceptance_computed_sha256: str | None = None
    source_retention_handoff_acceptance_status: str | None = None
    source_retention_handoff_acceptance_trust_banner: str | None = None
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    accepting_custodian_id: str | None = None
    custody_location: str | None = None
    acceptance_note: str | None = None
    acceptance_statement_declared_sha256: str | None = None
    acceptance_statement_computed_sha256: str | None = None
    acceptance_statement_hash_valid: bool = False
    source_retention_handoff_verification_artifact_path: str | None = None
    source_retention_handoff_verification_declared_sha256: str | None = None
    source_retention_handoff_verification_computed_sha256: str | None = None
    source_retention_handoff_verification_recomputed_sha256: str | None = None
    source_retention_handoff_verification_status: str | None = None
    source_retention_handoff_verification_trust_banner: str | None = None
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
    def _retention_handoff_acceptance_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v

class PaperExecutionEvidenceBundleRetentionHandoffAcceptanceVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention handoff acceptance verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_handoff_acceptance_verification_view/v1"] = "paper_execution_evidence_bundle_retention_handoff_acceptance_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_handoff_acceptance_artifact_path: str | None = None
    source_retention_handoff_acceptance_declared_sha256: str | None = None
    source_retention_handoff_acceptance_computed_sha256: str | None = None
    source_retention_handoff_acceptance_status: str | None = None
    source_retention_handoff_acceptance_trust_banner: str | None = None
    retention_handoff_acceptance_artifact_hash_valid: bool = False
    accepting_custodian_id: str | None = None
    custody_location: str | None = None
    acceptance_note: str | None = None
    acceptance_statement_declared_sha256: str | None = None
    acceptance_statement_computed_sha256: str | None = None
    acceptance_statement_hash_valid: bool = False
    source_retention_handoff_verification_artifact_path: str | None = None
    source_retention_handoff_verification_declared_sha256: str | None = None
    source_retention_handoff_verification_status: str | None = None
    source_retention_handoff_verification_trust_banner: str | None = None
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
    "PaperExecutionEvidenceBundleRetentionHandoffArtifact",
    "PaperExecutionEvidenceBundleRetentionHandoffView",
    "PaperExecutionEvidenceBundleRetentionHandoffVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionHandoffVerificationView",
    "PaperExecutionEvidenceBundleRetentionHandoffAcceptanceArtifact",
    "PaperExecutionEvidenceBundleRetentionHandoffAcceptanceView",
    "PaperExecutionEvidenceBundleRetentionHandoffAcceptanceVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionHandoffAcceptanceVerificationView",
)
