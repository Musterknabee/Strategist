"""Research OS evidence catalog contracts.

The catalog is an offline/read-plane index over already-produced Research OS artifacts.
It records paths, SHA-256 digests, category/status hints, and safety warnings without
executing research, touching broker APIs, mutating the ledger, approving deployment,
or claiming profitability.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner


class ResearchOsEvidenceCatalogStatus(str, Enum):
    READY = "READY"
    RESTRICTED = "RESTRICTED"
    BLOCKED = "BLOCKED"
    EMPTY = "EMPTY"


class ResearchOsEvidenceCatalogCategory(str, Enum):
    OPERATOR_RUN = "OPERATOR_RUN"
    DRIFT = "DRIFT"
    POLICY_GATE = "POLICY_GATE"
    EXCEPTION = "EXCEPTION"
    REMEDIATION = "REMEDIATION"
    RELEASE_READINESS = "RELEASE_READINESS"
    HANDOFF = "HANDOFF"
    HANDOFF_SIGNOFF = "HANDOFF_SIGNOFF"
    REVIEW_JOURNAL = "REVIEW_JOURNAL"
    EXPORT = "EXPORT"
    BRIEFING = "BRIEFING"
    CLOSURE = "CLOSURE"
    ATTESTATION = "ATTESTATION"
    PROVIDER_LOOP = "PROVIDER_LOOP"
    PROVIDER_SNAPSHOT = "PROVIDER_SNAPSHOT"
    PAPER_BROKER = "PAPER_BROKER"
    STRATEGY_BATCH = "STRATEGY_BATCH"
    MARKET_DATA_INTEGRITY = "MARKET_DATA_INTEGRITY"
    STRATEGY_MEMORY = "STRATEGY_MEMORY"
    STRATEGY_THESIS = "STRATEGY_THESIS"
    SHADOW_BOOK = "SHADOW_BOOK"
    RUNTIME = "RUNTIME"
    OTHER = "OTHER"


class ResearchOsEvidenceCatalogEntry(BaseModel):
    schema_version: Literal["research_os_evidence_catalog_entry/v1"] = "research_os_evidence_catalog_entry/v1"
    label: str = Field(min_length=1)
    category: ResearchOsEvidenceCatalogCategory = ResearchOsEvidenceCatalogCategory.OTHER
    artifact_path: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)
    file_sha256: str | None = None
    size_bytes: int | None = None
    schema_version_observed: str | None = None
    generated_at_utc: str | None = None
    status_hint: str | None = None
    trust_banner_hint: str | None = None
    ok_hint: bool | None = None
    run_id_hint: str | None = None
    required: bool = False
    latest_alias: bool = False
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class ResearchOsEvidenceCatalog(BaseModel):
    schema_version: Literal["research_os_evidence_catalog/v1"] = "research_os_evidence_catalog/v1"
    catalog_id: str = Field(min_length=1)
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifact_root: str = Field(min_length=1)
    status: ResearchOsEvidenceCatalogStatus = ResearchOsEvidenceCatalogStatus.RESTRICTED
    trust_banner: ResearchOsTrustBanner = ResearchOsTrustBanner.TRUST_RESTRICTED
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_broker_orders: bool = True
    no_order_controls: bool = True
    no_profitability_claim: bool = True
    deployment_approval_unchanged: bool = True
    entry_count: int = 0
    latest_entry_count: int = 0
    category_counts: dict[str, int] = Field(default_factory=dict)
    latest_by_category: dict[str, str] = Field(default_factory=dict)
    entries: list[ResearchOsEvidenceCatalogEntry] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    catalog_spine_sha256: str = ""
    manifest_sha256: str = ""
    disclaimer: str = (
        "Research OS evidence catalog is a read-plane index over existing artifacts. It does not authorize "
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
    "ResearchOsEvidenceCatalog",
    "ResearchOsEvidenceCatalogCategory",
    "ResearchOsEvidenceCatalogEntry",
    "ResearchOsEvidenceCatalogStatus",
]
