"""Governed provider historical snapshot contracts (research/paper; digest-linked; no secrets)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.provider_historical_data import ProviderHistoricalPitStatus


class ProviderHistoricalSnapshotStatus(str, Enum):
    OK = "OK"
    PENDING_KEY = "PENDING_KEY"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    ENDPOINT_CHANGED = "ENDPOINT_CHANGED"
    NON_JSON_BUT_VALID = "NON_JSON_BUT_VALID"
    BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"
    UNSUPPORTED_TIMEFRAME = "UNSUPPORTED_TIMEFRAME"
    FAILED_VALIDATION = "FAILED_VALIDATION"


class ProviderHistoricalSnapshotRequest(BaseModel):
    provider_id: str = Field(min_length=1)
    symbols: list[str] = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    start_utc: datetime
    end_utc: datetime
    as_of_utc: datetime
    access_type: str = "api"
    key_required: bool = True

    model_config = {"extra": "forbid"}

    @field_validator("start_utc", "end_utc", "as_of_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("datetimes must be timezone-aware")
        return v


class ProviderHistoricalSnapshotManifest(BaseModel):
    schema_version: Literal["provider_historical_snapshot_manifest/v1"] = "provider_historical_snapshot_manifest/v1"
    provider_id: str
    symbols: list[str] = Field(min_length=1)
    timeframe: str
    start_utc: datetime
    end_utc: datetime
    as_of_utc: datetime
    access_type: str = "api"
    key_required: bool = True
    key_configured: bool = False
    provider_status: ProviderHistoricalSnapshotStatus
    pit_status: ProviderHistoricalPitStatus
    license_scope: str = "freemium_research_only_unverified"
    trust_level: str = "unverified_freemium"
    retrieved_at_utc: datetime
    bars_path: str = ""
    bars_sha256: str = ""
    row_count: int = Field(ge=0)
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


class ProviderHistoricalSnapshotRun(BaseModel):
    schema_version: Literal["provider_historical_snapshot_run/v1"] = "provider_historical_snapshot_run/v1"
    generated_at_utc: datetime
    request: ProviderHistoricalSnapshotRequest
    snapshots: list[ProviderHistoricalSnapshotManifest] = Field(default_factory=list)
    network_used: bool = False
    fixture_path: str | None = None
    ok: bool = True
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    manifest_sha256: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class ProviderPaperLoopManifest(BaseModel):
    schema_version: Literal["provider_paper_loop_manifest/v1"] = "provider_paper_loop_manifest/v1"
    ok: bool = True
    run_id: str = ""
    generated_at_utc: datetime
    artifact_root: str = ""
    provider_snapshot: dict[str, Any] | None = None
    gauntlet_run: dict[str, Any] | None = None
    paper_tracking: dict[str, Any] | None = None
    lifecycle: dict[str, Any] | None = None
    promotion_packet: dict[str, Any] | None = None
    paper_broker: dict[str, Any] | None = None
    daily_tracking: dict[str, Any] | None = None
    portfolio: dict[str, Any] | None = None
    artifact_descriptor: dict[str, Any] | None = None
    replay_manifest_path: str | None = None
    replayable_offline: bool = True
    paper_only: bool = True
    live_trading_blocked: bool = True
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    digests: dict[str, str] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz_gen(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


__all__ = [
    "ProviderHistoricalSnapshotManifest",
    "ProviderHistoricalSnapshotRequest",
    "ProviderHistoricalSnapshotRun",
    "ProviderHistoricalSnapshotStatus",
    "ProviderPaperLoopManifest",
]
