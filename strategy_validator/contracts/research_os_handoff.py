"""Research OS single-tenant handoff pack contracts.

The handoff pack summarizes the latest Research OS release-readiness, policy,
exception, remediation, export, catalog, drift, and operator-run evidence into a
portable operator handoff posture. It is not deployment approval, live-trading
readiness, broker order authority, or profitability certification.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner


class ResearchOsHandoffStatus(str, Enum):
    READY = "READY"
    RESTRICTED = "RESTRICTED"
    NOT_READY = "NOT_READY"
    BLOCKED = "BLOCKED"
    EMPTY = "EMPTY"


class ResearchOsHandoffDecision(str, Enum):
    SINGLE_TENANT_HANDOFF_READY = "SINGLE_TENANT_HANDOFF_READY"
    HANDOFF_WITH_RESTRICTIONS = "HANDOFF_WITH_RESTRICTIONS"
    REMEDIATION_REQUIRED = "REMEDIATION_REQUIRED"
    BLOCKED_BY_EVIDENCE = "BLOCKED_BY_EVIDENCE"
    NO_EVIDENCE = "NO_EVIDENCE"


class ResearchOsHandoffChecklistStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ResearchOsHandoffSourceRef(BaseModel):
    schema_version: Literal["research_os_handoff_source_ref/v1"] = "research_os_handoff_source_ref/v1"
    label: str = Field(min_length=1)
    artifact_path: str = ""
    present: bool = False
    status_hint: str | None = None
    decision_hint: str | None = None
    manifest_sha256: str | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class ResearchOsHandoffChecklistItem(BaseModel):
    schema_version: Literal["research_os_handoff_checklist_item/v1"] = "research_os_handoff_checklist_item/v1"
    item_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: ResearchOsHandoffChecklistStatus = ResearchOsHandoffChecklistStatus.WARN
    source: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    acceptance: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ResearchOsHandoffPack(BaseModel):
    schema_version: Literal["research_os_handoff_pack/v1"] = "research_os_handoff_pack/v1"
    handoff_id: str = Field(min_length=1)
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifact_root: str = Field(min_length=1)
    status: ResearchOsHandoffStatus = ResearchOsHandoffStatus.NOT_READY
    decision: ResearchOsHandoffDecision = ResearchOsHandoffDecision.REMEDIATION_REQUIRED
    trust_banner: ResearchOsTrustBanner = ResearchOsTrustBanner.TRUST_RESTRICTED
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_broker_orders: bool = True
    no_order_controls: bool = True
    no_profitability_claim: bool = True
    deployment_approval_unchanged: bool = True
    deployment_approved: bool = False
    handoff_ready: bool = False
    restricted_handoff: bool = False
    source_release_readiness_report_id: str | None = None
    source_release_readiness_decision: str | None = None
    source_policy_gate_id: str | None = None
    source_policy_gate_decision: str | None = None
    source_exception_id: str | None = None
    source_exception_status: str | None = None
    source_remediation_plan_id: str | None = None
    source_export_id: str | None = None
    source_catalog_id: str | None = None
    source_operator_run_id: str | None = None
    source_refs: list[ResearchOsHandoffSourceRef] = Field(default_factory=list)
    checklist: list[ResearchOsHandoffChecklistItem] = Field(default_factory=list)
    checklist_counts: dict[str, int] = Field(default_factory=dict)
    required_operator_commands: list[str] = Field(default_factory=list)
    handoff_constraints: list[str] = Field(default_factory=list)
    remaining_followups: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    handoff_spine_sha256: str = ""
    manifest_sha256: str = ""
    disclaimer: str = (
        "Research OS handoff packs are operator handoff evidence only. They do not approve deployment, "
        "enable live trading, authorize broker orders, expose browser order controls, or certify profitability. "
        "DEPLOYMENT_APPROVED remains unchanged and false in this artifact."
    )

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


__all__ = [
    "ResearchOsHandoffChecklistItem",
    "ResearchOsHandoffChecklistStatus",
    "ResearchOsHandoffDecision",
    "ResearchOsHandoffPack",
    "ResearchOsHandoffSourceRef",
    "ResearchOsHandoffStatus",
]
