"""Paper execution retention custody audit/continuity contract models."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *
from strategy_validator.contracts.paper_execution_evidence_bundle import *
from strategy_validator.contracts.paper_execution_retention import *


class PaperExecutionEvidenceBundleRetentionCustodyAuditArtifact(BaseModel):
    """Read-only custody audit certificate for verified paper evidence retention custody."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_audit/v1"] = "paper_execution_evidence_bundle_retention_custody_audit/v1"
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
    audit_authority: Literal["READ_ONLY_RETENTION_CUSTODY_AUDIT"] = "READ_ONLY_RETENTION_CUSTODY_AUDIT"
    audit_status: Literal["AUDITED", "AUDITED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_audit_id: str | None = None
    audited_by: str | None = None
    custody_location: str | None = None
    audit_note: str | None = None
    source_retention_custody_seal_verification_artifact_path: str | None = None
    source_retention_custody_seal_verification_declared_sha256: str | None = None
    source_retention_custody_seal_verification_computed_sha256: str | None = None
    source_retention_custody_seal_verification_status: str | None = None
    source_retention_custody_seal_verification_trust_banner: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_artifact_path: str | None = None
    source_retention_custody_seal_status: str | None = None
    source_retention_custody_seal_trust_banner: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    source_retention_custody_register_verification_artifact_path: str | None = None
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
    custody_audit_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_audit_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyAuditView(BaseModel):
    """Read-plane summary of paper evidence retention custody audits."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_audit_view/v1"] = "paper_execution_evidence_bundle_retention_custody_audit_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    audit_status: Literal["AUDITED", "AUDITED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_audit_id: str | None = None
    audited_by: str | None = None
    custody_location: str | None = None
    audit_note: str | None = None
    source_retention_custody_seal_verification_artifact_path: str | None = None
    source_retention_custody_seal_verification_declared_sha256: str | None = None
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
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
    custody_audit_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyAuditVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody audits."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_audit_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_audit_verification/v1"
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
    audit_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_AUDIT_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_AUDIT_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_audit_artifact_path: str | None = None
    source_retention_custody_audit_declared_sha256: str | None = None
    source_retention_custody_audit_computed_sha256: str | None = None
    source_retention_custody_audit_status: str | None = None
    source_retention_custody_audit_trust_banner: str | None = None
    retention_custody_audit_artifact_hash_valid: bool = False
    custody_audit_id: str | None = None
    audited_by: str | None = None
    custody_location: str | None = None
    audit_note: str | None = None
    custody_audit_statement_declared_sha256: str | None = None
    custody_audit_statement_computed_sha256: str | None = None
    custody_audit_statement_hash_valid: bool = False
    source_retention_custody_seal_verification_artifact_path: str | None = None
    source_retention_custody_seal_verification_declared_sha256: str | None = None
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
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
    def _retention_custody_audit_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyAuditVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody audit verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_audit_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_audit_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_audit_artifact_path: str | None = None
    source_retention_custody_audit_declared_sha256: str | None = None
    source_retention_custody_audit_status: str | None = None
    retention_custody_audit_artifact_hash_valid: bool = False
    custody_audit_id: str | None = None
    audited_by: str | None = None
    custody_location: str | None = None
    audit_note: str | None = None
    custody_audit_statement_declared_sha256: str | None = None
    custody_audit_statement_computed_sha256: str | None = None
    custody_audit_statement_hash_valid: bool = False
    source_retention_custody_seal_verification_artifact_path: str | None = None
    source_retention_custody_seal_verification_declared_sha256: str | None = None
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
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


class PaperExecutionEvidenceBundleRetentionCustodyContinuityArtifact(BaseModel):
    """Read-only continuity attestation for verified paper evidence retention custody."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_continuity/v1"] = "paper_execution_evidence_bundle_retention_custody_continuity/v1"
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
    continuity_authority: Literal["READ_ONLY_RETENTION_CUSTODY_CONTINUITY"] = "READ_ONLY_RETENTION_CUSTODY_CONTINUITY"
    continuity_status: Literal["CONTINUITY_ATTESTED", "CONTINUITY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_continuity_id: str | None = None
    attested_by: str | None = None
    custody_location: str | None = None
    continuity_note: str | None = None
    source_retention_custody_audit_verification_artifact_path: str | None = None
    source_retention_custody_audit_verification_declared_sha256: str | None = None
    source_retention_custody_audit_verification_computed_sha256: str | None = None
    source_retention_custody_audit_verification_status: str | None = None
    source_retention_custody_audit_verification_trust_banner: str | None = None
    retention_custody_audit_verification_artifact_hash_valid: bool = False
    source_retention_custody_audit_artifact_path: str | None = None
    source_retention_custody_audit_status: str | None = None
    retention_custody_audit_artifact_hash_valid: bool = False
    custody_audit_id: str | None = None
    custody_audit_statement_hash_valid: bool = False
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
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
    custody_continuity_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_continuity_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyContinuityView(BaseModel):
    """Read-plane summary of paper evidence retention custody continuity attestations."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_continuity_view/v1"] = "paper_execution_evidence_bundle_retention_custody_continuity_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    continuity_status: Literal["CONTINUITY_ATTESTED", "CONTINUITY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_continuity_id: str | None = None
    attested_by: str | None = None
    custody_location: str | None = None
    continuity_note: str | None = None
    source_retention_custody_audit_verification_artifact_path: str | None = None
    source_retention_custody_audit_verification_declared_sha256: str | None = None
    source_retention_custody_audit_verification_status: str | None = None
    retention_custody_audit_verification_artifact_hash_valid: bool = False
    source_retention_custody_audit_status: str | None = None
    retention_custody_audit_artifact_hash_valid: bool = False
    custody_audit_id: str | None = None
    custody_audit_statement_hash_valid: bool = False
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
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
    custody_continuity_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody continuity attestations."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_continuity_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_continuity_verification/v1"
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
    continuity_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_CONTINUITY_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_CONTINUITY_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_continuity_artifact_path: str | None = None
    source_retention_custody_continuity_declared_sha256: str | None = None
    source_retention_custody_continuity_computed_sha256: str | None = None
    source_retention_custody_continuity_status: str | None = None
    source_retention_custody_continuity_trust_banner: str | None = None
    retention_custody_continuity_artifact_hash_valid: bool = False
    custody_continuity_id: str | None = None
    attested_by: str | None = None
    custody_location: str | None = None
    continuity_note: str | None = None
    custody_continuity_statement_declared_sha256: str | None = None
    custody_continuity_statement_computed_sha256: str | None = None
    custody_continuity_statement_hash_valid: bool = False
    source_retention_custody_audit_verification_artifact_path: str | None = None
    source_retention_custody_audit_verification_declared_sha256: str | None = None
    source_retention_custody_audit_verification_status: str | None = None
    retention_custody_audit_verification_artifact_hash_valid: bool = False
    source_retention_custody_audit_status: str | None = None
    retention_custody_audit_artifact_hash_valid: bool = False
    custody_audit_id: str | None = None
    custody_audit_statement_hash_valid: bool = False
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
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
    def _retention_custody_continuity_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody continuity verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_continuity_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_continuity_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_continuity_artifact_path: str | None = None
    source_retention_custody_continuity_declared_sha256: str | None = None
    source_retention_custody_continuity_status: str | None = None
    retention_custody_continuity_artifact_hash_valid: bool = False
    custody_continuity_id: str | None = None
    attested_by: str | None = None
    custody_location: str | None = None
    continuity_note: str | None = None
    custody_continuity_statement_declared_sha256: str | None = None
    custody_continuity_statement_computed_sha256: str | None = None
    custody_continuity_statement_hash_valid: bool = False
    source_retention_custody_audit_verification_artifact_path: str | None = None
    source_retention_custody_audit_verification_declared_sha256: str | None = None
    source_retention_custody_audit_verification_status: str | None = None
    retention_custody_audit_verification_artifact_hash_valid: bool = False
    source_retention_custody_audit_status: str | None = None
    retention_custody_audit_artifact_hash_valid: bool = False
    custody_audit_id: str | None = None
    custody_audit_statement_hash_valid: bool = False
    source_retention_custody_seal_verification_status: str | None = None
    retention_custody_seal_verification_artifact_hash_valid: bool = False
    source_retention_custody_seal_status: str | None = None
    retention_custody_seal_artifact_hash_valid: bool = False
    custody_seal_id: str | None = None
    custody_seal_statement_hash_valid: bool = False
    retention_custody_register_verification_artifact_hash_valid: bool = False
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
    "PaperExecutionEvidenceBundleRetentionCustodyAuditArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyAuditView",
    "PaperExecutionEvidenceBundleRetentionCustodyAuditVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyAuditVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyContinuityArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyContinuityView",
    "PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyContinuityVerificationView",
)
