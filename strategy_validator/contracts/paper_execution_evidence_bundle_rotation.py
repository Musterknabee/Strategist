"""Paper execution evidence-bundle rotation contracts."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *

class PaperExecutionEvidenceBundleRotationArtifact(BaseModel):
    """Durable operator recommendation for evidence-bundle rotation.

    Rotation is a recovery workflow recommendation only. It never submits orders
    and never mutates the adjudication ledger. It records whether the current
    paper execution evidence should be re-sealed, re-verified, and rechecked for
    drift after timeline/source changes.
    """

    schema_version: Literal["paper_execution_evidence_bundle_rotation/v1"] = "paper_execution_evidence_bundle_rotation/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    rotation_authority: Literal["CLI_RECOMMENDATION_ONLY"] = "CLI_RECOMMENDATION_ONLY"
    rotation_status: Literal["NOT_NEEDED", "RECOMMENDED", "REQUIRED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_bundle_sha256: str | None = None
    source_bundle_status: str | None = None
    source_bundle_trust_banner: str | None = None
    source_verification_status: str | None = None
    source_verification_trust_banner: str | None = None
    source_drift_status: str | None = None
    source_drift_trust_banner: str | None = None
    timeline_sequence_status: str | None = None
    timeline_event_count: int = 0
    rotation_reason_codes: list[str] = Field(default_factory=list)
    recommended_operator_sequence: list[str] = Field(default_factory=list)
    one_command_sequence_hint: str | None = None
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _rotation_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRotationView(BaseModel):
    """Read-plane summary of a paper evidence-bundle rotation recommendation."""

    schema_version: Literal["paper_execution_evidence_bundle_rotation_view/v1"] = "paper_execution_evidence_bundle_rotation_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    rotation_status: Literal["NOT_NEEDED", "RECOMMENDED", "REQUIRED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_bundle_sha256: str | None = None
    source_bundle_status: str | None = None
    source_verification_status: str | None = None
    source_drift_status: str | None = None
    timeline_sequence_status: str | None = None
    timeline_event_count: int = 0
    rotation_reason_codes: list[str] = Field(default_factory=list)
    recommended_operator_sequence: list[str] = Field(default_factory=list)
    one_command_sequence_hint: str | None = None
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRotationExecutionStep(BaseModel):
    """Single audited step in the bundle-rotation recovery workflow."""

    schema_version: Literal["paper_execution_evidence_bundle_rotation_execution_step/v1"] = "paper_execution_evidence_bundle_rotation_execution_step/v1"
    step_name: Literal["SEAL", "VERIFY", "DRIFT_CHECK", "SKIP", "BLOCK"]
    status: Literal["PASS", "FAIL", "SKIPPED", "BLOCKED"]
    artifact_path: str | None = None
    history_artifact_path: str | None = None
    artifact_sha256: str | None = None
    output_status: str | None = None
    trust_banner: str | None = None
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleRotationExecutionArtifact(BaseModel):
    """Durable manifest for executing the bundle-rotation recovery sequence.

    This is a CLI-only local evidence workflow. It may seal/verify/drift-check
    paper execution evidence artifacts, but it never submits orders, calls broker
    mutation endpoints, promotes strategies, or mutates the adjudication ledger.
    """

    schema_version: Literal["paper_execution_evidence_bundle_rotation_execution/v1"] = "paper_execution_evidence_bundle_rotation_execution/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    rotation_execution_authority: Literal["CLI_WORKFLOW_ONLY"] = "CLI_WORKFLOW_ONLY"
    rotation_execution_status: Literal["PASS", "FAILED", "BLOCKED", "SKIPPED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_recommendation_artifact_path: str | None = None
    source_recommendation_artifact_sha256: str | None = None
    source_recommendation_status: str | None = None
    source_recommendation_trust_banner: str | None = None
    force: bool = False
    timeline_sequence_status: str | None = None
    timeline_event_count: int = 0
    sealed_bundle_artifact_path: str | None = None
    sealed_bundle_sha256: str | None = None
    verification_artifact_path: str | None = None
    verification_status: str | None = None
    drift_artifact_path: str | None = None
    drift_status: str | None = None
    step_count: int = 0
    passed_step_count: int = 0
    failed_step_count: int = 0
    skipped_step_count: int = 0
    steps: list[PaperExecutionEvidenceBundleRotationExecutionStep] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _rotation_execution_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleRotationExecutionView(BaseModel):
    """Read-plane summary of a bundle-rotation execution manifest."""

    schema_version: Literal["paper_execution_evidence_bundle_rotation_execution_view/v1"] = "paper_execution_evidence_bundle_rotation_execution_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    rotation_execution_status: Literal["PASS", "FAILED", "BLOCKED", "SKIPPED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_recommendation_status: str | None = None
    timeline_sequence_status: str | None = None
    sealed_bundle_sha256: str | None = None
    verification_status: str | None = None
    drift_status: str | None = None
    step_count: int = 0
    passed_step_count: int = 0
    failed_step_count: int = 0
    skipped_step_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


__all__ = (
    "PaperExecutionEvidenceBundleRotationArtifact",
    "PaperExecutionEvidenceBundleRotationView",
    "PaperExecutionEvidenceBundleRotationExecutionStep",
    "PaperExecutionEvidenceBundleRotationExecutionArtifact",
    "PaperExecutionEvidenceBundleRotationExecutionView",
)
