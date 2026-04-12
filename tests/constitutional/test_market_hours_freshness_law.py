"""LIVE freshness uses US RTH vs off-hours thresholds when profile is enabled."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from strategy_validator.contracts.market_data import LiquiditySnapshot
from strategy_validator.core.config import RuntimePolicy
from strategy_validator.validator.orchestrator import _evaluate_snapshot_freshness


def test_live_freshness_off_hours_uses_wider_threshold_outside_rth():
    policy = RuntimePolicy(
        live_market_data_freshness_threshold_seconds=60,
        live_market_data_freshness_off_hours_threshold_seconds=500,
        live_freshness_market_hours_profile="US_EQUITIES_RTH",
    )
    # 2024-06-03 is a Monday; 09:00 UTC → 05:00 America/New_York (pre-open).
    as_of = datetime(2024, 6, 3, 9, 0, 0, tzinfo=timezone.utc)
    snap = LiquiditySnapshot(
        asset_id="SPY",
        snapshot_time=as_of - timedelta(seconds=120),
        adv_notional=1e9,
        spread_bps=1.0,
        source_id="feed",
        source_mode="LIVE",
    )
    fr = _evaluate_snapshot_freshness(snap, as_of, policy)
    assert fr.market_hours_law == "US_RTH_CLOSED"
    assert fr.applied_threshold_seconds == 500.0
    assert fr.status == "FRESH"


def test_live_freshness_rth_uses_base_threshold_inside_session():
    policy = RuntimePolicy(
        live_market_data_freshness_threshold_seconds=60,
        live_market_data_freshness_off_hours_threshold_seconds=500,
        live_freshness_market_hours_profile="US_EQUITIES_RTH",
    )
    # Same Monday; 14:30 UTC → 10:30 Eastern (within 09:30–16:00).
    as_of = datetime(2024, 6, 3, 14, 30, 0, tzinfo=timezone.utc)
    snap = LiquiditySnapshot(
        asset_id="SPY",
        snapshot_time=as_of - timedelta(seconds=120),
        adv_notional=1e9,
        spread_bps=1.0,
        source_id="feed",
        source_mode="LIVE",
    )
    fr = _evaluate_snapshot_freshness(snap, as_of, policy)
    assert fr.market_hours_law == "US_RTH_OPEN"
    assert fr.applied_threshold_seconds == 60.0
    assert fr.status == "STALE"
