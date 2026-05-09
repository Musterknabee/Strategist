"""Paper execution evidence-bundle export contracts."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *

class PaperExecutionEvidenceBundleExportEntry(BaseModel):
    """Single artifact row in a paper evidence-chain export handoff manifest."""

    schema_version: Literal["paper_execution_evidence_bundle_export_entry/v1"] = "paper_execution_evidence_bundle_export_entry/v1"
    kind: str
    artifact_path: str | None = None
    handoff_name: str
    declared_sha256: str | None = None
    computed_sha256: str | None = None
    file_sha256: str | None = None
    size_bytes: int | None = None
    present: bool = False
    digest_valid: bool = False

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleExportManifestArtifact(BaseModel):
    """Read-only export handoff manifest for a verified paper evidence chain.

    The manifest inventories the closure-verification artifact, closure packet,
    sealed bundle, bundle verification, drift check, attestation, and
    attestation verification. It does not copy files or grant execution,
    promotion, broker, or ledger mutation authority.
    """

    schema_version: Literal["paper_execution_evidence_bundle_export_manifest/v1"] = "paper_execution_evidence_bundle_export_manifest/v1"
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
    export_authority: Literal["READ_ONLY_HANDOFF_MANIFEST"] = "READ_ONLY_HANDOFF_MANIFEST"
    export_status: Literal["READY_FOR_EXPORT", "READY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_closure_verification_artifact_path: str | None = None
    source_closure_verification_artifact_sha256: str | None = None
    source_closure_verification_status: str | None = None
    source_closure_verification_trust_banner: str | None = None
    closure_verification_artifact_hash_valid: bool = False
    source_closure_status: str | None = None
    export_entry_count: int = 0
    export_digest_valid_entry_count: int = 0
    total_size_bytes: int = 0
    export_index_sha256: str | None = None
    entries: list[PaperExecutionEvidenceBundleExportEntry] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _export_manifest_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleExportManifestView(BaseModel):
    """Read-plane summary of a paper evidence-chain export handoff manifest."""

    schema_version: Literal["paper_execution_evidence_bundle_export_manifest_view/v1"] = "paper_execution_evidence_bundle_export_manifest_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    export_status: Literal["READY_FOR_EXPORT", "READY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_closure_verification_artifact_path: str | None = None
    source_closure_verification_artifact_sha256: str | None = None
    source_closure_verification_status: str | None = None
    source_closure_status: str | None = None
    closure_verification_artifact_hash_valid: bool = False
    export_entry_count: int = 0
    export_digest_valid_entry_count: int = 0
    total_size_bytes: int = 0
    export_index_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleExportVerificationEntry(BaseModel):
    """Verification row for one retained export handoff artifact entry."""

    schema_version: Literal["paper_execution_evidence_bundle_export_verification_entry/v1"] = "paper_execution_evidence_bundle_export_verification_entry/v1"
    kind: str
    artifact_path: str | None = None
    handoff_name: str | None = None
    declared_sha256: str | None = None
    manifest_computed_sha256: str | None = None
    recomputed_sha256: str | None = None
    manifest_file_sha256: str | None = None
    recomputed_file_sha256: str | None = None
    manifest_size_bytes: int | None = None
    recomputed_size_bytes: int | None = None
    present: bool = False
    manifest_entry_digest_valid: bool = False
    declared_digest_valid: bool = False
    manifest_computed_digest_valid: bool = False
    file_digest_valid: bool = False
    size_valid: bool = False
    verification_digest_valid: bool = False

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleExportVerificationArtifact(BaseModel):
    """Read-only verification result for a paper evidence-chain export manifest.

    The verifier recomputes the export manifest digest, the export index digest,
    and every retained artifact digest/size declared by the manifest. It never
    copies files and has no trading, promotion, or ledger authority.
    """

    schema_version: Literal["paper_execution_evidence_bundle_export_verification/v1"] = "paper_execution_evidence_bundle_export_verification/v1"
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
    verification_authority: Literal["READ_ONLY"] = "READ_ONLY"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_export_manifest_artifact_path: str | None = None
    source_export_manifest_declared_sha256: str | None = None
    source_export_manifest_computed_sha256: str | None = None
    source_export_manifest_status: str | None = None
    source_export_manifest_trust_banner: str | None = None
    export_manifest_hash_valid: bool = False
    source_export_index_declared_sha256: str | None = None
    source_export_index_computed_sha256: str | None = None
    export_index_hash_valid: bool = False
    source_export_entry_count: int = 0
    source_export_digest_valid_entry_count: int = 0
    recomputed_export_entry_count: int = 0
    recomputed_export_digest_valid_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    entries: list[PaperExecutionEvidenceBundleExportVerificationEntry] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _export_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleExportVerificationView(BaseModel):
    """Read-plane summary of export handoff verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_export_verification_view/v1"] = "paper_execution_evidence_bundle_export_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_export_manifest_artifact_path: str | None = None
    source_export_manifest_declared_sha256: str | None = None
    source_export_manifest_computed_sha256: str | None = None
    source_export_manifest_status: str | None = None
    source_export_manifest_trust_banner: str | None = None
    export_manifest_hash_valid: bool = False
    source_export_index_declared_sha256: str | None = None
    source_export_index_computed_sha256: str | None = None
    export_index_hash_valid: bool = False
    source_export_entry_count: int = 0
    source_export_digest_valid_entry_count: int = 0
    recomputed_export_entry_count: int = 0
    recomputed_export_digest_valid_entry_count: int = 0
    missing_entry_count: int = 0
    digest_mismatch_entry_count: int = 0
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


__all__ = (
    "PaperExecutionEvidenceBundleExportEntry",
    "PaperExecutionEvidenceBundleExportManifestArtifact",
    "PaperExecutionEvidenceBundleExportManifestView",
    "PaperExecutionEvidenceBundleExportVerificationEntry",
    "PaperExecutionEvidenceBundleExportVerificationArtifact",
    "PaperExecutionEvidenceBundleExportVerificationView",
)
