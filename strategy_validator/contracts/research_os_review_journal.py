"""Research OS review journal contracts.

The review journal is a local append-only-style evidence index for Research OS
review decisions. It summarizes already-produced policy, exception, readiness,
handoff, and reviewer-signoff artifacts into a durable journal artifact. It is
not the canonical ledger, does not mutate the validator ledger, and does not
approve deployment, live trading, broker orders, or profitability.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner


class ResearchOsReviewJournalStatus(str, Enum):
    READY = "READY"
    RESTRICTED = "RESTRICTED"
    BLOCKED = "BLOCKED"
    EMPTY = "EMPTY"


class ResearchOsReviewJournalEntryType(str, Enum):
    HANDOFF_SIGNOFF = "HANDOFF_SIGNOFF"
    HANDOFF = "HANDOFF"
    RELEASE_READINESS = "RELEASE_READINESS"
    POLICY_GATE = "POLICY_GATE"
    EXCEPTION = "EXCEPTION"
    REMEDIATION = "REMEDIATION"
    EVIDENCE_CATALOG = "EVIDENCE_CATALOG"
    EVIDENCE_DRIFT = "EVIDENCE_DRIFT"
    OPERATOR_RUN = "OPERATOR_RUN"
    EXPORT = "EXPORT"
    BRIEFING = "BRIEFING"
    CLOSURE = "CLOSURE"
    ATTESTATION = "ATTESTATION"
    OTHER = "OTHER"


class ResearchOsReviewJournalEntry(BaseModel):
    schema_version: Literal["research_os_review_journal_entry/v1"] = "research_os_review_journal_entry/v1"
    entry_id: str = Field(min_length=1)
    entry_type: ResearchOsReviewJournalEntryType = ResearchOsReviewJournalEntryType.OTHER
    recorded_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_artifact_path: str = Field(min_length=1)
    source_file_sha256: str | None = None
    source_manifest_sha256: str | None = None
    source_schema_version: str | None = None
    source_status: str | None = None
    source_decision: str | None = None
    source_trust_banner: str | None = None
    source_id_hint: str | None = None
    summary: str = ""
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    @field_validator("recorded_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("recorded_at_utc must be timezone-aware")
        return v


class ResearchOsReviewJournal(BaseModel):
    schema_version: Literal["research_os_review_journal/v1"] = "research_os_review_journal/v1"
    journal_id: str = Field(min_length=1)
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifact_root: str = Field(min_length=1)
    status: ResearchOsReviewJournalStatus = ResearchOsReviewJournalStatus.EMPTY
    trust_banner: ResearchOsTrustBanner = ResearchOsTrustBanner.UNTRUSTED
    read_plane_only: bool = True
    no_live_trading: bool = True
    no_broker_orders: bool = True
    no_order_controls: bool = True
    no_profitability_claim: bool = True
    deployment_approval_unchanged: bool = True
    deployment_approved: bool = False
    entry_count: int = 0
    source_counts: dict[str, int] = Field(default_factory=dict)
    latest_decision_summary: dict[str, Any] = Field(default_factory=dict)
    entries: list[ResearchOsReviewJournalEntry] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    journal_spine_sha256: str = ""
    manifest_sha256: str = ""
    disclaimer: str = (
        "Research OS review journal is an offline read-plane review record over existing evidence. "
        "It is not the canonical validator ledger, does not mutate the ledger, does not approve deployment, "
        "does not authorize live trading or broker orders, and does not certify profitability."
    )

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


__all__ = [
    "ResearchOsReviewJournal",
    "ResearchOsReviewJournalEntry",
    "ResearchOsReviewJournalEntryType",
    "ResearchOsReviewJournalStatus",
]
