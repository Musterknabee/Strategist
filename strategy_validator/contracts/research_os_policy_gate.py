"""Research OS policy gate contracts.

The policy gate turns the evidence spine (closure, attestation, briefing,
export, operator run, catalog, drift) into a read-plane operator readiness
classification. It is advisory/governance evidence only: no live trading, no
broker orders, no browser mutation controls, no ledger mutation, no deployment
approval, and no profitability claim.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner


class ResearchOsPolicyGateDecision(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"
    EMPTY = "EMPTY"


class ResearchOsPolicyGateRuleStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ResearchOsPolicyGateSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKER = "BLOCKER"


class ResearchOsPolicyGateInputRef(BaseModel):
    schema_version: Literal["research_os_policy_gate_input_ref/v1"] = "research_os_policy_gate_input_ref/v1"
    input_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    artifact_path: str
    exists: bool = False
    readable: bool = False
    file_sha256: str | None = None
    schema_version_observed: str | None = None
    status_hint: str | None = None
    trust_banner_hint: str | None = None
    decision_hint: str | None = None
    verification_status_hint: str | None = None
    ok_hint: bool | None = None
    warnings_count: int = 0
    blockers_count: int = 0
    safety_flags: dict[str, bool | None] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ResearchOsPolicyGateRuleResult(BaseModel):
    schema_version: Literal["research_os_policy_gate_rule_result/v1"] = "research_os_policy_gate_rule_result/v1"
    rule_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: ResearchOsPolicyGateRuleStatus = ResearchOsPolicyGateRuleStatus.PASS
    severity: ResearchOsPolicyGateSeverity = ResearchOsPolicyGateSeverity.INFO
    evidence_refs: list[str] = Field(default_factory=list)
    message: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class ResearchOsPolicyGateReport(BaseModel):
    schema_version: Literal["research_os_policy_gate_report/v1"] = "research_os_policy_gate_report/v1"
    gate_id: str = Field(min_length=1)
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifact_root: str = Field(min_length=1)
    decision: ResearchOsPolicyGateDecision = ResearchOsPolicyGateDecision.WARN
    trust_banner: ResearchOsTrustBanner = ResearchOsTrustBanner.TRUST_RESTRICTED
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_broker_orders: bool = True
    no_order_controls: bool = True
    no_profitability_claim: bool = True
    deployment_approval_unchanged: bool = True
    required_input_count: int = 0
    present_input_count: int = 0
    warning_count: int = 0
    blocker_count: int = 0
    inputs: list[ResearchOsPolicyGateInputRef] = Field(default_factory=list)
    rules: list[ResearchOsPolicyGateRuleResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    recommended_operator_actions: list[str] = Field(default_factory=list)
    gate_spine_sha256: str = ""
    manifest_sha256: str = ""
    disclaimer: str = (
        "Research OS policy gate is read-plane governance evidence only. PASS/WARN/BLOCK is an "
        "operator review posture, not deployment approval, live-trading readiness, broker-order "
        "authority, or profitability certification."
    )

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


__all__ = [
    "ResearchOsPolicyGateDecision",
    "ResearchOsPolicyGateInputRef",
    "ResearchOsPolicyGateReport",
    "ResearchOsPolicyGateRuleResult",
    "ResearchOsPolicyGateRuleStatus",
    "ResearchOsPolicyGateSeverity",
]
