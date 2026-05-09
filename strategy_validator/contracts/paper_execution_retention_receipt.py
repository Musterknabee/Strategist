"""Paper execution evidence-bundle retention receipt and verification contracts."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *
from strategy_validator.contracts.paper_execution_evidence_bundle import *

class PaperExecutionEvidenceBundleRetentionReceiptEntry(BaseModel):
    """Single verified artifact row in a paper evidence-chain retention receipt."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_receipt_entry/v1"] = "paper_execution_evidence_bundle_retention_receipt_entry/v1"
    kind: str
    artifact_path: str | None = None
    handoff_name: str | None = None
    retention_name: str
    declared_sha256: str | None = None
    verified_sha256: str | None = None
    file_sha256: str | None = None
    expected_file_sha256: str | None = None
    size_bytes: int | None = None
    expected_size_bytes: int | None = None
    present: bool = False
    source_verification_digest_valid: bool = False
    file_digest_valid: bool = False
    size_valid: bool = False
    ready_for_retention: bool = False

    model_config = {"extra": "forbid"}

class PaperExecutionEvidenceBundleRetentionReceiptArtifact(BaseModel):
    """Read-only receipt describing the verified export artifacts to retain."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_receipt/v1"] = "paper_execution_evidence_bundle_retention_receipt/v1"
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
    retention_authority: Literal["READ_ONLY_RETENTION_RECEIPT"] = "READ_ONLY_RETENTION_RECEIPT"
    retention_status: Literal["READY_FOR_RETENTION", "READY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_export_verification_artifact_path: str | None = None
    source_export_verification_artifact_sha256: str | None = None
    source_export_verification_computed_sha256: str | None = None
    source_export_verification_status: str | None = None
    source_export_verification_trust_banner: str | None = None
    export_verification_artifact_hash_valid: bool = False
    source_export_manifest_artifact_path: str | None = None
    source_export_manifest_sha256: str | None = None
    source_export_manifest_status: str | None = None
    source_export_index_sha256: str | None = None
    retained_entry_count: int = 0
    retained_ready_entry_count: int = 0
    total_size_bytes: int = 0
    retention_index_sha256: str | None = None
    entries: list[PaperExecutionEvidenceBundleRetentionReceiptEntry] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_receipt_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v

class PaperExecutionEvidenceBundleRetentionReceiptView(BaseModel):
    """Read-plane summary of a paper evidence-chain retention receipt."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_receipt_view/v1"] = "paper_execution_evidence_bundle_retention_receipt_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    retention_status: Literal["READY_FOR_RETENTION", "READY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_export_verification_artifact_path: str | None = None
    source_export_verification_artifact_sha256: str | None = None
    source_export_verification_status: str | None = None
    source_export_manifest_artifact_path: str | None = None
    source_export_manifest_status: str | None = None
    export_verification_artifact_hash_valid: bool = False
    retained_entry_count: int = 0
    retained_ready_entry_count: int = 0
    total_size_bytes: int = 0
    retention_index_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

class PaperExecutionEvidenceBundleRetentionVerificationEntry(BaseModel):
    """Single retained artifact row rechecked from a retention receipt."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_verification_entry/v1"] = "paper_execution_evidence_bundle_retention_verification_entry/v1"
    kind: str
    artifact_path: str | None = None
    retention_name: str | None = None
    receipt_declared_sha256: str | None = None
    receipt_verified_sha256: str | None = None
    receipt_file_sha256: str | None = None
    receipt_expected_file_sha256: str | None = None
    recomputed_file_sha256: str | None = None
    receipt_size_bytes: int | None = None
    receipt_expected_size_bytes: int | None = None
    recomputed_size_bytes: int | None = None
    present: bool = False
    retention_entry_ready: bool = False
    source_verification_digest_valid: bool = False
    file_digest_valid: bool = False
    size_valid: bool = False
    verification_digest_valid: bool = False

    model_config = {"extra": "forbid"}

class PaperExecutionEvidenceBundleRetentionVerificationArtifact(BaseModel):
    """Read-only verifier for a paper evidence-chain retention receipt."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_verification/v1"] = "paper_execution_evidence_bundle_retention_verification/v1"
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
    retention_authority: Literal["READ_ONLY_RETENTION_VERIFICATION"] = "READ_ONLY_RETENTION_VERIFICATION"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_declared_sha256: str | None = None
    source_retention_receipt_computed_sha256: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_receipt_trust_banner: str | None = None
    retention_receipt_hash_valid: bool = False
    source_retention_index_declared_sha256: str | None = None
    source_retention_index_computed_sha256: str | None = None
    retention_index_hash_valid: bool = False
    source_retention_entry_count: int = 0
    source_retention_ready_entry_count: int = 0
    recomputed_retention_entry_count: int = 0
    recomputed_retention_ready_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    entries: list[PaperExecutionEvidenceBundleRetentionVerificationEntry] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _retention_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v

class PaperExecutionEvidenceBundleRetentionVerificationView(BaseModel):
    """Read-plane summary of retention receipt verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_retention_verification_view/v1"] = "paper_execution_evidence_bundle_retention_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_retention_receipt_artifact_path: str | None = None
    source_retention_receipt_declared_sha256: str | None = None
    source_retention_receipt_computed_sha256: str | None = None
    source_retention_receipt_status: str | None = None
    source_retention_receipt_trust_banner: str | None = None
    retention_receipt_hash_valid: bool = False
    source_retention_index_declared_sha256: str | None = None
    source_retention_index_computed_sha256: str | None = None
    retention_index_hash_valid: bool = False
    source_retention_entry_count: int = 0
    source_retention_ready_entry_count: int = 0
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
    "PaperExecutionEvidenceBundleRetentionReceiptEntry",
    "PaperExecutionEvidenceBundleRetentionReceiptArtifact",
    "PaperExecutionEvidenceBundleRetentionReceiptView",
    "PaperExecutionEvidenceBundleRetentionVerificationEntry",
    "PaperExecutionEvidenceBundleRetentionVerificationArtifact",
    "PaperExecutionEvidenceBundleRetentionVerificationView",
)
