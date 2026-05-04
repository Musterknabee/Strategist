from __future__ import annotations

from datetime import datetime, timezone

from strategy_validator.contracts.market_data_integrity import MarketDataIntegrityGateStatus
from strategy_validator.contracts.strategy_data_snapshot import StrategyBar
from strategy_validator.research.market_data_integrity import evaluate_market_data_integrity


def _bar(day: int, close: float) -> StrategyBar:
    return StrategyBar(
        symbol="SPY",
        timestamp_utc=datetime(2026, 1, day, tzinfo=timezone.utc),
        open=close,
        high=close,
        low=close,
        close=close,
        volume=1_000_000,
    )


def test_split_like_jump_warns_and_digest_is_deterministic() -> None:
    bars = [_bar(2, 100), _bar(5, 49), _bar(6, 50)]
    res1 = evaluate_market_data_integrity(
        strategy_id="s1",
        batch_id="b1",
        run_id="r1",
        bars=bars,
        as_of_utc=datetime(2026, 1, 6, tzinfo=timezone.utc),
        snapshot=None,
    )
    res2 = evaluate_market_data_integrity(
        strategy_id="s1",
        batch_id="b1",
        run_id="r1",
        bars=bars,
        as_of_utc=datetime(2026, 1, 6, tzinfo=timezone.utc),
        snapshot=None,
    )
    assert res1.gate_status in {MarketDataIntegrityGateStatus.WARNING, MarketDataIntegrityGateStatus.BLOCKED}
    assert res1.corporate_action_warnings
    assert res1.evidence_sha256 == res2.evidence_sha256


def test_stale_bar_blocks() -> None:
    res = evaluate_market_data_integrity(
        strategy_id="s1",
        batch_id="b1",
        run_id="r1",
        bars=[_bar(2, 100), _bar(5, 101)],
        as_of_utc=datetime(2026, 1, 15, tzinfo=timezone.utc),
        snapshot=None,
    )
    assert res.gate_status == MarketDataIntegrityGateStatus.BLOCKED
    assert any(x.startswith("STALE_LAST_BAR_HOURS") for x in res.blockers)
