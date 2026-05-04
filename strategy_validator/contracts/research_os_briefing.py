"""Research OS daily briefing pack contracts.

Briefing packs are read-plane/evidence-plane artifacts. They summarize Research OS
closure, attestation, and paper-research subsystem posture for an operator. They do
not authorize live trading, broker orders, deployment approval, or profitability claims.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner


class ResearchOsBriefingStatus(str, Enum):
    READY = "READY"
    RESTRICTED = "RESTRICTED"
    BLOCKED = "BLOCKED"
    EMPTY = "EMPTY"


class ResearchOsBriefingSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKER = "BLOCKER"


class ResearchOsBriefingSection(BaseModel):
    schema_version: Literal["research_os_briefing_section/v1"] = "research_os_briefing_section/v1"
    section_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: str = Field(default="UNKNOWN")
    summary: str = Field(default="")
    artifact_path: str | None = None
    digest: str | None = None
    key_fields: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ResearchOsBriefingActionItem(BaseModel):
    schema_version: Literal["research_os_briefing_action_item/v1"] = "research_os_briefing_action_item/v1"
    action_id: str = Field(min_length=1)
    severity: ResearchOsBriefingSeverity = ResearchOsBriefingSeverity.INFO
    title: str = Field(min_length=1)
    detail: str = Field(default="")
    suggested_command: str | None = None
    related_section_id: str | None = None

    model_config = {"extra": "forbid"}


class ResearchOsBriefingPack(BaseModel):
    schema_version: Literal["research_os_briefing_pack/v1"] = "research_os_briefing_pack/v1"
    briefing_id: str = Field(min_length=1)
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifact_root: str = Field(min_length=1)
    status: ResearchOsBriefingStatus = ResearchOsBriefingStatus.RESTRICTED
    trust_banner: ResearchOsTrustBanner = ResearchOsTrustBanner.TRUST_RESTRICTED
    headline: str = Field(default="")
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_broker_orders: bool = True
    no_profitability_claim: bool = True
    deployment_approval_unchanged: bool = True
    sections: list[ResearchOsBriefingSection] = Field(default_factory=list)
    action_items: list[ResearchOsBriefingActionItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    digests: dict[str, str] = Field(default_factory=dict)
    briefing_sha256: str = ""
    disclaimer: str = (
        "Research OS briefing is operational evidence only. It does not authorize live trading, "
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
    "ResearchOsBriefingActionItem",
    "ResearchOsBriefingPack",
    "ResearchOsBriefingSection",
    "ResearchOsBriefingSeverity",
    "ResearchOsBriefingStatus",
]
