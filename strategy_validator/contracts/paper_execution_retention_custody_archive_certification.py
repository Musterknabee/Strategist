"""Paper execution retention custody certification/attestation contract models."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *
from strategy_validator.contracts.paper_execution_evidence_bundle import *
from strategy_validator.contracts.paper_execution_retention import *
from strategy_validator.contracts.paper_execution_retention_custody_chain import *
from strategy_validator.contracts.paper_execution_retention_custody_renewal import *


class PaperExecutionEvidenceBundleRetentionCustodyCertificationArtifact(BaseModel):
    """Read-only certification record for verified paper evidence retention custody reconciliation."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_certification/v1"] = "paper_execution_evidence_bundle_retention_custody_certification/v1"
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
    certification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_CERTIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_CERTIFICATION"
    certification_status: Literal["CERTIFIED", "CERTIFIED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_certification_id: str | None = None
    certified_by: str | None = None
    certification_reason: str | None = None
    custody_location: str | None = None
    certified_at_utc: str | None = None
    certification_note: str | None = None
    source_retention_custody_reconciliation_verification_artifact_path: str | None = None
    source_retention_custody_reconciliation_verification_declared_sha256: str | None = None
    source_retention_custody_reconciliation_verification_computed_sha256: str | None = None
    source_retention_custody_reconciliation_verification_status: str | None = None
    source_retention_custody_reconciliation_verification_trust_banner: str | None = None
    retention_custody_reconciliation_verification_artifact_hash_valid: bool = False
    source_retention_custody_reconciliation_status: str | None = None
    retention_custody_reconciliation_artifact_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    source_retention_custody_inventory_verification_status: str | None = None
    retention_custody_inventory_verification_artifact_hash_valid: bool = False
    source_retention_custody_inventory_status: str | None = None
    retention_custody_inventory_artifact_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_inventory_statement_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
    source_retention_custody_redeposit_verification_status: str | None = None
    retention_custody_redeposit_verification_artifact_hash_valid: bool = False
    source_retention_custody_redeposit_status: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
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
    custody_certification_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_certification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyCertificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody certification records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_certification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_certification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    certification_status: Literal["CERTIFIED", "CERTIFIED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_certification_id: str | None = None
    certified_by: str | None = None
    certification_reason: str | None = None
    custody_location: str | None = None
    certified_at_utc: str | None = None
    certification_note: str | None = None
    source_retention_custody_reconciliation_verification_artifact_path: str | None = None
    source_retention_custody_reconciliation_verification_status: str | None = None
    retention_custody_reconciliation_verification_artifact_hash_valid: bool = False
    source_retention_custody_reconciliation_status: str | None = None
    retention_custody_reconciliation_artifact_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_redeposit_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_certification_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyCertificationVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody certification records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_certification_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_certification_verification/v1"
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
    certification_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_CERTIFICATION_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_CERTIFICATION_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_certification_artifact_path: str | None = None
    source_retention_custody_certification_declared_sha256: str | None = None
    source_retention_custody_certification_computed_sha256: str | None = None
    source_retention_custody_certification_status: str | None = None
    source_retention_custody_certification_trust_banner: str | None = None
    retention_custody_certification_artifact_hash_valid: bool = False
    custody_certification_id: str | None = None
    certified_by: str | None = None
    certification_reason: str | None = None
    custody_location: str | None = None
    certified_at_utc: str | None = None
    certification_note: str | None = None
    custody_certification_statement_declared_sha256: str | None = None
    custody_certification_statement_computed_sha256: str | None = None
    custody_certification_statement_hash_valid: bool = False
    source_retention_custody_reconciliation_verification_artifact_path: str | None = None
    source_retention_custody_reconciliation_verification_status: str | None = None
    retention_custody_reconciliation_verification_artifact_hash_valid: bool = False
    source_retention_custody_reconciliation_status: str | None = None
    retention_custody_reconciliation_artifact_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    source_retention_custody_inventory_verification_status: str | None = None
    retention_custody_inventory_verification_artifact_hash_valid: bool = False
    source_retention_custody_inventory_status: str | None = None
    retention_custody_inventory_artifact_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_inventory_statement_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
    source_retention_custody_redeposit_verification_status: str | None = None
    retention_custody_redeposit_verification_artifact_hash_valid: bool = False
    source_retention_custody_redeposit_status: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_return_id: str | None = None
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
    def _retention_custody_certification_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyCertificationVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody certification verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_certification_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_certification_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_certification_artifact_path: str | None = None
    source_retention_custody_certification_status: str | None = None
    retention_custody_certification_artifact_hash_valid: bool = False
    custody_certification_id: str | None = None
    certified_by: str | None = None
    certification_reason: str | None = None
    custody_location: str | None = None
    certified_at_utc: str | None = None
    custody_certification_statement_hash_valid: bool = False
    source_retention_custody_reconciliation_verification_artifact_path: str | None = None
    source_retention_custody_reconciliation_verification_status: str | None = None
    retention_custody_reconciliation_verification_artifact_hash_valid: bool = False
    source_retention_custody_reconciliation_status: str | None = None
    retention_custody_reconciliation_artifact_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_redeposit_id: str | None = None
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


class PaperExecutionEvidenceBundleRetentionCustodyAttestationArtifact(BaseModel):
    """Read-only attestation record for verified certified paper evidence retention custody."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_attestation/v1"] = "paper_execution_evidence_bundle_retention_custody_attestation/v1"
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
    attestation_authority: Literal["READ_ONLY_RETENTION_CUSTODY_ATTESTATION"] = "READ_ONLY_RETENTION_CUSTODY_ATTESTATION"
    attestation_status: Literal["ATTESTED", "ATTESTED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_attestation_id: str | None = None
    attested_by: str | None = None
    attestation_reason: str | None = None
    attestation_scope: str | None = None
    attested_at_utc: str | None = None
    attestation_note: str | None = None
    source_retention_custody_certification_verification_artifact_path: str | None = None
    source_retention_custody_certification_verification_declared_sha256: str | None = None
    source_retention_custody_certification_verification_computed_sha256: str | None = None
    source_retention_custody_certification_verification_status: str | None = None
    source_retention_custody_certification_verification_trust_banner: str | None = None
    retention_custody_certification_verification_artifact_hash_valid: bool = False
    source_retention_custody_certification_status: str | None = None
    retention_custody_certification_artifact_hash_valid: bool = False
    custody_certification_id: str | None = None
    custody_certification_statement_hash_valid: bool = False
    source_retention_custody_reconciliation_verification_status: str | None = None
    retention_custody_reconciliation_verification_artifact_hash_valid: bool = False
    source_retention_custody_reconciliation_status: str | None = None
    retention_custody_reconciliation_artifact_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_redeposit_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_attestation_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_attestation_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyAttestationView(BaseModel):
    """Read-plane summary of paper evidence retention custody attestation records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_attestation_view/v1"] = "paper_execution_evidence_bundle_retention_custody_attestation_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    attestation_status: Literal["ATTESTED", "ATTESTED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_attestation_id: str | None = None
    attested_by: str | None = None
    attestation_reason: str | None = None
    attestation_scope: str | None = None
    attested_at_utc: str | None = None
    attestation_note: str | None = None
    source_retention_custody_certification_verification_artifact_path: str | None = None
    source_retention_custody_certification_verification_status: str | None = None
    retention_custody_certification_verification_artifact_hash_valid: bool = False
    source_retention_custody_certification_status: str | None = None
    retention_custody_certification_artifact_hash_valid: bool = False
    custody_certification_id: str | None = None
    custody_certification_statement_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_redeposit_id: str | None = None
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_attestation_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody attestation records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_attestation_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_attestation_verification/v1"
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
    attestation_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_ATTESTATION_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_ATTESTATION_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_attestation_artifact_path: str | None = None
    source_retention_custody_attestation_declared_sha256: str | None = None
    source_retention_custody_attestation_computed_sha256: str | None = None
    source_retention_custody_attestation_status: str | None = None
    source_retention_custody_attestation_trust_banner: str | None = None
    retention_custody_attestation_artifact_hash_valid: bool = False
    custody_attestation_id: str | None = None
    attested_by: str | None = None
    attestation_reason: str | None = None
    attestation_scope: str | None = None
    attested_at_utc: str | None = None
    attestation_note: str | None = None
    custody_attestation_statement_declared_sha256: str | None = None
    custody_attestation_statement_computed_sha256: str | None = None
    custody_attestation_statement_hash_valid: bool = False
    source_retention_custody_certification_verification_artifact_path: str | None = None
    source_retention_custody_certification_verification_status: str | None = None
    retention_custody_certification_verification_artifact_hash_valid: bool = False
    source_retention_custody_certification_status: str | None = None
    retention_custody_certification_artifact_hash_valid: bool = False
    custody_certification_id: str | None = None
    custody_certification_statement_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_redeposit_id: str | None = None
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
    def _retention_custody_attestation_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody attestation verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_attestation_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_attestation_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_attestation_artifact_path: str | None = None
    source_retention_custody_attestation_status: str | None = None
    retention_custody_attestation_artifact_hash_valid: bool = False
    custody_attestation_id: str | None = None
    attested_by: str | None = None
    attestation_reason: str | None = None
    attestation_scope: str | None = None
    attested_at_utc: str | None = None
    custody_attestation_statement_hash_valid: bool = False
    source_retention_custody_certification_verification_artifact_path: str | None = None
    source_retention_custody_certification_verification_status: str | None = None
    retention_custody_certification_verification_artifact_hash_valid: bool = False
    source_retention_custody_certification_status: str | None = None
    retention_custody_certification_artifact_hash_valid: bool = False
    custody_certification_id: str | None = None
    custody_certification_statement_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_redeposit_id: str | None = None
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
    "PaperExecutionEvidenceBundleRetentionCustodyCertificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyCertificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyCertificationVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyCertificationVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyAttestationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyAttestationView",
    "PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyAttestationVerificationView",
)
