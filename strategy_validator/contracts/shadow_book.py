"""Paper-only Shadow Book contracts (no broker orders; research evidence only)."""
from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ShadowBookStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    FROZEN_BY_RULE = "FROZEN_BY_RULE"
    KILLED = "KILLED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ShadowBookAllocation(BaseModel):
    strategy_id: str = Field(min_length=1)
    target_weight: float
    notional: float = 0.0
    source: str = "manual_or_allocation_artifact"
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ShadowBookPosition(BaseModel):
    strategy_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    quantity: float = 0.0
    avg_price: float = 0.0
    last_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    weight: float = 0.0

    model_config = {"extra": "forbid"}


class ShadowBookFill(BaseModel):
    fill_id: str = Field(min_length=1)
    strategy_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    timestamp_utc: datetime
    side: Literal["BUY", "SELL"] = "BUY"
    quantity: float
    price: float
    notional: float
    simulated: bool = True
    no_broker_order: bool = True

    model_config = {"extra": "forbid"}

    @field_validator("timestamp_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamp_utc must be timezone-aware")
        return v


class ShadowBookRiskSummary(BaseModel):
    schema_version: Literal["shadow_book_risk_summary/v1"] = "shadow_book_risk_summary/v1"
    book_id: str = Field(min_length=1)
    as_of_date: date
    status: ShadowBookStatus = ShadowBookStatus.ACTIVE
    gross_exposure: float = 0.0
    net_liquidation_value: float = 0.0
    cash: float = 0.0
    max_single_strategy_weight: float = 0.0
    max_drawdown: float = 0.0
    correlated_cluster_exposure: float = 0.0
    risk_flags: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    risk_sha256: str = ""

    model_config = {"extra": "forbid"}


class ShadowBookDailySnapshot(BaseModel):
    schema_version: Literal["shadow_book_daily_snapshot/v1"] = "shadow_book_daily_snapshot/v1"
    book_id: str = Field(min_length=1)
    as_of_date: date
    status: ShadowBookStatus = ShadowBookStatus.ACTIVE
    positions: list[ShadowBookPosition] = Field(default_factory=list)
    cash: float = 0.0
    net_liquidation_value: float = 0.0
    daily_pnl: float = 0.0
    cumulative_pnl: float = 0.0
    drawdown: float = 0.0
    risk_summary: ShadowBookRiskSummary | None = None
    snapshot_sha256: str = ""

    model_config = {"extra": "forbid"}


class ShadowBookEvent(BaseModel):
    schema_version: Literal["shadow_book_event/v1"] = "shadow_book_event/v1"
    event_id: str = Field(min_length=1)
    book_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    severity: Literal["INFO", "WARNING", "BLOCKER"] = "INFO"
    message: str = ""
    refs: list[dict[str, Any]] = Field(default_factory=list)
    event_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("created_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("created_at_utc must be timezone-aware")
        return v


class ShadowBook(BaseModel):
    schema_version: Literal["shadow_book_manifest/v1"] = "shadow_book_manifest/v1"
    book_id: str = Field(min_length=1)
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: ShadowBookStatus = ShadowBookStatus.ACTIVE
    starting_capital: float = Field(default=100_000.0, gt=0)
    cash: float = 100_000.0
    allocations: list[ShadowBookAllocation] = Field(default_factory=list)
    latest_snapshot_path: str | None = None
    latest_risk_summary_path: str | None = None
    event_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    no_live_trading: bool = True
    no_broker_orders: bool = True
    disclaimer: str = "Paper-only shadow book; simulated fills only; no profitability or live-readiness claim."
    manifest_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("created_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("created_at_utc must be timezone-aware")
        return v


__all__ = [
    "ShadowBook",
    "ShadowBookAllocation",
    "ShadowBookDailySnapshot",
    "ShadowBookEvent",
    "ShadowBookFill",
    "ShadowBookPosition",
    "ShadowBookRiskSummary",
    "ShadowBookStatus",
]
