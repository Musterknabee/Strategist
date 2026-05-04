"""Research OS handoff verification and reviewer signoff contracts.

These artifacts verify that a single-tenant Research OS handoff pack still matches
its referenced source evidence and then record a reviewer-facing signoff posture.
They are not deployment approval, live-trading readiness, broker order authority,
or profitability certification.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner


class ResearchOsHandoffVerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    STALE = "STALE"
    TAMPERED = "TAMPERED"
    MISSING = "MISSING"
    BLOCKED = "BLOCKED"


class ResearchOsHandoffDigestCheckStatus(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    MISSING = "MISSING"
    UNREADABLE = "UNREADABLE"
    NO_EXPECTED_DIGEST = "NO_EXPECTED_DIGEST"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ResearchOsHandoffReviewerDecision(str, Enum):
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ACCEPTED_WITH_RESTRICTIONS = "ACCEPTED_WITH_RESTRICTIONS"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"


class ResearchOsHandoffSourceDigestCheck(BaseModel):
    schema_version: Literal["research_os_handoff_source_digest_check/v1"] = "research_os_handoff_source_digest_check/v1"
    label: str = Field(min_length=1)
    artifact_path: str = ""
    present: bool = False
    status: ResearchOsHandoffDigestCheckStatus = ResearchOsHandoffDigestCheckStatus.NOT_APPLICABLE
    expected_manifest_sha256: str | None = None
    observed_manifest_sha256: str | None = None
    observed_file_sha256: str | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class ResearchOsHandoffVerificationResult(BaseModel):
    schema_version: Literal["research_os_handoff_verification_result/v1"] = "research_os_handoff_verification_result/v1"
    verification_id: str = Field(min_length=1)
    verified_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifact_root: str = Field(min_length=1)
    status: ResearchOsHandoffVerificationStatus = ResearchOsHandoffVerificationStatus.MISSING
    trust_banner: ResearchOsTrustBanner = ResearchOsTrustBanner.UNTRUSTED
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_broker_orders: bool = True
    no_order_controls: bool = True
    no_profitability_claim: bool = True
    deployment_approval_unchanged: bool = True
    deployment_approved: bool = False
    handoff_verified: bool = False
    source_handoff_id: str | None = None
    source_handoff_status: str | None = None
    source_handoff_decision: str | None = None
    handoff_manifest_path: str = ""
    expected_handoff_manifest_sha256: str | None = None
    observed_handoff_manifest_sha256: str | None = None
    expected_handoff_spine_sha256: str | None = None
    observed_handoff_spine_sha256: str | None = None
    source_digest_checks: list[ResearchOsHandoffSourceDigestCheck] = Field(default_factory=list)
    match_count: int = 0
    mismatch_count: int = 0
    missing_count: int = 0
    unchecked_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    verification_spine_sha256: str = ""
    result_sha256: str = ""
    disclaimer: str = (
        "Research OS handoff verification proves only that the handoff pack and referenced source artifacts "
        "still match their recorded digests. It does not approve deployment, enable live trading, authorize "
        "broker orders, expose browser order controls, or certify profitability."
    )

    model_config = {"extra": "forbid"}

    @field_validator("verified_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("verified_at_utc must be timezone-aware")
        return v


class ResearchOsHandoffReviewerSignoff(BaseModel):
    schema_version: Literal["research_os_handoff_reviewer_signoff/v1"] = "research_os_handoff_reviewer_signoff/v1"
    signoff_id: str = Field(min_length=1)
    signed_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifact_root: str = Field(min_length=1)
    reviewer_id: str = Field(min_length=1)
    decision: ResearchOsHandoffReviewerDecision = ResearchOsHandoffReviewerDecision.BLOCKED
    trust_banner: ResearchOsTrustBanner = ResearchOsTrustBanner.UNTRUSTED
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_broker_orders: bool = True
    no_order_controls: bool = True
    no_profitability_claim: bool = True
    deployment_approval_unchanged: bool = True
    deployment_approved: bool = False
    source_verification_id: str | None = None
    source_verification_status: str | None = None
    source_handoff_id: str | None = None
    source_handoff_decision: str | None = None
    rationale: str = Field(default="", max_length=4000)
    constraints: list[str] = Field(default_factory=list)
    required_followups: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    signoff_spine_sha256: str = ""
    manifest_sha256: str = ""
    disclaimer: str = (
        "Research OS handoff reviewer signoff is an operator review record only. It does not change "
        "DEPLOYMENT_APPROVED, authorize live trading, submit broker orders, add browser order controls, "
        "or certify profitability."
    )

    model_config = {"extra": "forbid"}

    @field_validator("signed_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("signed_at_utc must be timezone-aware")
        return v


__all__ = [
    "ResearchOsHandoffDigestCheckStatus",
    "ResearchOsHandoffReviewerDecision",
    "ResearchOsHandoffReviewerSignoff",
    "ResearchOsHandoffSourceDigestCheck",
    "ResearchOsHandoffVerificationResult",
    "ResearchOsHandoffVerificationStatus",
]
