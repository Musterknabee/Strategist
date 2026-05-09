"""Paper execution evidence-bundle closure contracts."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *

class PaperExecutionEvidenceBundleClosureArtifact(BaseModel):
    """Durable final review packet for a paper execution evidence bundle chain.

    Closure is a read-only operator review artifact. It aggregates the latest
    sealed bundle, bundle verification, drift check, keyless attestation, and
    attestation verification into one final decision posture. It never submits
    orders, grants live authority, promotes strategies, or mutates the ledger.
    """

    schema_version: Literal["paper_execution_evidence_bundle_closure/v1"] = "paper_execution_evidence_bundle_closure/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    closure_authority: Literal["CLI_REVIEW_PACKET_ONLY"] = "CLI_REVIEW_PACKET_ONLY"
    closure_status: Literal["READY_FOR_OPERATOR_REVIEW", "READY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_bundle_artifact_path: str | None = None
    source_bundle_sha256: str | None = None
    source_bundle_status: str | None = None
    source_bundle_trust_banner: str | None = None
    source_verification_artifact_path: str | None = None
    source_verification_artifact_sha256: str | None = None
    source_verification_status: str | None = None
    source_verification_trust_banner: str | None = None
    source_drift_artifact_path: str | None = None
    source_drift_artifact_sha256: str | None = None
    source_drift_status: str | None = None
    source_drift_trust_banner: str | None = None
    source_attestation_artifact_path: str | None = None
    source_attestation_artifact_sha256: str | None = None
    source_attestation_status: str | None = None
    source_attestation_trust_banner: str | None = None
    source_attestation_verification_artifact_path: str | None = None
    source_attestation_verification_artifact_sha256: str | None = None
    source_attestation_verification_status: str | None = None
    source_attestation_verification_trust_banner: str | None = None
    source_attestation_artifact_hash_valid: bool = False
    source_attestation_statement_hash_valid: bool = False
    source_attestation_envelope_hash_valid: bool = False
    source_attestation_keyless_stub_valid: bool = False
    source_attestation_bundle_hash_valid: bool = False
    source_attestation_bundle_verification_hash_valid: bool = False
    source_attestation_drift_hash_valid: bool = False
    closure_reason_codes: list[str] = Field(default_factory=list)
    recommended_operator_sequence: list[str] = Field(default_factory=list)
    one_command_sequence_hint: str | None = None
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _closure_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleClosureView(BaseModel):
    """Read-plane summary of a paper execution evidence-bundle closure packet."""

    schema_version: Literal["paper_execution_evidence_bundle_closure_view/v1"] = "paper_execution_evidence_bundle_closure_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    closure_status: Literal["READY_FOR_OPERATOR_REVIEW", "READY_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_bundle_sha256: str | None = None
    source_bundle_status: str | None = None
    source_verification_status: str | None = None
    source_drift_status: str | None = None
    source_attestation_status: str | None = None
    source_attestation_verification_status: str | None = None
    source_attestation_artifact_hash_valid: bool = False
    source_attestation_statement_hash_valid: bool = False
    source_attestation_envelope_hash_valid: bool = False
    source_attestation_keyless_stub_valid: bool = False
    source_attestation_bundle_hash_valid: bool = False
    source_attestation_bundle_verification_hash_valid: bool = False
    source_attestation_drift_hash_valid: bool = False
    closure_reason_codes: list[str] = Field(default_factory=list)
    recommended_operator_sequence: list[str] = Field(default_factory=list)
    one_command_sequence_hint: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleClosureVerificationArtifact(BaseModel):
    """Read-only verification result for a paper evidence-bundle closure packet.

    The verifier recomputes the closure packet digest and re-hashes every
    source artifact referenced by the closure packet. It is deliberately
    read-only: no broker orders, no live authority, no promotion authority,
    and no decision-ledger mutation.
    """

    schema_version: Literal["paper_execution_evidence_bundle_closure_verification/v1"] = "paper_execution_evidence_bundle_closure_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    verification_authority: Literal["READ_ONLY"] = "READ_ONLY"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_closure_artifact_path: str | None = None
    source_closure_declared_sha256: str | None = None
    source_closure_computed_sha256: str | None = None
    source_closure_status: str | None = None
    source_closure_trust_banner: str | None = None
    closure_artifact_hash_valid: bool = False
    source_bundle_sha256: str | None = None
    source_bundle_hash_valid: bool = False
    source_verification_artifact_sha256: str | None = None
    source_verification_hash_valid: bool = False
    source_drift_artifact_sha256: str | None = None
    source_drift_hash_valid: bool = False
    source_attestation_artifact_sha256: str | None = None
    source_attestation_hash_valid: bool = False
    source_attestation_verification_artifact_sha256: str | None = None
    source_attestation_verification_hash_valid: bool = False
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _closure_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleClosureVerificationView(BaseModel):
    """Read-plane summary for closure packet verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_closure_verification_view/v1"] = "paper_execution_evidence_bundle_closure_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_closure_artifact_path: str | None = None
    source_closure_declared_sha256: str | None = None
    source_closure_computed_sha256: str | None = None
    source_closure_status: str | None = None
    source_closure_trust_banner: str | None = None
    closure_artifact_hash_valid: bool = False
    source_bundle_hash_valid: bool = False
    source_verification_hash_valid: bool = False
    source_drift_hash_valid: bool = False
    source_attestation_hash_valid: bool = False
    source_attestation_verification_hash_valid: bool = False
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


__all__ = (
    "PaperExecutionEvidenceBundleClosureArtifact",
    "PaperExecutionEvidenceBundleClosureView",
    "PaperExecutionEvidenceBundleClosureVerificationArtifact",
    "PaperExecutionEvidenceBundleClosureVerificationView",
)
