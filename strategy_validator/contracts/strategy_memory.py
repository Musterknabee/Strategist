"""Strategy memory / candidate graveyard contracts (research evidence only)."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class StrategyMemoryStatus(str, Enum):
    ACTIVE_RESEARCH = "ACTIVE_RESEARCH"
    PAPER_TRACKING = "PAPER_TRACKING"
    INCUBATING = "INCUBATING"
    PROMOTION_REVIEW_READY = "PROMOTION_REVIEW_READY"
    REJECTED = "REJECTED"
    KILLED = "KILLED"
    ARCHIVED = "ARCHIVED"
    DUPLICATE_VARIANT = "DUPLICATE_VARIANT"
    SUPERSEDED = "SUPERSEDED"


class StrategyFailureReason(str, Enum):
    DATA_QUALITY = "DATA_QUALITY"
    PIT = "PIT"
    EXECUTION_REALISM = "EXECUTION_REALISM"
    ROBUSTNESS = "ROBUSTNESS"
    PARAMETER_FRAGILITY = "PARAMETER_FRAGILITY"
    REGIME_FAILURE = "REGIME_FAILURE"
    PORTFOLIO_DUPLICATIVE = "PORTFOLIO_DUPLICATIVE"
    PAPER_DECAY = "PAPER_DECAY"
    KILL_RULE = "KILL_RULE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    OPERATOR_REJECTED = "OPERATOR_REJECTED"


class StrategyFamily(BaseModel):
    family_id: str = Field(min_length=1)
    strategy_type: str = Field(min_length=1)
    universe: str = Field(min_length=1)
    family_tags: list[str] = Field(default_factory=list)
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latest_strategy_id: str | None = None
    variant_count: int = 0

    model_config = {"extra": "forbid"}

    @field_validator("created_at_utc")
    @classmethod
    def _tz_created(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("created_at_utc must be timezone-aware")
        return v


class StrategyVariantLineage(BaseModel):
    strategy_id: str = Field(min_length=1)
    family_id: str = Field(min_length=1)
    parent_strategy_id: str | None = None
    supersedes_strategy_id: str | None = None
    lineage_tags: list[str] = Field(default_factory=list)
    variant_fingerprint: str = Field(default="")

    model_config = {"extra": "forbid"}


class StrategyMemoryRecord(BaseModel):
    schema_version: Literal["strategy_memory_record/v1"] = "strategy_memory_record/v1"
    strategy_id: str = Field(min_length=1)
    family_id: str = Field(min_length=1)
    status: StrategyMemoryStatus = StrategyMemoryStatus.ACTIVE_RESEARCH
    strategy_type: str = "unknown"
    universe: str = "unknown"
    timeframe: str = "unknown"
    params: dict[str, Any] = Field(default_factory=dict)
    data_plane: str = "UNKNOWN"
    provider_snapshot_manifest_sha256: str | None = None
    batch_id: str | None = None
    run_id: str | None = None
    tracking_id: str | None = None
    lifecycle_state: str | None = None
    failure_reasons: list[StrategyFailureReason] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    lineage: StrategyVariantLineage
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    record_sha256: str = ""
    disclaimer: str = "Research memory only; no live trading or profitability claim."

    model_config = {"extra": "forbid"}

    @field_validator("created_at_utc", "updated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        return v


class CandidateGraveyardEntry(BaseModel):
    schema_version: Literal["candidate_graveyard_entry/v1"] = "candidate_graveyard_entry/v1"
    strategy_id: str = Field(min_length=1)
    family_id: str = Field(min_length=1)
    status: StrategyMemoryStatus = StrategyMemoryStatus.KILLED
    failure_reasons: list[StrategyFailureReason] = Field(default_factory=list)
    kill_reason: str = ""
    killed_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_record_sha256: str | None = None
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    entry_sha256: str = ""
    disclaimer: str = "Candidate graveyard entry; research memory only, no live trading."

    model_config = {"extra": "forbid"}

    @field_validator("killed_at_utc")
    @classmethod
    def _tz_killed(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("killed_at_utc must be timezone-aware")
        return v


class StrategySimilarityWarning(BaseModel):
    schema_version: Literal["strategy_similarity_warning/v1"] = "strategy_similarity_warning/v1"
    strategy_id: str = Field(min_length=1)
    similar_strategy_id: str = Field(min_length=1)
    family_id: str = Field(min_length=1)
    similarity_basis: list[str] = Field(default_factory=list)
    severity: Literal["INFO", "WARNING", "BLOCKER"] = "WARNING"
    warning: str = "Possible duplicate variant; review before spending more research budget."

    model_config = {"extra": "forbid"}


class StrategyMemoryIndex(BaseModel):
    schema_version: Literal["strategy_memory_index/v1"] = "strategy_memory_index/v1"
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active_count: int = 0
    killed_count: int = 0
    rejected_count: int = 0
    duplicate_variant_count: int = 0
    family_count: int = 0
    top_failure_reasons: dict[str, int] = Field(default_factory=dict)
    families: list[StrategyFamily] = Field(default_factory=list)
    recent_graveyard_entries: list[CandidateGraveyardEntry] = Field(default_factory=list)
    duplicate_variant_warnings: list[StrategySimilarityWarning] = Field(default_factory=list)
    memory_records: list[StrategyMemoryRecord] = Field(default_factory=list)
    index_sha256: str = ""
    disclaimer: str = "Strategy memory is research/governance evidence only; it does not certify profitability."

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz_generated(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


__all__ = [
    "CandidateGraveyardEntry",
    "StrategyFailureReason",
    "StrategyFamily",
    "StrategyMemoryIndex",
    "StrategyMemoryRecord",
    "StrategyMemoryStatus",
    "StrategySimilarityWarning",
    "StrategyVariantLineage",
]
