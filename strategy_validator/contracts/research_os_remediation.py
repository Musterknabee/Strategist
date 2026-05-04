"""Research OS remediation plan contracts.

The remediation plan turns Research OS policy-gate, exception, catalog, and drift
signals into a read-plane action queue. It is operator guidance only: no live
trading, no broker orders, no browser mutation controls, no ledger mutation, no
deployment approval, and no profitability claim.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner


class ResearchOsRemediationStatus(str, Enum):
    READY = "READY"
    RESTRICTED = "RESTRICTED"
    BLOCKED = "BLOCKED"
    EMPTY = "EMPTY"


class ResearchOsRemediationPriority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class ResearchOsRemediationItemStatus(str, Enum):
    OPEN = "OPEN"
    BLOCKED = "BLOCKED"
    WAIVED_BY_EXCEPTION = "WAIVED_BY_EXCEPTION"
    DONE = "DONE"


class ResearchOsRemediationCategory(str, Enum):
    REQUIRED_EVIDENCE = "REQUIRED_EVIDENCE"
    OPTIONAL_EVIDENCE = "OPTIONAL_EVIDENCE"
    POLICY_GATE = "POLICY_GATE"
    EXCEPTION = "EXCEPTION"
    DRIFT = "DRIFT"
    CATALOG = "CATALOG"
    PROVIDER_LOOP = "PROVIDER_LOOP"
    PAPER_BROKER = "PAPER_BROKER"
    STRATEGY_MEMORY = "STRATEGY_MEMORY"
    THESIS = "THESIS"
    SHADOW_BOOK = "SHADOW_BOOK"
    FRONTEND_RUNTIME = "FRONTEND_RUNTIME"
    SECURITY = "SECURITY"
    OTHER = "OTHER"


class ResearchOsRemediationItem(BaseModel):
    schema_version: Literal["research_os_remediation_item/v1"] = "research_os_remediation_item/v1"
    item_id: str = Field(min_length=1)
    category: ResearchOsRemediationCategory = ResearchOsRemediationCategory.OTHER
    priority: ResearchOsRemediationPriority = ResearchOsRemediationPriority.P2
    status: ResearchOsRemediationItemStatus = ResearchOsRemediationItemStatus.OPEN
    title: str = Field(min_length=1)
    description: str = ""
    source: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    recommended_command: str | None = None
    acceptance: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class ResearchOsRemediationPlan(BaseModel):
    schema_version: Literal["research_os_remediation_plan/v1"] = "research_os_remediation_plan/v1"
    plan_id: str = Field(min_length=1)
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifact_root: str = Field(min_length=1)
    status: ResearchOsRemediationStatus = ResearchOsRemediationStatus.RESTRICTED
    trust_banner: ResearchOsTrustBanner = ResearchOsTrustBanner.TRUST_RESTRICTED
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_broker_orders: bool = True
    no_order_controls: bool = True
    no_profitability_claim: bool = True
    deployment_approval_unchanged: bool = True
    source_policy_gate_id: str | None = None
    source_policy_gate_decision: str | None = None
    source_exception_id: str | None = None
    source_exception_status: str | None = None
    source_catalog_id: str | None = None
    source_drift_id: str | None = None
    open_count: int = 0
    blocked_count: int = 0
    waived_count: int = 0
    item_count: int = 0
    priority_counts: dict[str, int] = Field(default_factory=dict)
    category_counts: dict[str, int] = Field(default_factory=dict)
    items: list[ResearchOsRemediationItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    recommended_next_actions: list[str] = Field(default_factory=list)
    remediation_spine_sha256: str = ""
    manifest_sha256: str = ""
    disclaimer: str = (
        "Research OS remediation plans are read-plane operator guidance. They do not approve "
        "deployment, live trading, broker orders, browser order controls, or profitability claims."
    )

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


__all__ = [
    "ResearchOsRemediationCategory",
    "ResearchOsRemediationItem",
    "ResearchOsRemediationItemStatus",
    "ResearchOsRemediationPlan",
    "ResearchOsRemediationPriority",
    "ResearchOsRemediationStatus",
]
