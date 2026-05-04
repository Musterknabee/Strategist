from __future__ import annotations

from datetime import datetime, timezone

from strategy_validator.contracts.strategy_batch import StrategyBatchSpec, StrategyCandidateSpec
from strategy_validator.contracts.strategy_data_snapshot import StrategyBar
from strategy_validator.contracts.strategy_execution_realism import ExecutionRealismGateStatus
from strategy_validator.research.strategy_execution_realism import evaluate_execution_realism


def _batch() -> StrategyBatchSpec:
    stub = StrategyCandidateSpec(
        strategy_id="stub",
        strategy_type="momentum",
        universe="U",
        timeframe="1d",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        lookback_days=30,
    )
    return StrategyBatchSpec(
        batch_id="b",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        mode="paper",
        output_root="out",
        strategies=[stub],
    )


def _assumptions() -> dict:
    return {
        "starting_capital": 1_000_000.0,
        "max_participation_rate": 0.05,
        "fee_bps": 1.0,
        "slippage_bps": 5.0,
        "min_average_daily_volume": 50_000.0,
        "allow_short": False,
        "borrow_required": False,
    }


def test_synthetic_cannot_prove() -> None:
    c = StrategyCandidateSpec(
        strategy_id="s",
        strategy_type="momentum",
        universe="U",
        timeframe="1d",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        lookback_days=30,
        execution_assumptions=_assumptions(),
    )
    batch = _batch()
    er = evaluate_execution_realism(
        candidate=c,
        batch=batch,
        run_id="r1",
        metrics={"trade_count": 1.0},
        bars=None,
        synthetic=True,
    )
    assert er.gate_status == ExecutionRealismGateStatus.NOT_APPLICABLE


def test_missing_assumptions_blocks() -> None:
    c = StrategyCandidateSpec(
        strategy_id="s",
        strategy_type="momentum",
        universe="DEMO",
        timeframe="1d",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        lookback_days=30,
    )
    bars = [
        StrategyBar(
            symbol="DEMO",
            timestamp_utc=datetime(2026, 4, 1, tzinfo=timezone.utc),
            open=100,
            high=101,
            low=99,
            close=100,
            volume=1000,
        )
    ]
    batch = _batch()
    er = evaluate_execution_realism(
        candidate=c,
        batch=batch,
        run_id="r1",
        metrics={"trade_count": 0.0},
        bars=bars,
        synthetic=False,
    )
    assert er.gate_status == ExecutionRealismGateStatus.BLOCKED
    assert "MISSING_EXECUTION_REALISM_ASSUMPTIONS" in er.blockers


def test_zero_volume_blocks() -> None:
    c = StrategyCandidateSpec(
        strategy_id="s",
        strategy_type="momentum",
        universe="DEMO",
        timeframe="1d",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        lookback_days=30,
        execution_assumptions=_assumptions(),
    )
    bars = [
        StrategyBar(
            symbol="DEMO",
            timestamp_utc=datetime(2026, 4, 1, tzinfo=timezone.utc),
            open=100,
            high=101,
            low=99,
            close=100,
            volume=0,
        )
    ]
    batch = _batch()
    er = evaluate_execution_realism(
        candidate=c,
        batch=batch,
        run_id="r1",
        metrics={"trade_count": 0.0},
        bars=bars,
        synthetic=False,
    )
    assert er.gate_status == ExecutionRealismGateStatus.BLOCKED


def test_high_participation_blocks() -> None:
    c = StrategyCandidateSpec(
        strategy_id="s",
        strategy_type="momentum",
        universe="DEMO",
        timeframe="1d",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        lookback_days=30,
        execution_assumptions={
            **_assumptions(),
            "starting_capital": 1e12,
            "max_participation_rate": 0.001,
        },
    )
    bars = [
        StrategyBar(
            symbol="DEMO",
            timestamp_utc=datetime(2026, 4, 1, tzinfo=timezone.utc),
            open=100,
            high=101,
            low=99,
            close=100,
            volume=50_000,
        )
    ]
    batch = _batch()
    er = evaluate_execution_realism(
        candidate=c,
        batch=batch,
        run_id="r1",
        metrics={"trade_count": 50.0},
        bars=bars,
        synthetic=False,
    )
    assert er.gate_status == ExecutionRealismGateStatus.BLOCKED
    assert any("PARTICIPATION" in b for b in er.blockers)


def test_borrow_required_blocks_without_ack() -> None:
    c = StrategyCandidateSpec(
        strategy_id="s",
        strategy_type="momentum",
        universe="DEMO",
        timeframe="1d",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        lookback_days=30,
        execution_assumptions={**_assumptions(), "borrow_required": True, "borrow_liquidity_evidence_ack": False},
    )
    bars = [
        StrategyBar(
            symbol="DEMO",
            timestamp_utc=datetime(2026, 4, 1, tzinfo=timezone.utc),
            open=100,
            high=101,
            low=99,
            close=100,
            volume=5000,
        )
    ]
    batch = _batch()
    er = evaluate_execution_realism(
        candidate=c,
        batch=batch,
        run_id="r1",
        metrics={"trade_count": 0.0},
        bars=bars,
        synthetic=False,
    )
    assert er.gate_status == ExecutionRealismGateStatus.BLOCKED
    assert any("BORROW" in b for b in er.blockers)
