"""Research OS release-readiness review contracts.

The release-readiness report converts the latest Research OS policy-gate,
exception, remediation, catalog, drift, and operator-run evidence into a
machine-readable *release review* posture. It is not deployment approval, not
live-trading readiness, not broker order authority, and not a profitability
claim.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner


class ResearchOsReleaseReadinessStatus(str, Enum):
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    RESTRICTED_REVIEW = "RESTRICTED_REVIEW"
    NOT_READY = "NOT_READY"
    BLOCKED = "BLOCKED"
    EMPTY = "EMPTY"


class ResearchOsReleaseReadinessDecision(str, Enum):
    SINGLE_TENANT_REVIEW_READY = "SINGLE_TENANT_REVIEW_READY"
    REVIEW_WITH_RESTRICTIONS = "REVIEW_WITH_RESTRICTIONS"
    REMEDIATION_REQUIRED = "REMEDIATION_REQUIRED"
    BLOCKED_BY_EVIDENCE = "BLOCKED_BY_EVIDENCE"
    NO_EVIDENCE = "NO_EVIDENCE"


class ResearchOsReleaseReadinessCriterionStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ResearchOsReleaseReadinessCriterion(BaseModel):
    schema_version: Literal["research_os_release_readiness_criterion/v1"] = "research_os_release_readiness_criterion/v1"
    criterion_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: ResearchOsReleaseReadinessCriterionStatus = ResearchOsReleaseReadinessCriterionStatus.WARN
    source: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class ResearchOsReleaseReadinessReport(BaseModel):
    schema_version: Literal["research_os_release_readiness_report/v1"] = "research_os_release_readiness_report/v1"
    report_id: str = Field(min_length=1)
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifact_root: str = Field(min_length=1)
    status: ResearchOsReleaseReadinessStatus = ResearchOsReleaseReadinessStatus.NOT_READY
    decision: ResearchOsReleaseReadinessDecision = ResearchOsReleaseReadinessDecision.REMEDIATION_REQUIRED
    trust_banner: ResearchOsTrustBanner = ResearchOsTrustBanner.TRUST_RESTRICTED
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_broker_orders: bool = True
    no_order_controls: bool = True
    no_profitability_claim: bool = True
    deployment_approval_unchanged: bool = True
    deployment_approved: bool = False
    release_review_ready: bool = False
    source_policy_gate_id: str | None = None
    source_policy_gate_decision: str | None = None
    source_exception_id: str | None = None
    source_exception_status: str | None = None
    source_remediation_plan_id: str | None = None
    source_operator_run_id: str | None = None
    source_catalog_id: str | None = None
    source_drift_id: str | None = None
    p0_open_count: int = 0
    p1_open_count: int = 0
    p2_open_count: int = 0
    p3_open_count: int = 0
    open_remediation_count: int = 0
    blocked_remediation_count: int = 0
    waived_remediation_count: int = 0
    criterion_counts: dict[str, int] = Field(default_factory=dict)
    criteria: list[ResearchOsReleaseReadinessCriterion] = Field(default_factory=list)
    required_followups: list[str] = Field(default_factory=list)
    recommended_review_commands: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    release_readiness_spine_sha256: str = ""
    manifest_sha256: str = ""
    disclaimer: str = (
        "Research OS release-readiness reports only classify readiness for a single-tenant release review. "
        "They do not approve deployment, enable live trading, authorize broker orders, expose browser order controls, "
        "or certify profitability. DEPLOYMENT_APPROVED remains unchanged and false in this artifact."
    )

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


__all__ = [
    "ResearchOsReleaseReadinessCriterion",
    "ResearchOsReleaseReadinessCriterionStatus",
    "ResearchOsReleaseReadinessDecision",
    "ResearchOsReleaseReadinessReport",
    "ResearchOsReleaseReadinessStatus",
]
