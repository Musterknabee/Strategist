"""Research OS operator run contracts.

Operator run manifests are read-plane/evidence-plane records. They sequence existing
Research OS evidence steps (closure, verification, attestation, briefing, export)
without granting live trading, broker order, deployment approval, or profitability authority.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner


class ResearchOsOperatorRunStatus(str, Enum):
    COMPLETE = "COMPLETE"
    RESTRICTED = "RESTRICTED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    EMPTY = "EMPTY"


class ResearchOsOperatorRunStepStatus(str, Enum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ResearchOsOperatorRunStep(BaseModel):
    schema_version: Literal["research_os_operator_run_step/v1"] = "research_os_operator_run_step/v1"
    step_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: ResearchOsOperatorRunStepStatus = ResearchOsOperatorRunStepStatus.SUCCESS
    started_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifact_path: str | None = None
    artifact_sha256: str | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    @field_validator("started_at_utc", "completed_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("operator run step timestamps must be timezone-aware")
        return v


class ResearchOsOperatorRunManifest(BaseModel):
    schema_version: Literal["research_os_operator_run_manifest/v1"] = "research_os_operator_run_manifest/v1"
    run_id: str = Field(min_length=1)
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifact_root: str = Field(min_length=1)
    status: ResearchOsOperatorRunStatus = ResearchOsOperatorRunStatus.RESTRICTED
    trust_banner: ResearchOsTrustBanner = ResearchOsTrustBanner.TRUST_RESTRICTED
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_broker_orders: bool = True
    no_order_controls: bool = True
    no_profitability_claim: bool = True
    deployment_approval_unchanged: bool = True
    steps: list[ResearchOsOperatorRunStep] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    digests: dict[str, str] = Field(default_factory=dict)
    manifest_sha256: str = ""
    disclaimer: str = (
        "Research OS operator run is paper-only operational evidence. It does not authorize live trading, "
        "broker orders, deployment approval, or profitability claims."
    )

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


__all__ = [
    "ResearchOsOperatorRunManifest",
    "ResearchOsOperatorRunStatus",
    "ResearchOsOperatorRunStep",
    "ResearchOsOperatorRunStepStatus",
]
