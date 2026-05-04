"""Research OS governed exception contracts.

Exceptions are time-bounded operator annotations over Research OS policy-gate
WARN/BLOCK evidence. They never override safety policy, deployment approval, live
trading restrictions, broker-order restrictions, or read-plane boundaries.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner


class ResearchOsExceptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ResearchOsExceptionDecision(str, Enum):
    GRANTED_WITH_RESTRICTIONS = "GRANTED_WITH_RESTRICTIONS"
    REJECTED_POLICY_BLOCK = "REJECTED_POLICY_BLOCK"
    REJECTED_EMPTY_GATE = "REJECTED_EMPTY_GATE"
    NOT_NEEDED_FOR_PASS = "NOT_NEEDED_FOR_PASS"
    REVOKED = "REVOKED"


class ResearchOsExceptionScope(str, Enum):
    POLICY_GATE_WARN = "POLICY_GATE_WARN"
    MISSING_OPTIONAL_EVIDENCE = "MISSING_OPTIONAL_EVIDENCE"
    PENDING_PROVIDER_KEY = "PENDING_PROVIDER_KEY"
    PENDING_BROKER_KEY = "PENDING_BROKER_KEY"
    RESTRICTED_TRUST = "RESTRICTED_TRUST"
    EVIDENCE_DRIFT_REVIEW = "EVIDENCE_DRIFT_REVIEW"
    OPERATOR_ACKNOWLEDGEMENT = "OPERATOR_ACKNOWLEDGEMENT"
    OTHER = "OTHER"


class ResearchOsExceptionRecord(BaseModel):
    schema_version: Literal["research_os_exception_record/v1"] = "research_os_exception_record/v1"
    exception_id: str = Field(min_length=1)
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at_utc: datetime | None = None
    operator_id: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    source_policy_gate_id: str | None = None
    source_policy_gate_decision: str | None = None
    source_policy_gate_sha256: str | None = None
    status: ResearchOsExceptionStatus = ResearchOsExceptionStatus.REJECTED
    decision: ResearchOsExceptionDecision = ResearchOsExceptionDecision.REJECTED_POLICY_BLOCK
    trust_banner: ResearchOsTrustBanner = ResearchOsTrustBanner.TRUST_RESTRICTED
    scopes: list[ResearchOsExceptionScope] = Field(default_factory=list)
    covered_warnings: list[str] = Field(default_factory=list)
    covered_blockers: list[str] = Field(default_factory=list)
    residual_warnings: list[str] = Field(default_factory=list)
    residual_blockers: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    recommended_followups: list[str] = Field(default_factory=list)
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_broker_orders: bool = True
    no_order_controls: bool = True
    no_profitability_claim: bool = True
    deployment_approval_unchanged: bool = True
    exception_spine_sha256: str = ""
    manifest_sha256: str = ""
    disclaimer: str = (
        "Research OS exceptions are time-bounded governance annotations over evidence warnings. "
        "They do not approve deployment, live trading, broker orders, browser order controls, "
        "or profitability claims, and they cannot override BLOCK-level safety evidence."
    )

    model_config = {"extra": "forbid"}

    @field_validator("created_at_utc", "expires_at_utc")
    @classmethod
    def _tz(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return v
        if v.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        return v


__all__ = [
    "ResearchOsExceptionDecision",
    "ResearchOsExceptionRecord",
    "ResearchOsExceptionScope",
    "ResearchOsExceptionStatus",
]
