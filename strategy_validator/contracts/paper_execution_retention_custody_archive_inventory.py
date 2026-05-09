"""Paper execution retention custody inventory/reconciliation contract models."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *
from strategy_validator.contracts.paper_execution_evidence_bundle import *
from strategy_validator.contracts.paper_execution_retention import *
from strategy_validator.contracts.paper_execution_retention_custody_chain import *
from strategy_validator.contracts.paper_execution_retention_custody_renewal import *


class PaperExecutionEvidenceBundleRetentionCustodyInventoryArtifact(BaseModel):
    """Read-only inventory record for verified redeposited paper evidence retention custody."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_inventory/v1"] = "paper_execution_evidence_bundle_retention_custody_inventory/v1"
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
    inventory_authority: Literal["READ_ONLY_RETENTION_CUSTODY_INVENTORY"] = "READ_ONLY_RETENTION_CUSTODY_INVENTORY"
    inventory_status: Literal["INVENTORIED", "INVENTORIED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_inventory_id: str | None = None
    inventoried_by: str | None = None
    inventory_reason: str | None = None
    custody_location: str | None = None
    inventoried_at_utc: str | None = None
    inventory_note: str | None = None
    source_retention_custody_redeposit_verification_artifact_path: str | None = None
    source_retention_custody_redeposit_verification_declared_sha256: str | None = None
    source_retention_custody_redeposit_verification_computed_sha256: str | None = None
    source_retention_custody_redeposit_verification_status: str | None = None
    source_retention_custody_redeposit_verification_trust_banner: str | None = None
    retention_custody_redeposit_verification_artifact_hash_valid: bool = False
    source_retention_custody_redeposit_status: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
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
    custody_inventory_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_inventory_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyInventoryView(BaseModel):
    """Read-plane summary of paper evidence retention custody inventory records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_inventory_view/v1"] = "paper_execution_evidence_bundle_retention_custody_inventory_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    inventory_status: Literal["INVENTORIED", "INVENTORIED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_inventory_id: str | None = None
    inventoried_by: str | None = None
    inventory_reason: str | None = None
    custody_location: str | None = None
    inventoried_at_utc: str | None = None
    inventory_note: str | None = None
    source_retention_custody_redeposit_verification_artifact_path: str | None = None
    source_retention_custody_redeposit_verification_status: str | None = None
    retention_custody_redeposit_verification_artifact_hash_valid: bool = False
    source_retention_custody_redeposit_status: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
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
    custody_inventory_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyInventoryVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody inventory records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_inventory_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_inventory_verification/v1"
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
    inventory_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_INVENTORY_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_INVENTORY_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_inventory_artifact_path: str | None = None
    source_retention_custody_inventory_declared_sha256: str | None = None
    source_retention_custody_inventory_computed_sha256: str | None = None
    source_retention_custody_inventory_status: str | None = None
    source_retention_custody_inventory_trust_banner: str | None = None
    retention_custody_inventory_artifact_hash_valid: bool = False
    custody_inventory_id: str | None = None
    inventoried_by: str | None = None
    inventory_reason: str | None = None
    custody_location: str | None = None
    inventoried_at_utc: str | None = None
    inventory_note: str | None = None
    custody_inventory_statement_declared_sha256: str | None = None
    custody_inventory_statement_computed_sha256: str | None = None
    custody_inventory_statement_hash_valid: bool = False
    source_retention_custody_redeposit_verification_artifact_path: str | None = None
    source_retention_custody_redeposit_verification_status: str | None = None
    retention_custody_redeposit_verification_artifact_hash_valid: bool = False
    source_retention_custody_redeposit_status: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
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
    def _retention_custody_inventory_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyInventoryVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody inventory verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_inventory_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_inventory_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_inventory_artifact_path: str | None = None
    source_retention_custody_inventory_status: str | None = None
    retention_custody_inventory_artifact_hash_valid: bool = False
    custody_inventory_id: str | None = None
    inventoried_by: str | None = None
    inventory_reason: str | None = None
    custody_location: str | None = None
    inventoried_at_utc: str | None = None
    custody_inventory_statement_hash_valid: bool = False
    source_retention_custody_redeposit_verification_artifact_path: str | None = None
    source_retention_custody_redeposit_verification_status: str | None = None
    retention_custody_redeposit_verification_artifact_hash_valid: bool = False
    source_retention_custody_redeposit_status: str | None = None
    retention_custody_redeposit_artifact_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
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
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyReconciliationArtifact(BaseModel):
    """Read-only reconciliation record for verified paper evidence retention custody inventory."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_reconciliation/v1"] = "paper_execution_evidence_bundle_retention_custody_reconciliation/v1"
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
    reconciliation_authority: Literal["READ_ONLY_RETENTION_CUSTODY_RECONCILIATION"] = "READ_ONLY_RETENTION_CUSTODY_RECONCILIATION"
    reconciliation_status: Literal["RECONCILED", "RECONCILED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_reconciliation_id: str | None = None
    reconciled_by: str | None = None
    reconciliation_reason: str | None = None
    custody_location: str | None = None
    reconciled_at_utc: str | None = None
    reconciliation_note: str | None = None
    source_retention_custody_inventory_verification_artifact_path: str | None = None
    source_retention_custody_inventory_verification_declared_sha256: str | None = None
    source_retention_custody_inventory_verification_computed_sha256: str | None = None
    source_retention_custody_inventory_verification_status: str | None = None
    source_retention_custody_inventory_verification_trust_banner: str | None = None
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
    custody_reconciliation_statement_sha256: str | None = None
    checklist: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_custody_reconciliation_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyReconciliationView(BaseModel):
    """Read-plane summary of paper evidence retention custody reconciliation records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_reconciliation_view/v1"] = "paper_execution_evidence_bundle_retention_custody_reconciliation_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    reconciliation_status: Literal["RECONCILED", "RECONCILED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    custody_reconciliation_id: str | None = None
    reconciled_by: str | None = None
    reconciliation_reason: str | None = None
    custody_location: str | None = None
    reconciled_at_utc: str | None = None
    reconciliation_note: str | None = None
    source_retention_custody_inventory_verification_artifact_path: str | None = None
    source_retention_custody_inventory_verification_status: str | None = None
    retention_custody_inventory_verification_artifact_hash_valid: bool = False
    source_retention_custody_inventory_status: str | None = None
    retention_custody_inventory_artifact_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_inventory_statement_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
    next_renewal_due_at_utc: str | None = None
    days_until_due: int = 0
    source_retention_index_sha256: str | None = None
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    custody_reconciliation_statement_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRetentionCustodyReconciliationVerificationArtifact(BaseModel):
    """Read-only verifier for paper evidence retention custody reconciliation records."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_reconciliation_verification/v1"] = "paper_execution_evidence_bundle_retention_custody_reconciliation_verification/v1"
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
    reconciliation_verification_authority: Literal["READ_ONLY_RETENTION_CUSTODY_RECONCILIATION_VERIFICATION"] = "READ_ONLY_RETENTION_CUSTODY_RECONCILIATION_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_reconciliation_artifact_path: str | None = None
    source_retention_custody_reconciliation_declared_sha256: str | None = None
    source_retention_custody_reconciliation_computed_sha256: str | None = None
    source_retention_custody_reconciliation_status: str | None = None
    source_retention_custody_reconciliation_trust_banner: str | None = None
    retention_custody_reconciliation_artifact_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    reconciled_by: str | None = None
    reconciliation_reason: str | None = None
    custody_location: str | None = None
    reconciled_at_utc: str | None = None
    reconciliation_note: str | None = None
    custody_reconciliation_statement_declared_sha256: str | None = None
    custody_reconciliation_statement_computed_sha256: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    source_retention_custody_inventory_verification_artifact_path: str | None = None
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
    def _retention_custody_reconciliation_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRetentionCustodyReconciliationVerificationView(BaseModel):
    """Read-plane summary of paper evidence retention custody reconciliation verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_custody_reconciliation_verification_view/v1"] = "paper_execution_evidence_bundle_retention_custody_reconciliation_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_custody_reconciliation_artifact_path: str | None = None
    source_retention_custody_reconciliation_status: str | None = None
    retention_custody_reconciliation_artifact_hash_valid: bool = False
    custody_reconciliation_id: str | None = None
    reconciled_by: str | None = None
    reconciliation_reason: str | None = None
    custody_location: str | None = None
    reconciled_at_utc: str | None = None
    custody_reconciliation_statement_hash_valid: bool = False
    source_retention_custody_inventory_verification_artifact_path: str | None = None
    source_retention_custody_inventory_verification_status: str | None = None
    retention_custody_inventory_verification_artifact_hash_valid: bool = False
    source_retention_custody_inventory_status: str | None = None
    retention_custody_inventory_artifact_hash_valid: bool = False
    custody_inventory_id: str | None = None
    custody_inventory_statement_hash_valid: bool = False
    custody_redeposit_id: str | None = None
    custody_redeposit_statement_hash_valid: bool = False
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
    "PaperExecutionEvidenceBundleRetentionCustodyInventoryArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyInventoryView",
    "PaperExecutionEvidenceBundleRetentionCustodyInventoryVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyInventoryVerificationView",
    "PaperExecutionEvidenceBundleRetentionCustodyReconciliationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyReconciliationView",
    "PaperExecutionEvidenceBundleRetentionCustodyReconciliationVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionCustodyReconciliationVerificationView",
)
