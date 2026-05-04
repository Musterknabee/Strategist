"""Research OS portable evidence export contracts.

Export bundles are offline/read-plane artifacts. They package already-produced Research OS
closure, attestation, briefing, and paper-research evidence for operator review or audit
handoff. They do not authorize live trading, broker orders, deployment approval, or
profitability claims.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner


class ResearchOsExportStatus(str, Enum):
    READY = "READY"
    RESTRICTED = "RESTRICTED"
    BLOCKED = "BLOCKED"
    EMPTY = "EMPTY"


class ResearchOsExportFormat(str, Enum):
    DIRECTORY = "DIRECTORY"
    TAR_GZ = "TAR_GZ"


class ResearchOsExportFileRef(BaseModel):
    schema_version: Literal["research_os_export_file_ref/v1"] = "research_os_export_file_ref/v1"
    label: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    bundle_path: str | None = None
    required: bool = False
    present: bool = False
    readable: bool = False
    size_bytes: int | None = None
    file_sha256: str | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ResearchOsExportVerificationResult(BaseModel):
    schema_version: Literal["research_os_export_verification_result/v1"] = "research_os_export_verification_result/v1"
    export_id: str = Field(min_length=1)
    verified_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: ResearchOsExportStatus = ResearchOsExportStatus.RESTRICTED
    verified_file_count: int = 0
    missing_file_count: int = 0
    changed_file_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    result_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("verified_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("verified_at_utc must be timezone-aware")
        return v


class ResearchOsExportManifest(BaseModel):
    schema_version: Literal["research_os_export_manifest/v1"] = "research_os_export_manifest/v1"
    export_id: str = Field(min_length=1)
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifact_root: str = Field(min_length=1)
    export_root: str = Field(min_length=1)
    bundle_directory: str = Field(min_length=1)
    archive_path: str | None = None
    archive_sha256: str | None = None
    status: ResearchOsExportStatus = ResearchOsExportStatus.RESTRICTED
    trust_banner: ResearchOsTrustBanner = ResearchOsTrustBanner.TRUST_RESTRICTED
    formats: list[ResearchOsExportFormat] = Field(default_factory=lambda: [ResearchOsExportFormat.DIRECTORY])
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_broker_orders: bool = True
    no_profitability_claim: bool = True
    deployment_approval_unchanged: bool = True
    files: list[ResearchOsExportFileRef] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    export_spine_sha256: str = ""
    manifest_sha256: str = ""
    disclaimer: str = (
        "Research OS export bundle is portable operational evidence only. It does not authorize "
        "live trading, broker orders, deployment approval, or profitability claims."
    )

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


__all__ = [
    "ResearchOsExportFileRef",
    "ResearchOsExportFormat",
    "ResearchOsExportManifest",
    "ResearchOsExportStatus",
    "ResearchOsExportVerificationResult",
]
