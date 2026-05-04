"""Strategy graveyard and resurrection-rule UI contracts."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class StrategyGraveyardResurrectionRule(BaseModel):
    schema_version: Literal["strategy_graveyard_resurrection_rule/v1"] = "strategy_graveyard_resurrection_rule/v1"
    rule_id: str
    failure_reason: str
    condition: str
    required_evidence: list[str] = Field(default_factory=list)
    rationale: str = ""
    status: Literal["BLOCKING", "CONDITIONAL", "REVIEW"] = "CONDITIONAL"
    model_config = {"extra": "forbid"}


class StrategyGraveyardEntryView(BaseModel):
    schema_version: Literal["strategy_graveyard_entry_view/v1"] = "strategy_graveyard_entry_view/v1"
    strategy_id: str
    family_id: str
    status: str
    kill_reason: str = ""
    killed_at_utc: datetime | None = None
    failure_reasons: list[str] = Field(default_factory=list)
    resurrectability: Literal["CONDITIONAL_RESEARCH_RETRY", "HARD_BLOCKED_UNTIL_EVIDENCE", "DUPLICATE_SUPERSEDED", "OPERATOR_REVIEW_REQUIRED", "UNKNOWN"] = "UNKNOWN"
    resurrection_rules: list[StrategyGraveyardResurrectionRule] = Field(default_factory=list)
    hard_blockers: list[str] = Field(default_factory=list)
    advisory_notes: list[str] = Field(default_factory=list)
    source_record_sha256: str | None = None
    entry_sha256: str | None = None
    run_id: str | None = None
    batch_id: str | None = None
    tracking_id: str | None = None
    strategy_type: str | None = None
    universe: str | None = None
    timeframe: str | None = None
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    raw_entry: dict[str, Any] = Field(default_factory=dict)
    model_config = {"extra": "forbid"}

    @field_validator("killed_at_utc")
    @classmethod
    def _tz(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            raise ValueError("killed_at_utc must be timezone-aware")
        return v


class StrategyGraveyardSummary(BaseModel):
    schema_version: Literal["strategy_graveyard_summary/v1"] = "strategy_graveyard_summary/v1"
    entry_count: int = 0
    hard_blocked_count: int = 0
    conditional_retry_count: int = 0
    duplicate_superseded_count: int = 0
    operator_review_count: int = 0
    failure_reason_counts: dict[str, int] = Field(default_factory=dict)
    resurrectability_counts: dict[str, int] = Field(default_factory=dict)
    model_config = {"extra": "forbid"}


class StrategyGraveyardPayload(BaseModel):
    schema_version: Literal["ui_strategy_graveyard/v1"] = "ui_strategy_graveyard/v1"
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read_plane_only: bool = True
    no_live_trading: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    scan_root: str = ""
    index_path: str = ""
    degraded: list[str] = Field(default_factory=list)
    summary: StrategyGraveyardSummary = Field(default_factory=StrategyGraveyardSummary)
    entries: list[StrategyGraveyardEntryView] = Field(default_factory=list)
    disclaimer: str = "Strategy graveyard is advisory research memory only; resurrection rules do not approve promotion or execution."
    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz_generated(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


__all__ = ["StrategyGraveyardEntryView", "StrategyGraveyardPayload", "StrategyGraveyardResurrectionRule", "StrategyGraveyardSummary"]
