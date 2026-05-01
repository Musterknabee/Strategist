"""Contracts for optional provider historical bar ingestion (research/paper only)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ProviderHistoricalPitStatus(str, Enum):
    PIT_VERIFIED = "PIT_VERIFIED"
    BEST_EFFORT_AS_OF = "BEST_EFFORT_AS_OF"
    MISSING_RELEASE_TIMESTAMPS = "MISSING_RELEASE_TIMESTAMPS"
    BLOCKED_PROVIDER_UNAVAILABLE = "BLOCKED_PROVIDER_UNAVAILABLE"


class ProviderIngestionRuntimeStatus(str, Enum):
    OK = "OK"
    PENDING_KEY = "PENDING_KEY"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    DEGRADED = "DEGRADED"


class HistoricalBar(BaseModel):
    timestamp_utc: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    model_config = {"extra": "forbid"}

    @field_validator("timestamp_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamp_utc must be timezone-aware")
        return v


class HistoricalDataRequest(BaseModel):
    provider_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    timeframe: str = Field(min_length=1, description="e.g. 1d")
    start_utc: datetime
    end_utc: datetime
    as_of_utc: datetime

    model_config = {"extra": "forbid"}

    @field_validator("start_utc", "end_utc", "as_of_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("datetimes must be timezone-aware")
        return v


class HistoricalDataProviderResult(BaseModel):
    """Immediate fetch outcome before snapshot persistence."""

    provider_id: str
    provider_status: ProviderIngestionRuntimeStatus
    pit_status: ProviderHistoricalPitStatus
    bars: list[HistoricalBar] = Field(default_factory=list)
    retrieved_at_utc: datetime
    published_at_utc: datetime | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    license_scope: str = "freemium_research_only_unverified"

    model_config = {"extra": "forbid"}

    @field_validator("retrieved_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("retrieved_at_utc must be timezone-aware")
        return v


class ProviderDataIngestionManifest(BaseModel):
    schema_version: Literal["provider_data_ingestion_manifest/v1"] = "provider_data_ingestion_manifest/v1"
    provider_id: str
    symbol: str
    timeframe: str
    start_utc: datetime
    end_utc: datetime
    as_of_utc: datetime
    retrieved_at_utc: datetime
    published_at_utc: datetime | None = None
    pit_status: ProviderHistoricalPitStatus
    bars_path: str
    bars_sha256: str
    row_count: int = Field(ge=0)
    license_scope: str = "freemium_research_only_unverified"
    provider_status: ProviderIngestionRuntimeStatus
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    manifest_sha256: str = ""
    extra: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    @field_validator("start_utc", "end_utc", "as_of_utc", "retrieved_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("datetimes must be timezone-aware")
        return v


__all__ = [
    "HistoricalBar",
    "HistoricalDataProviderResult",
    "HistoricalDataRequest",
    "ProviderDataIngestionManifest",
    "ProviderHistoricalPitStatus",
    "ProviderIngestionRuntimeStatus",
]
