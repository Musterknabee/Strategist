"""Paper execution evidence-bundle verification contracts."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *
from strategy_validator.contracts.paper_execution_evidence_bundle_core import *

class PaperExecutionEvidenceBundleVerificationSource(BaseModel):
    """Per-source digest verification row for a sealed evidence bundle."""

    schema_version: Literal["paper_execution_evidence_bundle_verification_source/v1"] = "paper_execution_evidence_bundle_verification_source/v1"
    stage: str
    tracking_id: str | None = None
    artifact_path: str | None = None
    declared_sha256: str | None = None
    computed_sha256: str | None = None
    verified: bool = False
    issue: str | None = None

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleVerificationArtifact(BaseModel):
    """Durable verification result for a paper execution evidence bundle.

    Verification is read-only: it recomputes bundle/source digests and records
    whether the sealed bundle still matches the artifacts it claims to seal.
    """

    schema_version: Literal["paper_execution_evidence_bundle_verification/v1"] = "paper_execution_evidence_bundle_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    verification_authority: Literal["CLI_EVIDENCE_ONLY"] = "CLI_EVIDENCE_ONLY"
    verification_status: Literal["PASS", "FAIL"] = "FAIL"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "UNTRUSTED"
    source_bundle_artifact_path: str
    source_bundle_declared_sha256: str | None = None
    source_bundle_computed_sha256: str | None = None
    bundle_hash_valid: bool = False
    timeline_source_link_valid: bool = False
    source_artifact_count: int = 0
    verified_source_artifact_count: int = 0
    missing_source_artifact_count: int = 0
    mismatched_source_artifact_count: int = 0
    source_verifications: list[PaperExecutionEvidenceBundleVerificationSource] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleVerificationView(BaseModel):
    """Read-plane summary of a paper evidence bundle verification artifact."""

    schema_version: Literal["paper_execution_evidence_bundle_verification_view/v1"] = "paper_execution_evidence_bundle_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "UNTRUSTED"
    source_bundle_artifact_path: str | None = None
    source_bundle_declared_sha256: str | None = None
    source_bundle_computed_sha256: str | None = None
    bundle_hash_valid: bool = False
    timeline_source_link_valid: bool = False
    source_artifact_count: int = 0
    verified_source_artifact_count: int = 0
    missing_source_artifact_count: int = 0
    mismatched_source_artifact_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleDriftArtifact(BaseModel):
    """Durable drift check for a sealed paper execution evidence bundle.

    A bundle can verify cryptographically while still being stale relative to
    newer paper execution timeline artifacts. This artifact records whether the
    current timeline source set still matches the latest sealed bundle.
    """

    schema_version: Literal["paper_execution_evidence_bundle_drift/v1"] = "paper_execution_evidence_bundle_drift/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    drift_check_authority: Literal["CLI_EVIDENCE_ONLY"] = "CLI_EVIDENCE_ONLY"
    drift_status: Literal["IN_SYNC", "DRIFTED", "NO_BUNDLE", "NO_TIMELINE", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_bundle_artifact_path: str | None = None
    source_bundle_sha256: str | None = None
    source_bundle_generated_at_utc: str | None = None
    current_timeline_sequence_status: str | None = None
    current_timeline_event_count: int = 0
    bundled_timeline_event_count: int = 0
    current_source_artifact_count: int = 0
    bundled_source_artifact_count: int = 0
    current_timeline_fingerprint: str | None = None
    bundled_timeline_fingerprint: str | None = None
    new_source_artifacts: list[str] = Field(default_factory=list)
    removed_source_artifacts: list[str] = Field(default_factory=list)
    changed_stage_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _drift_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleDriftView(BaseModel):
    """Read-plane summary of a paper evidence bundle drift artifact."""

    schema_version: Literal["paper_execution_evidence_bundle_drift_view/v1"] = "paper_execution_evidence_bundle_drift_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    drift_status: Literal["IN_SYNC", "DRIFTED", "NO_BUNDLE", "NO_TIMELINE", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_bundle_artifact_path: str | None = None
    source_bundle_sha256: str | None = None
    source_bundle_generated_at_utc: str | None = None
    current_timeline_sequence_status: str | None = None
    current_timeline_event_count: int = 0
    bundled_timeline_event_count: int = 0
    current_source_artifact_count: int = 0
    bundled_source_artifact_count: int = 0
    current_timeline_fingerprint: str | None = None
    bundled_timeline_fingerprint: str | None = None
    new_source_artifact_count: int = 0
    removed_source_artifact_count: int = 0
    changed_stage_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


__all__ = (
    "PaperExecutionEvidenceBundleVerificationSource",
    "PaperExecutionEvidenceBundleVerificationArtifact",
    "PaperExecutionEvidenceBundleVerificationView",
    "PaperExecutionEvidenceBundleDriftArtifact",
    "PaperExecutionEvidenceBundleDriftView",
)
