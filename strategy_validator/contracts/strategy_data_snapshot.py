"""Contracts for PIT-aware strategy data snapshots (local bars; research/paper only)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class StrategyPitSnapshotStatus(str, Enum):
    PIT_VERIFIED = "PIT_VERIFIED"
    BEST_EFFORT_AS_OF = "BEST_EFFORT_AS_OF"
    MISSING_RELEASE_TIMESTAMPS = "MISSING_RELEASE_TIMESTAMPS"
    SYNTHETIC_DEMO = "SYNTHETIC_DEMO"
    BLOCKED_NO_PIT = "BLOCKED_NO_PIT"


class StrategyDataSourceClassification(str, Enum):
    LOCAL_GOVERNED_BARS = "LOCAL_GOVERNED_BARS"
    SYNTHETIC_DETERMINISTIC = "SYNTHETIC_DETERMINISTIC"
    UNAVAILABLE = "UNAVAILABLE"


class StrategyBar(BaseModel):
    symbol: str = Field(min_length=1)
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


class StrategyDataRequirement(BaseModel):
    """Future hook for declarative data needs; optional for local bars path."""

    requirement_id: str = Field(min_length=1)
    kind: Literal["local_bars", "provider_panel"] = "local_bars"
    notes: str = ""

    model_config = {"extra": "forbid"}


class StrategyDataSnapshot(BaseModel):
    """In-memory slice description (serializable for manifests)."""

    strategy_id: str
    batch_id: str
    universe: str
    timeframe: str
    as_of_utc: datetime
    lookback_start_utc: datetime
    lookback_end_utc: datetime
    provider_id: str = "local_file"
    source_classification: StrategyDataSourceClassification = StrategyDataSourceClassification.LOCAL_GOVERNED_BARS
    pit_status: StrategyPitSnapshotStatus
    retrieved_at_utc: datetime
    published_at_utc: datetime | None = None
    bars_path: str
    bars_sha256: str
    row_count: int = Field(ge=0)
    symbol_count: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    may_gate_live_promotion: bool = False

    model_config = {"extra": "forbid"}

    @field_validator("as_of_utc", "lookback_start_utc", "lookback_end_utc", "retrieved_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")
        return v


class StrategyDataSnapshotManifest(BaseModel):
    schema_version: Literal["strategy_data_snapshot_manifest/v1"] = "strategy_data_snapshot_manifest/v1"
    strategy_id: str
    batch_id: str
    run_id: str
    snapshot: StrategyDataSnapshot
    compute_backend: str = "cpu"
    extra: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class LocalBarsDataSourceConfig(BaseModel):
    """Declared in batch spec: load historical bars from a repo-local file."""

    kind: Literal["local_bars"] = "local_bars"
    path: str = Field(min_length=1)
    pit_status: StrategyPitSnapshotStatus = StrategyPitSnapshotStatus.BEST_EFFORT_AS_OF

    model_config = {"extra": "forbid"}


def snapshot_data_gates_promotion(snapshot: StrategyDataSnapshot) -> bool:
    """True when this snapshot alone should gate (block) live promotion."""

    if snapshot.blockers:
        return True
    if snapshot.pit_status in (StrategyPitSnapshotStatus.SYNTHETIC_DEMO, StrategyPitSnapshotStatus.BLOCKED_NO_PIT):
        return True
    if snapshot.pit_status == StrategyPitSnapshotStatus.PIT_VERIFIED and not snapshot.warnings:
        return False
    return True


def snapshot_promotion_eligible_data_plane(snapshot: StrategyDataSnapshot) -> bool:
    """Data-plane-only eligibility: verified PIT, no blockers, no warnings."""

    return not snapshot_data_gates_promotion(snapshot) and snapshot.pit_status == StrategyPitSnapshotStatus.PIT_VERIFIED


__all__ = [
    "LocalBarsDataSourceConfig",
    "StrategyBar",
    "StrategyDataRequirement",
    "StrategyDataSnapshot",
    "StrategyDataSnapshotManifest",
    "StrategyDataSourceClassification",
    "StrategyPitSnapshotStatus",
    "snapshot_data_gates_promotion",
    "snapshot_promotion_eligible_data_plane",
]
