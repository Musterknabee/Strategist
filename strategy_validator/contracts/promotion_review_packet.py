"""Promotion review packet (human review evidence only; not live approval)."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class PromotionReviewRecommendation(str, Enum):
    DO_NOT_PROMOTE = "DO_NOT_PROMOTE"
    REVIEW_FOR_PAPER_EXTENSION = "REVIEW_FOR_PAPER_EXTENSION"
    READY_FOR_HUMAN_REVIEW = "READY_FOR_HUMAN_REVIEW"


class PromotionReviewEvidenceRef(BaseModel):
    ref_kind: str = Field(min_length=1)
    artifact_path: str = ""
    sha256: str | None = None

    model_config = {"extra": "forbid"}


class PromotionReviewChecklist(BaseModel):
    has_manifest: bool = False
    has_scorecard: bool = False
    has_lifecycle_assessment: bool = False
    has_gauntlet_scorecard_ref: bool = False
    has_evidence_manifest_ref: bool = False

    model_config = {"extra": "forbid"}


class PromotionReviewDecisionRecommendation(BaseModel):
    recommendation: PromotionReviewRecommendation
    rationale: str = ""

    model_config = {"extra": "forbid"}


class PromotionReviewPacket(BaseModel):
    schema_version: Literal["promotion_review_packet/v1"] = "promotion_review_packet/v1"
    packet_id: str
    tracking_id: str
    strategy_id: str
    batch_id: str
    run_id: str = ""
    generated_at_utc: datetime
    candidate_lifecycle_state: str
    gauntlet_summary: dict[str, Any] = Field(default_factory=dict)
    paper_tracking_summary: dict[str, Any] = Field(default_factory=dict)
    kill_rule_summary: dict[str, Any] = Field(default_factory=dict)
    execution_realism_summary: dict[str, Any] = Field(default_factory=dict)
    robustness_summary: dict[str, Any] = Field(default_factory=dict)
    portfolio_correlation_summary: dict[str, Any] = Field(default_factory=dict)
    provider_data_summary: dict[str, Any] = Field(default_factory=dict)
    known_risks: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence_refs: list[PromotionReviewEvidenceRef] = Field(default_factory=list)
    checklist: PromotionReviewChecklist = Field(default_factory=PromotionReviewChecklist)
    recommendation: PromotionReviewDecisionRecommendation
    packet_sha256: str = ""
    human_review_only_disclaimer: str = (
        "This packet supports human promotion review only. It does not approve live trading, "
        "broker execution, or deployment."
    )

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


__all__ = [
    "PromotionReviewChecklist",
    "PromotionReviewDecisionRecommendation",
    "PromotionReviewEvidenceRef",
    "PromotionReviewPacket",
    "PromotionReviewRecommendation",
]
