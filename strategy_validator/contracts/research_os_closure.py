"""Research OS evidence closure contracts (read-plane evidence; no trading authority)."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ResearchOsClosureStatus(str, Enum):
    COMPLETE = "COMPLETE"
    DEGRADED = "DEGRADED"
    BLOCKED = "BLOCKED"
    EMPTY = "EMPTY"


class ResearchOsTrustBanner(str, Enum):
    TRUSTED = "TRUSTED"
    TRUST_RESTRICTED = "TRUST_RESTRICTED"
    UNTRUSTED = "UNTRUSTED"


class ResearchOsEvidenceArtifactRef(BaseModel):
    schema_version: Literal["research_os_evidence_artifact_ref/v1"] = "research_os_evidence_artifact_ref/v1"
    artifact_kind: str = Field(min_length=1)
    artifact_path: str = Field(min_length=1)
    required: bool = False
    exists: bool = False
    readable: bool = False
    file_sha256: str | None = None
    schema_version_observed: str | None = None
    status_hint: str | None = None
    ok_hint: bool | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class ResearchOsClosureManifest(BaseModel):
    schema_version: Literal["research_os_closure_manifest/v1"] = "research_os_closure_manifest/v1"
    closure_id: str = Field(min_length=1)
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifact_root: str = Field(min_length=1)
    status: ResearchOsClosureStatus = ResearchOsClosureStatus.DEGRADED
    trust_banner: ResearchOsTrustBanner = ResearchOsTrustBanner.TRUST_RESTRICTED
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_broker_orders: bool = True
    no_profitability_claim: bool = True
    deployment_approval_unchanged: bool = True
    artifacts: list[ResearchOsEvidenceArtifactRef] = Field(default_factory=list)
    artifact_count: int = 0
    present_artifact_count: int = 0
    missing_required: list[str] = Field(default_factory=list)
    unreadable_artifacts: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    digests: dict[str, str] = Field(default_factory=dict)
    manifest_sha256: str = ""
    disclaimer: str = (
        "Evidence closure only. This manifest does not authorize live trading, broker orders, "
        "deployment approval, or profitability claims."
    )

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


__all__ = [
    "ResearchOsClosureManifest",
    "ResearchOsClosureStatus",
    "ResearchOsEvidenceArtifactRef",
    "ResearchOsTrustBanner",
]
