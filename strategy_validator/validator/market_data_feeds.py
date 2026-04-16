"""
Typed adapter seams for market-data feeds (liquidity and borrow).

Design:
  - Abstract repository interfaces define the lawful retrieval contract.
  - A snapshot-store implementation provides replayable, PIT-aware access
    from an in-memory list of typed snapshots.
  - A provisional-fallback implementation produces PROVISIONAL-labeled
    snapshots from bare evidence-payload values, never masquerading as
    feed-backed.
  - Provider-backed adapters add deterministic retry and circuit-breaker
    behavior without hiding source degradation from provenance.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Iterable, List, Literal, Optional

if TYPE_CHECKING:
    from strategy_validator.core.config import RuntimePolicy

from strategy_validator.contracts.market_data import (
    BorrowSnapshot,
    LiquiditySnapshot,
    LiquidityFeed as LiquidityFeedProtocol,
    BorrowFeed as BorrowFeedProtocol,
    MarketDataProvider,
    ProviderLookupMetadata,
    ProviderResiliencePolicy,
)
from strategy_validator.contracts.vendor_runtime import classify_vendor_failure_detail


def _transient_vendor_5xx_summary(summary: str) -> bool:
    """True when error text indicates an HTTP 5xx class vendor outage (transient)."""
    low = (summary or "").lower()
    return any(
        tok in low
        for tok in (
            "alpaca_http_5",
            "alpaca_trading_http_5",
            "http_json_http_5",
            "http_502",
            "http_503",
            "http_504",
        )
    )


def provider_resilience_from_runtime_policy(policy: "RuntimePolicy") -> ProviderResiliencePolicy:
    """Map ``RuntimePolicy`` market-data fields to a ``ProviderResiliencePolicy`` for feeds."""
    return ProviderResiliencePolicy(
        max_retries=policy.market_data_provider_max_retries,
        retry_backoff_ms=0,
        circuit_breaker_threshold=policy.market_data_circuit_breaker_threshold,
        circuit_cooldown_seconds=policy.market_data_circuit_cooldown_seconds,
        vendor_outage_circuit_policy=policy.market_data_vendor_outage_circuit_policy,
    )


class _ProviderBackedFeedBase:
    def __init__(
        self,
        provider: MarketDataProvider,
        policy: Optional[ProviderResiliencePolicy] = None,
        *,
        failure_feed_kind: Literal["liquidity", "borrow"] = "liquidity",
    ):
        self.provider = provider
        self.policy = policy or ProviderResiliencePolicy()
        self._failure_feed_kind: Literal["liquidity", "borrow"] = failure_feed_kind
        self._consecutive_failures = 0
        self._circuit_open_until: Optional[datetime] = None
        self.last_lookup_metadata = ProviderLookupMetadata(
            provider_id=getattr(provider, "provider_id", "unknown"),
            feed_kind=failure_feed_kind,
        )

    def _begin_metadata(self, as_of: datetime) -> ProviderLookupMetadata:
        return ProviderLookupMetadata(
            provider_id=getattr(self.provider, "provider_id", "unknown"),
            feed_kind=self._failure_feed_kind,
            lookup_time_utc=as_of,
        )

    def _circuit_open(self, as_of: datetime) -> bool:
        return self._circuit_open_until is not None and as_of < self._circuit_open_until

    def _trip_circuit(self, as_of: datetime) -> None:
        self._circuit_open_until = as_of + timedelta(seconds=self.policy.circuit_cooldown_seconds)

    def _mark_success(self, meta: ProviderLookupMetadata) -> ProviderLookupMetadata:
        self._consecutive_failures = 0
        self._circuit_open_until = None
        meta.status = "SUCCESS"
        meta.circuit_state = "CLOSED"
        self.last_lookup_metadata = meta
        return meta

    def _mark_failure(self, meta: ProviderLookupMetadata, *, status: str, error_summary: str) -> ProviderLookupMetadata:
        transient_5xx = (
            self.policy.vendor_outage_circuit_policy == "LENIENT_TRANSIENT_5XX"
            and _transient_vendor_5xx_summary(error_summary)
        )
        if not transient_5xx:
            self._consecutive_failures += 1
        if self._consecutive_failures >= self.policy.circuit_breaker_threshold:
            self._trip_circuit(meta.lookup_time_utc)
            meta.circuit_state = "OPEN"
        else:
            meta.circuit_state = "CLOSED"
        meta.status = status  # type: ignore[assignment]
        meta.error_summary = error_summary
        ev = classify_vendor_failure_detail(
            error_summary,
            feed_kind=self._failure_feed_kind,
            provider_id=meta.provider_id,
        )
        meta.failure_domain = ev.domain
        meta.failure_code = ev.code
        self.last_lookup_metadata = meta
        return meta

    def _execute_with_resilience(self, *, as_of: datetime, fetcher):
        meta = self._begin_metadata(as_of)
        if self._circuit_open(as_of):
            meta.status = "CIRCUIT_OPEN"
            meta.circuit_state = "OPEN"
            meta.error_summary = "CIRCUIT_OPEN"
            ev = classify_vendor_failure_detail(
                "CIRCUIT_OPEN",
                feed_kind=self._failure_feed_kind,
                provider_id=meta.provider_id,
            )
            meta.failure_domain = ev.domain
            meta.failure_code = ev.code
            self.last_lookup_metadata = meta
            return None

        last_error = None
        attempts = self.policy.max_retries + 1
        for attempt in range(1, attempts + 1):
            meta.attempts = attempt
            meta.retry_count = attempt - 1
            try:
                snap = fetcher()
            except TimeoutError as exc:
                last_error = exc
                if attempt == attempts:
                    self._mark_failure(meta, status="TIMEOUT", error_summary=str(exc) or exc.__class__.__name__)
                    return None
                if self.policy.retry_backoff_ms:
                    time.sleep(self.policy.retry_backoff_ms / 1000.0)
                continue
            except Exception as exc:  # noqa: BLE001 - provenance requires exact failure capture
                last_error = exc
                if attempt == attempts:
                    self._mark_failure(meta, status="ERROR", error_summary=str(exc) or exc.__class__.__name__)
                    return None
                if self.policy.retry_backoff_ms:
                    time.sleep(self.policy.retry_backoff_ms / 1000.0)
                continue

            # successful provider call
            if snap is None:
                meta.status = "MISSING"
                meta.circuit_state = "CLOSED"
                self._consecutive_failures = 0
                self.last_lookup_metadata = meta
                return None
            self._mark_success(meta)
            return snap

        # defensive fallback
        self._mark_failure(meta, status="ERROR", error_summary=str(last_error) if last_error else "UNKNOWN_PROVIDER_ERROR")
        return None


class ProviderBackedLiquidityFeed(_ProviderBackedFeedBase, LiquidityFeedProtocol):
    """Feed adapter that delegates to a MarketDataProvider with resilience metadata."""

    def __init__(self, provider: MarketDataProvider, policy: Optional[ProviderResiliencePolicy] = None):
        super().__init__(provider, policy, failure_feed_kind="liquidity")

    def lookup(self, asset_id: str, as_of: datetime) -> Optional[LiquiditySnapshot]:
        return self._execute_with_resilience(
            as_of=as_of,
            fetcher=lambda: self.provider.provide_liquidity(asset_id, as_of),
        )


class ProviderBackedBorrowFeed(_ProviderBackedFeedBase, BorrowFeedProtocol):
    """Feed adapter that delegates to a MarketDataProvider with resilience metadata."""

    def __init__(self, provider: MarketDataProvider, policy: Optional[ProviderResiliencePolicy] = None):
        super().__init__(provider, policy, failure_feed_kind="borrow")

    def lookup(self, asset_id: str, as_of: datetime) -> Optional[BorrowSnapshot]:
        return self._execute_with_resilience(
            as_of=as_of,
            fetcher=lambda: self.provider.provide_borrow(asset_id, as_of),
        )


class LiveConnectorProvider(MarketDataProvider):
    """
    Production-grade seam for real-time market-data providers.

    This adapter is intended to wrap real-time API clients (e.g., CCXT).
    Currently implemented as a lawful seam to enforce provider identity
    and source_mode=LIVE in development/testing.
    """
    def __init__(self, provider_id: str):
        self.provider_id = provider_id

    def provide_liquidity(self, asset_id: str, as_of: datetime) -> Optional[LiquiditySnapshot]:
        # Live lookup logic would go here. For now, it's a lawful seam.
        return None

    def provide_borrow(self, asset_id: str, as_of: datetime) -> Optional[BorrowSnapshot]:
        # Live lookup logic would go here.
        return None


class SnapshotStore:
    """
    Replayable, PIT-aware store of typed market-data snapshots.

    Populate with LiquiditySnapshot / BorrowSnapshot objects and query
    via the feed adapters below.  Deterministic: identical input lists
    produce identical lookup results and fingerprint chains.
    """

    def __init__(
        self,
        liquidity: Iterable[LiquiditySnapshot] = (),
        borrow: Iterable[BorrowSnapshot] = (),
    ):
        self._liquidity: List[LiquiditySnapshot] = sorted(
            list(liquidity), key=lambda s: s.snapshot_time
        )
        self._borrow: List[BorrowSnapshot] = sorted(
            list(borrow), key=lambda s: s.snapshot_time
        )

    @property
    def liquidity_snapshots(self) -> List[LiquiditySnapshot]:
        return list(self._liquidity)

    @property
    def borrow_snapshots(self) -> List[BorrowSnapshot]:
        return list(self._borrow)


class SnapshotStoreLiquidityFeed(LiquidityFeedProtocol):
    """Feed adapter backed by a SnapshotStore of LiquiditySnapshot objects."""

    def __init__(self, store: SnapshotStore):
        self._store = store

    def lookup(self, asset_id: str, as_of: datetime) -> Optional[LiquiditySnapshot]:
        candidates = [
            s for s in self._store._liquidity
            if s.asset_id == asset_id and s.snapshot_time <= as_of
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda s: s.snapshot_time)


class SnapshotStoreBorrowFeed(BorrowFeedProtocol):
    """Feed adapter backed by a SnapshotStore of BorrowSnapshot objects."""

    def __init__(self, store: SnapshotStore):
        self._store = store

    def lookup(self, asset_id: str, as_of: datetime) -> Optional[BorrowSnapshot]:
        candidates = [
            s for s in self._store._borrow
            if s.asset_id == asset_id and s.snapshot_time <= as_of
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda s: s.snapshot_time)


class ProvisionalLiquidityFeed(LiquidityFeedProtocol):
    """
    Fallback feed that produces PROVISIONAL-labeled snapshots from
    bare evidence-payload values.

    This feed NEVER returns LIVE or SNAPSHOT source_mode.  It exists
    so that strategies with only provisional liquidity inputs are
    honestly labeled rather than silently treated as feed-backed.
    """

    def lookup(self, asset_id: str, as_of: datetime) -> Optional[LiquiditySnapshot]:
        return LiquiditySnapshot(
            asset_id=asset_id,
            snapshot_time=as_of,
            source_mode="PROVISIONAL",
            source_id="provisional_payload",
        )


class ProvisionalBorrowFeed(BorrowFeedProtocol):
    """
    Fallback feed that produces PROVISIONAL-labeled snapshots from
    bare evidence-payload values.

    This feed NEVER returns LIVE or SNAPSHOT source_mode.
    """

    def lookup(self, asset_id: str, as_of: datetime) -> Optional[BorrowSnapshot]:
        return BorrowSnapshot(
            asset_id=asset_id,
            snapshot_time=as_of,
            source_mode="PROVISIONAL",
            source_id="provisional_payload",
        )
