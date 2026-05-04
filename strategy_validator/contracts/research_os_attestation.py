"""Research OS closure verification and operator attestation contracts.

These contracts are read-plane/evidence-plane only. They do not authorize live
trading, broker orders, deployment approval, or profitability claims.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner


class ResearchOsClosureVerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    STALE = "STALE"
    TAMPERED = "TAMPERED"
    MISSING = "MISSING"
    BLOCKED = "BLOCKED"


class ResearchOsOperatorDecision(str, Enum):
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ACCEPTED_WITH_RESTRICTIONS = "ACCEPTED_WITH_RESTRICTIONS"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"


class ResearchOsClosureDigestCheck(BaseModel):
    schema_version: Literal["research_os_closure_digest_check/v1"] = "research_os_closure_digest_check/v1"
    artifact_kind: str = Field(min_length=1)
    artifact_path: str = Field(min_length=1)
    expected_sha256: str | None = None
    observed_sha256: str | None = None
    exists_now: bool = False
    readable_now: bool = False
    match: bool | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ResearchOsClosureVerificationResult(BaseModel):
    schema_version: Literal["research_os_closure_verification_result/v1"] = "research_os_closure_verification_result/v1"
    verification_id: str = Field(min_length=1)
    closure_id: str | None = None
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    manifest_path: str = Field(min_length=1)
    artifact_root: str | None = None
    status: ResearchOsClosureVerificationStatus = ResearchOsClosureVerificationStatus.MISSING
    trust_banner: ResearchOsTrustBanner = ResearchOsTrustBanner.UNTRUSTED
    manifest_sha256_expected: str | None = None
    manifest_sha256_observed: str | None = None
    evidence_spine_sha256_expected: str | None = None
    artifact_checks: list[ResearchOsClosureDigestCheck] = Field(default_factory=list)
    digest_mismatches: list[str] = Field(default_factory=list)
    missing_artifacts: list[str] = Field(default_factory=list)
    unreadable_artifacts: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_broker_orders: bool = True
    no_profitability_claim: bool = True
    deployment_approval_unchanged: bool = True
    result_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class ResearchOsOperatorAttestation(BaseModel):
    schema_version: Literal["research_os_operator_attestation/v1"] = "research_os_operator_attestation/v1"
    attestation_id: str = Field(min_length=1)
    closure_id: str = Field(min_length=1)
    operator_id: str = Field(min_length=1)
    decision: ResearchOsOperatorDecision = ResearchOsOperatorDecision.ACKNOWLEDGED
    attested_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rationale: str = Field(default="", max_length=4096)
    constraints: list[str] = Field(default_factory=list)
    verification_status: ResearchOsClosureVerificationStatus
    closure_trust_banner: ResearchOsTrustBanner
    closure_manifest_sha256: str | None = None
    verification_result_sha256: str | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_broker_orders: bool = True
    no_profitability_claim: bool = True
    deployment_approval_unchanged: bool = True
    attestation_sha256: str = ""
    disclaimer: str = (
        "Operator attestation acknowledges evidence posture only. It does not authorize live trading, "
        "broker orders, deployment approval, or profitability claims."
    )

    model_config = {"extra": "forbid"}

    @field_validator("attested_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("attested_at_utc must be timezone-aware")
        return v


__all__ = [
    "ResearchOsClosureDigestCheck",
    "ResearchOsClosureVerificationResult",
    "ResearchOsClosureVerificationStatus",
    "ResearchOsOperatorAttestation",
    "ResearchOsOperatorDecision",
]
