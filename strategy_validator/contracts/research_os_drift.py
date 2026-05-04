"""Research OS evidence drift contracts.

The drift report compares two evidence catalogs and summarizes added, removed,
changed, and unchanged Research OS artifacts. It is read-plane only: no broker
orders, no network calls, no ledger mutation, no deployment approval, and no
profitability claim.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner


class ResearchOsEvidenceDriftStatus(str, Enum):
    READY = "READY"
    RESTRICTED = "RESTRICTED"
    BLOCKED = "BLOCKED"
    EMPTY = "EMPTY"


class ResearchOsEvidenceDriftChangeType(str, Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    CHANGED = "CHANGED"
    UNCHANGED = "UNCHANGED"


class ResearchOsEvidenceDriftEntry(BaseModel):
    schema_version: Literal["research_os_evidence_drift_entry/v1"] = "research_os_evidence_drift_entry/v1"
    key: str = Field(min_length=1)
    category: str = Field(min_length=1)
    change_type: ResearchOsEvidenceDriftChangeType
    baseline_relative_path: str | None = None
    candidate_relative_path: str | None = None
    baseline_file_sha256: str | None = None
    candidate_file_sha256: str | None = None
    baseline_status_hint: str | None = None
    candidate_status_hint: str | None = None
    baseline_trust_banner_hint: str | None = None
    candidate_trust_banner_hint: str | None = None
    baseline_generated_at_utc: str | None = None
    candidate_generated_at_utc: str | None = None
    size_delta_bytes: int | None = None
    changed_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ResearchOsEvidenceDriftReport(BaseModel):
    schema_version: Literal["research_os_evidence_drift_report/v1"] = "research_os_evidence_drift_report/v1"
    drift_id: str = Field(min_length=1)
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifact_root: str = Field(min_length=1)
    baseline_catalog_id: str | None = None
    baseline_catalog_path: str | None = None
    baseline_catalog_sha256: str | None = None
    candidate_catalog_id: str | None = None
    candidate_catalog_path: str | None = None
    candidate_catalog_sha256: str | None = None
    status: ResearchOsEvidenceDriftStatus = ResearchOsEvidenceDriftStatus.RESTRICTED
    trust_banner: ResearchOsTrustBanner = ResearchOsTrustBanner.TRUST_RESTRICTED
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_broker_orders: bool = True
    no_order_controls: bool = True
    no_profitability_claim: bool = True
    deployment_approval_unchanged: bool = True
    added_count: int = 0
    removed_count: int = 0
    changed_count: int = 0
    unchanged_count: int = 0
    total_compared_count: int = 0
    category_change_counts: dict[str, dict[str, int]] = Field(default_factory=dict)
    entries: list[ResearchOsEvidenceDriftEntry] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    drift_spine_sha256: str = ""
    manifest_sha256: str = ""
    disclaimer: str = (
        "Research OS evidence drift is a read-plane comparison of existing evidence catalogs. "
        "It does not authorize live trading, broker orders, deployment approval, or profitability claims."
    )

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


__all__ = [
    "ResearchOsEvidenceDriftChangeType",
    "ResearchOsEvidenceDriftEntry",
    "ResearchOsEvidenceDriftReport",
    "ResearchOsEvidenceDriftStatus",
]
