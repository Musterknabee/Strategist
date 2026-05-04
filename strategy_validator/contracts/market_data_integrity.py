"""Market-data integrity contracts for PIT research/paper evidence."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class MarketDataIntegrityGateStatus(str, Enum):
    PROVEN = "PROVEN"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TradingCalendarCoverage(BaseModel):
    expected_trading_days: int = 0
    observed_trading_days: int = 0
    missing_trading_days: int = 0
    missing_date_ratio: float = 0.0
    calendar_status: MarketDataIntegrityGateStatus = MarketDataIntegrityGateStatus.NOT_APPLICABLE

    model_config = {"extra": "forbid"}


class CorporateActionWarning(BaseModel):
    symbol: str
    timestamp_utc: datetime | None = None
    warning_code: str
    detail: str

    model_config = {"extra": "forbid"}

    @field_validator("timestamp_utc")
    @classmethod
    def _tz(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            raise ValueError("timestamp_utc must be timezone-aware")
        return v


class SurvivorshipWarning(BaseModel):
    symbol: str
    warning_code: str
    detail: str

    model_config = {"extra": "forbid"}


class SymbolContinuityCheck(BaseModel):
    symbol: str
    first_seen_utc: datetime | None = None
    last_seen_utc: datetime | None = None
    observed_days: int = 0
    missing_days: int = 0
    status: MarketDataIntegrityGateStatus = MarketDataIntegrityGateStatus.NOT_APPLICABLE

    model_config = {"extra": "forbid"}

    @field_validator("first_seen_utc", "last_seen_utc")
    @classmethod
    def _tz(cls, v: datetime | None) -> datetime | None:
        if v is not None and v.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        return v


class PriceDiscontinuityCheck(BaseModel):
    symbol: str
    timestamp_utc: datetime
    previous_close: float
    close: float
    absolute_return: float
    warning_code: str

    model_config = {"extra": "forbid"}

    @field_validator("timestamp_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamp_utc must be timezone-aware")
        return v


class MarketDataIntegrityResult(BaseModel):
    schema_version: Literal["market_data_integrity_result/v1"] = "market_data_integrity_result/v1"
    strategy_id: str
    batch_id: str
    run_id: str
    provider_id: str = "unknown"
    license_scope: str = "unknown"
    trust_level: str = "unknown"
    adjusted_status: Literal["ADJUSTED", "UNADJUSTED", "UNKNOWN"] = "UNKNOWN"
    as_of_utc: datetime
    row_count: int = 0
    symbol_count: int = 0
    stale_last_bar_hours: float | None = None
    trading_calendar_coverage: TradingCalendarCoverage = Field(default_factory=TradingCalendarCoverage)
    corporate_action_warnings: list[CorporateActionWarning] = Field(default_factory=list)
    survivorship_warnings: list[SurvivorshipWarning] = Field(default_factory=list)
    symbol_continuity_checks: list[SymbolContinuityCheck] = Field(default_factory=list)
    price_discontinuity_checks: list[PriceDiscontinuityCheck] = Field(default_factory=list)
    duplicate_vendor_record_count: int = 0
    timezone_session_warnings: list[str] = Field(default_factory=list)
    benchmark_calendar_mismatch: bool = False
    gate_status: MarketDataIntegrityGateStatus = MarketDataIntegrityGateStatus.NOT_APPLICABLE
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    evidence_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("as_of_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("as_of_utc must be timezone-aware")
        return v


__all__ = [
    "CorporateActionWarning",
    "MarketDataIntegrityGateStatus",
    "MarketDataIntegrityResult",
    "PriceDiscontinuityCheck",
    "SurvivorshipWarning",
    "SymbolContinuityCheck",
    "TradingCalendarCoverage",
]
