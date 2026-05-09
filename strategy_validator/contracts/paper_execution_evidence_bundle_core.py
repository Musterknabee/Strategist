"""Paper execution evidence-bundle core contracts."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.paper_execution_core import *

class PaperExecutionEvidenceBundleSource(BaseModel):
    """Source artifact reference sealed into a paper execution evidence bundle."""

    schema_version: Literal["paper_execution_evidence_bundle_source/v1"] = "paper_execution_evidence_bundle_source/v1"
    stage: str
    tracking_id: str | None = None
    generated_at_utc: str | None = None
    artifact_path: str | None = None
    artifact_sha256: str | None = None
    status: str = "UNKNOWN"
    trusted: bool = False
    blocker_count: int = 0
    warning_count: int = 0

    model_config = {"extra": "forbid"}


class PaperExecutionEvidenceBundleArtifact(BaseModel):
    """Durable bundle sealing the current paper execution timeline.

    The bundle is an attestable review package only. It does not authorize a
    trade, submit an order, promote a strategy, or mutate the decision ledger.
    """

    schema_version: Literal["paper_execution_evidence_bundle/v1"] = "paper_execution_evidence_bundle/v1"
    generated_at_utc: datetime
    tracking_id: str | None = None
    paper_trading_only: bool = True
    live_trading_blocked: bool = True
    browser_orders_blocked: bool = True
    no_new_order_submitted: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    bundle_authority: Literal["CLI_EVIDENCE_ONLY"] = "CLI_EVIDENCE_ONLY"
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    bundle_status: Literal["SEALED", "SEALED_RESTRICTED", "SEALED_BLOCKED"] = "SEALED_RESTRICTED"
    timeline_sequence_status: Literal["EMPTY", "PARTIAL", "BLOCKED", "COMPLETE"] = "EMPTY"
    timeline_event_count: int = 0
    timeline_trusted_event_count: int = 0
    timeline_blocker_count: int = 0
    timeline_warning_count: int = 0
    source_artifact_count: int = 0
    missing_stages: list[str] = Field(default_factory=list)
    source_artifacts: list[PaperExecutionEvidenceBundleSource] = Field(default_factory=list)
    timeline_summary: PaperExecutionTimelineSummary = Field(default_factory=PaperExecutionTimelineSummary)
    timeline: list[PaperExecutionTimelineEntry] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    bundle_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _bundle_generated_at_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class PaperExecutionEvidenceBundleView(BaseModel):
    """Read-plane summary of a sealed paper execution evidence bundle."""

    schema_version: Literal["paper_execution_evidence_bundle_view/v1"] = "paper_execution_evidence_bundle_view/v1"
    tracking_id: str | None = None
    artifact_path: str
    bundle_sha256: str | None = None
    generated_at_utc: str | None = None
    trust_banner: Literal["TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"] = "TRUST_RESTRICTED"
    bundle_status: Literal["SEALED", "SEALED_RESTRICTED", "SEALED_BLOCKED", "UNKNOWN"] = "UNKNOWN"
    timeline_sequence_status: str = "EMPTY"
    timeline_event_count: int = 0
    timeline_trusted_event_count: int = 0
    timeline_blocker_count: int = 0
    source_artifact_count: int = 0
    missing_stages: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


__all__ = (
    "PaperExecutionEvidenceBundleSource",
    "PaperExecutionEvidenceBundleArtifact",
    "PaperExecutionEvidenceBundleView",
)
