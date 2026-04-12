"""
Typed market-data snapshot contracts for liquidity and borrow realism.

These contracts provide the lawful input path for execution realism.
Each snapshot carries a source_mode that certifies its provenance:
  - LIVE:       from a real-time or near-real-time market-data feed
  - SNAPSHOT:   from a replayable, point-in-time preserved data store
  - PROVISIONAL: from an opaque payload assertion (no feed backing)

No promotion-grade decision should be liquidity-source-ambiguous or
borrow-source-ambiguous.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Literal, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

SourceMode = Literal["LIVE", "SNAPSHOT", "PROVISIONAL"]
ProviderStatus = Literal["SUCCESS", "ERROR", "TIMEOUT", "STALE", "MISSING", "NOT_CONFIGURED", "CIRCUIT_OPEN"]

VendorOutageCircuitPolicy = Literal["STANDARD", "LENIENT_TRANSIENT_5XX"]


class ProviderResiliencePolicy(BaseModel):
    """Typed resilience policy for provider-backed lookup flows."""
    max_retries: int = Field(default=0, ge=0)
    retry_backoff_ms: int = Field(default=0, ge=0, le=60_000)
    circuit_breaker_threshold: int = Field(default=2, ge=1)
    circuit_cooldown_seconds: int = Field(default=300, ge=1)
    vendor_outage_circuit_policy: VendorOutageCircuitPolicy = "STANDARD"
    """LENIENT_TRANSIENT_5XX: HTTP 5xx class errors do not advance the circuit counter (vendor blips)."""

    model_config = {"extra": "forbid"}


class ProviderLookupMetadata(BaseModel):
    """Typed result metadata for a single provider-backed lookup."""
    provider_id: str = "unknown"
    feed_kind: Literal["liquidity", "borrow"] = "liquidity"
    status: ProviderStatus = "NOT_CONFIGURED"
    attempts: int = Field(default=0, ge=0)
    retry_count: int = Field(default=0, ge=0)
    error_summary: Optional[str] = None
    failure_domain: Optional[str] = None
    failure_code: Optional[str] = None
    circuit_state: Literal["CLOSED", "OPEN"] = "CLOSED"
    lookup_time_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"extra": "forbid"}

class FreshnessResult(BaseModel):
    """
    Lawful evaluation of market-data freshness against policy thresholds.
    """
    status: Literal["FRESH", "STALE", "MISSING", "ERROR", "UNKNOWN"] = "UNKNOWN"
    age_seconds: float = 0.0
    threshold_seconds: float = 0.0
    """Effective max-age threshold (seconds) used for this evaluation."""
    applied_threshold_seconds: Optional[float] = None
    """Same as threshold_seconds when set by evaluator; for audit alignment."""
    market_hours_law: Optional[str] = None
    """DISABLED | US_RTH_OPEN | US_RTH_CLOSED — session context for LIVE age law."""
    as_of_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def is_acceptable(self) -> bool:
        return self.status == "FRESH"

@runtime_checkable
class LiquidityFeed(Protocol):
    """Forensic-grade liquidity data provider."""
    def lookup(self, asset_id: str, timestamp: datetime) -> Optional[LiquiditySnapshot]: ...

@runtime_checkable
class BorrowFeed(Protocol):
    """Forensic-grade borrow/shortability data provider."""
    def lookup(self, asset_id: str, timestamp: datetime) -> Optional[BorrowSnapshot]: ...

@runtime_checkable
class MarketDataProvider(Protocol):
    """
    Lawful market-data source interface.
    Provides standardized lookup access to liquidity and borrow snaps.
    """
    provider_id: str
    def provide_liquidity(self, asset_id: str, timestamp: datetime) -> Optional[LiquiditySnapshot]: ...
    def provide_borrow(self, asset_id: str, timestamp: datetime) -> Optional[BorrowSnapshot]: ...


class LiquiditySnapshot(BaseModel):
    """
    Point-in-time liquidity snapshot for a single asset.

    Structural fields:
      - adv_notional: average daily volume in notional units
      - spread_bps: quoted / effective spread in basis points

    Provenance fields:
      - source_mode: LIVE | SNAPSHOT | PROVISIONAL
      - source_id: identifier of the feed or fixture that produced this snapshot
      - snapshot_hash: deterministic fingerprint of the snapshot content

    Honesty guarantees:
      - If source_mode is LIVE or SNAPSHOT, source_id must be non-empty.
      - If source_mode is PROVISIONAL, the snapshot cannot masquerade as
        feed-backed; downstream consumers must degrade accordingly.
      - snapshot_hash is computed deterministically from the snapshot's
        structural fields and timestamp.
    """
    asset_id: str = Field(min_length=1)
    snapshot_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    adv_notional: float = Field(default=0.0, ge=0.0)
    spread_bps: float = Field(default=0.0, ge=0.0)
    volume_proxy: float = Field(default=0.0, ge=0.0)
    """Secondary volume proxy when ADV is unavailable."""

    source_id: str = ""
    source_mode: SourceMode = "PROVISIONAL"
    snapshot_hash: Optional[str] = None

    model_config = {"extra": "forbid"}

    def compute_fingerprint(self) -> str:
        """Deterministic hash of structural content for provenance sealing."""
        import json
        canonical = json.dumps({
            "asset_id": self.asset_id,
            "snapshot_time": self.snapshot_time.isoformat(),
            "adv_notional": self.adv_notional,
            "spread_bps": self.spread_bps,
            "volume_proxy": self.volume_proxy,
            "source_id": self.source_id,
            "source_mode": self.source_mode,
        }, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def model_post_init(self, __context) -> None:
        if self.snapshot_hash is None:
            self.snapshot_hash = self.compute_fingerprint()
        if self.source_mode in ("LIVE", "SNAPSHOT") and not self.source_id:
            raise ValueError(
                f"LiquiditySnapshot with source_mode={self.source_mode} requires a non-empty source_id."
            )


class BorrowSnapshot(BaseModel):
    """
    Point-in-time borrow-availability snapshot for a single asset.

    Structural fields:
      - borrow_available: whether shares are available to borrow
      - borrow_cost_bps: annualized borrow fee in basis points
      - locate_required: whether a pre-borrow locate is required

    Provenance fields:
      - source_mode: LIVE | SNAPSHOT | PROVISIONAL
      - source_id: identifier of the feed or fixture that produced this snapshot
      - snapshot_hash: deterministic fingerprint of the snapshot content

    Honesty guarantees:
      - If source_mode is LIVE or SNAPSHOT, source_id must be non-empty.
      - If source_mode is PROVISIONAL, the snapshot cannot masquerade as
        feed-backed; downstream consumers must degrade accordingly.
      - snapshot_hash is computed deterministically from the snapshot's
        structural fields and timestamp.
    """
    asset_id: str = Field(min_length=1)
    snapshot_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    borrow_available: bool = True
    borrow_cost_bps: float = Field(default=0.0, ge=0.0)
    locate_required: Optional[bool] = None

    source_id: str = ""
    source_mode: SourceMode = "PROVISIONAL"
    snapshot_hash: Optional[str] = None

    model_config = {"extra": "forbid"}

    def compute_fingerprint(self) -> str:
        """Deterministic hash of structural content for provenance sealing."""
        import json
        canonical = json.dumps({
            "asset_id": self.asset_id,
            "snapshot_time": self.snapshot_time.isoformat(),
            "borrow_available": self.borrow_available,
            "borrow_cost_bps": self.borrow_cost_bps,
            "locate_required": self.locate_required,
            "source_id": self.source_id,
            "source_mode": self.source_mode,
        }, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def model_post_init(self, __context) -> None:
        if self.snapshot_hash is None:
            self.snapshot_hash = self.compute_fingerprint()
        if self.source_mode in ("LIVE", "SNAPSHOT") and not self.source_id:
            raise ValueError(
                f"BorrowSnapshot with source_mode={self.source_mode} requires a non-empty source_id."
            )
