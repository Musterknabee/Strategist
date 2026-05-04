"""Governed candidate lifecycle contracts (research / paper evidence only; no ledger authority)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class CandidateLifecycleState(str, Enum):
    RESEARCH_CANDIDATE = "RESEARCH_CANDIDATE"
    PAPER_TRACKING = "PAPER_TRACKING"
    WATCHLIST = "WATCHLIST"
    DEGRADED = "DEGRADED"
    KILL_CANDIDATE = "KILL_CANDIDATE"
    KILLED_BY_RULE = "KILLED_BY_RULE"
    PROMOTION_REVIEW_READY = "PROMOTION_REVIEW_READY"
    REJECTED = "REJECTED"


class CandidateLifecycleTransitionReason(str, Enum):
    INITIAL = "INITIAL"
    SCORECARD_UPDATED = "SCORECARD_UPDATED"
    GOVERNANCE_UPDATE = "GOVERNANCE_UPDATE"
    KILL_RULE_TRIGGERED = "KILL_RULE_TRIGGERED"
    MANUAL_REJECT = "MANUAL_REJECT"
    PROMOTION_GATE = "PROMOTION_GATE"
    DAILY_RUN = "DAILY_RUN"


class CandidateLifecycleEvidenceRef(BaseModel):
    ref_kind: str = Field(min_length=1)
    artifact_path: str = ""
    sha256: str | None = None
    note: str = ""

    model_config = {"extra": "forbid"}


class CandidateLifecycleAssessment(BaseModel):
    """Artifact-backed lifecycle projection (read-plane / CLI; not deployment approval)."""

    schema_version: Literal["lifecycle_assessment/v1"] = "lifecycle_assessment/v1"
    tracking_id: str
    strategy_id: str
    batch_id: str
    run_id: str = ""
    current_state: CandidateLifecycleState
    recommended_state: CandidateLifecycleState
    previous_state: CandidateLifecycleState | None = None
    transition_reason: CandidateLifecycleTransitionReason = CandidateLifecycleTransitionReason.SCORECARD_UPDATED
    assessed_at_utc: datetime
    gauntlet_status_summary: dict[str, Any] = Field(default_factory=dict)
    paper_tracking_scorecard_digest: str | None = None
    kill_rule_status: str = "NONE"
    duplicative_portfolio_warning: bool = False
    synthetic_demo: bool = False
    promotion_review_ready: bool = False
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence_refs: list[CandidateLifecycleEvidenceRef] = Field(default_factory=list)
    basis_summary: str = ""
    manifest_sha256: str = ""
    promotion_review_disclaimer: str = (
        "PROMOTION_REVIEW_READY is an evidence gate only — not live trading approval or deployment promotion."
    )
    lifecycle_assessment_sha256: str = ""

    model_config = {"extra": "forbid"}

    @property
    def state(self) -> CandidateLifecycleState:
        """Backward-compatible alias for ``current_state``."""
        return self.current_state

    @field_validator("assessed_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("assessed_at_utc must be timezone-aware")
        return v


__all__ = [
    "CandidateLifecycleAssessment",
    "CandidateLifecycleEvidenceRef",
    "CandidateLifecycleState",
    "CandidateLifecycleTransitionReason",
]
