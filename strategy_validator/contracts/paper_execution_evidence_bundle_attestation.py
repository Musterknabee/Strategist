"""Paper execution evidence-bundle attestation contracts."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *

class PaperExecutionEvidenceBundleAttestationArtifact(BaseModel):
    """Keyless local DSSE-style attestation envelope for paper execution bundles.

    This deliberately does not use private keys. It binds a sealed, verified,
    in-sync paper execution evidence bundle to a structured in-toto-like
    statement so the operator can inspect attestability before introducing real
    signing infrastructure.
    """

    schema_version: Literal["paper_execution_evidence_bundle_attestation/v1"] = "paper_execution_evidence_bundle_attestation/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    attestation_authority: Literal["KEYLESS_LOCAL_STUB"] = "KEYLESS_LOCAL_STUB"
    attestation_mode: Literal["KEYLESS_LOCAL_STUB"] = "KEYLESS_LOCAL_STUB"
    signature_status: Literal["UNSIGNED_KEYLESS_STUB"] = "UNSIGNED_KEYLESS_STUB"
    attestation_status: Literal["ATTESTED", "ATTESTED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    signer_identity: str = "local-operator-keyless-stub"
    source_bundle_artifact_path: str | None = None
    source_bundle_sha256: str | None = None
    source_bundle_status: str | None = None
    source_verification_artifact_path: str | None = None
    source_verification_artifact_sha256: str | None = None
    source_verification_status: str | None = None
    source_drift_artifact_path: str | None = None
    source_drift_artifact_sha256: str | None = None
    source_drift_status: str | None = None
    statement_payload_sha256: str | None = None
    envelope: dict[str, Any] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _attestation_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleAttestationView(BaseModel):
    """Read-plane summary of a keyless local attestation envelope."""

    schema_version: Literal["paper_execution_evidence_bundle_attestation_view/v1"] = "paper_execution_evidence_bundle_attestation_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    attestation_status: Literal["ATTESTED", "ATTESTED_RESTRICTED", "BLOCKED", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    attestation_mode: str = "KEYLESS_LOCAL_STUB"
    signature_status: str = "UNSIGNED_KEYLESS_STUB"
    signer_identity: str | None = None
    source_bundle_sha256: str | None = None
    source_bundle_status: str | None = None
    source_verification_status: str | None = None
    source_drift_status: str | None = None
    statement_payload_sha256: str | None = None
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleAttestationVerificationArtifact(BaseModel):
    """Read-only verification result for a keyless local attestation envelope.

    The verifier recomputes the attestation artifact digest, validates the
    embedded statement payload hash, checks the keyless-stub signature marker,
    and re-hashes the attestation's referenced bundle / verification / drift
    artifacts when their paths are available. It is read-only and paper-only.
    """

    schema_version: Literal["paper_execution_evidence_bundle_attestation_verification/v1"] = "paper_execution_evidence_bundle_attestation_verification/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    verification_authority: Literal["READ_ONLY"] = "READ_ONLY"
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_attestation_artifact_path: str | None = None
    source_attestation_declared_sha256: str | None = None
    source_attestation_computed_sha256: str | None = None
    source_attestation_status: str | None = None
    source_attestation_trust_banner: str | None = None
    artifact_hash_valid: bool = False
    statement_payload_hash_valid: bool = False
    envelope_payload_hash_valid: bool = False
    keyless_stub_signature_valid: bool = False
    source_bundle_sha256: str | None = None
    source_bundle_hash_valid: bool = False
    source_verification_artifact_sha256: str | None = None
    source_verification_hash_valid: bool = False
    source_drift_artifact_sha256: str | None = None
    source_drift_hash_valid: bool = False
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _attestation_verification_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleAttestationVerificationView(BaseModel):
    """Read-plane summary for attestation verification results."""

    schema_version: Literal["paper_execution_evidence_bundle_attestation_verification_view/v1"] = "paper_execution_evidence_bundle_attestation_verification_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    artifact_sha256: str | None = None
    generated_at_utc: str | None = None
    verification_status: Literal["PASS", "FAIL", "UNKNOWN"] = "UNKNOWN"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    source_attestation_artifact_path: str | None = None
    source_attestation_declared_sha256: str | None = None
    source_attestation_computed_sha256: str | None = None
    source_attestation_status: str | None = None
    source_attestation_trust_banner: str | None = None
    artifact_hash_valid: bool = False
    statement_payload_hash_valid: bool = False
    envelope_payload_hash_valid: bool = False
    keyless_stub_signature_valid: bool = False
    source_bundle_hash_valid: bool = False
    source_verification_hash_valid: bool = False
    source_drift_hash_valid: bool = False
    blocker_count: int = 0
    warning_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


__all__ = (
    "PaperExecutionEvidenceBundleAttestationArtifact",
    "PaperExecutionEvidenceBundleAttestationView",
    "PaperExecutionEvidenceBundleAttestationVerificationArtifact",
    "PaperExecutionEvidenceBundleAttestationVerificationView",
)
