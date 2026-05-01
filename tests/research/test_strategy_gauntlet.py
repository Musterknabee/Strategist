from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from strategy_validator.contracts.strategy_data_quality import DataQualityGateStatus
from strategy_validator.contracts.strategy_data_snapshot import (
    StrategyBar,
    StrategyDataSnapshot,
    StrategyDataSourceClassification,
    StrategyPitSnapshotStatus,
)
from strategy_validator.contracts.strategy_parameter_sensitivity import ParameterSensitivityGateStatus
from strategy_validator.research.strategy_data_quality import evaluate_local_bars_data_quality
from strategy_validator.research.strategy_parameter_sensitivity import evaluate_parameter_sensitivity
from strategy_validator.research.strategy_portfolio_summary import build_batch_portfolio_summary
from strategy_validator.research.strategy_regime_analysis import evaluate_regime_analysis
from strategy_validator.contracts.strategy_batch import StrategyRunResult, StrategyRunStatus


def _bar(
    *,
    sym: str = "X",
    ts: str = "2026-01-02T00:00:00+00:00",
    o: float = 100.0,
    h: float = 101.0,
    l: float = 99.0,
    c: float = 100.5,
    v: float = 1000.0,
) -> StrategyBar:
    return StrategyBar(
        symbol=sym,
        timestamp_utc=datetime.fromisoformat(ts.replace("Z", "+00:00")),
        open=o,
        high=h,
        low=l,
        close=c,
        volume=v,
    )


def test_data_quality_proven_clean_bars() -> None:
    bars = []
    for i in range(2, 12):
        c = 100.0 + i * 0.1
        bars.append(
            _bar(
                ts=f"2026-01-{i:02d}T00:00:00+00:00",
                o=c - 0.2,
                h=c + 0.5,
                l=c - 0.5,
                c=c,
            )
        )
    snap = StrategyDataSnapshot(
        strategy_id="s",
        batch_id="b",
        universe="X",
        timeframe="1d",
        as_of_utc=datetime(2026, 1, 20, tzinfo=timezone.utc),
        lookback_start_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
        lookback_end_utc=datetime(2026, 1, 20, tzinfo=timezone.utc),
        provider_id="local",
        source_classification=StrategyDataSourceClassification.LOCAL_GOVERNED_BARS,
        pit_status=StrategyPitSnapshotStatus.PIT_VERIFIED,
        retrieved_at_utc=datetime(2026, 1, 20, tzinfo=timezone.utc),
        published_at_utc=datetime(2026, 1, 2, tzinfo=timezone.utc),
        bars_path="x",
        bars_sha256="x",
        row_count=len(bars),
        symbol_count=1,
        warnings=[],
        blockers=[],
        may_gate_live_promotion=False,
    )
    dq = evaluate_local_bars_data_quality(
        strategy_id="s",
        batch_id="b",
        run_id="r",
        bars=bars,
        as_of_utc=datetime(2026, 1, 20, tzinfo=timezone.utc),
        synthetic_demo=False,
        snapshot=snap,
        load_warnings=[],
    )
    assert dq.gate_status == DataQualityGateStatus.PROVEN
    assert dq.data_quality_evidence_sha256


def test_data_quality_blocked_duplicate_timestamp() -> None:
    t = "2026-01-05T00:00:00+00:00"
    bars = [_bar(ts=t, c=100.0), _bar(ts=t, c=101.0)]
    dq = evaluate_local_bars_data_quality(
        strategy_id="s",
        batch_id="b",
        run_id="r",
        bars=bars,
        as_of_utc=datetime(2026, 1, 10, tzinfo=timezone.utc),
        synthetic_demo=False,
        snapshot=None,
        load_warnings=[],
    )
    assert dq.gate_status == DataQualityGateStatus.BLOCKED
    assert dq.duplicate_timestamp_count >= 1


def test_data_quality_blocked_bad_ohlc() -> None:
    bars = [_bar(h=99.0, l=100.0, c=100.5)]
    dq = evaluate_local_bars_data_quality(
        strategy_id="s",
        batch_id="b",
        run_id="r",
        bars=bars,
        as_of_utc=datetime(2026, 1, 10, tzinfo=timezone.utc),
        synthetic_demo=False,
        snapshot=None,
        load_warnings=[],
    )
    assert dq.gate_status == DataQualityGateStatus.BLOCKED


def test_parameter_sensitivity_not_applicable_synthetic() -> None:
    prices = np.array([100.0, 100.5, 101.0], dtype=np.float64)
    ps = evaluate_parameter_sensitivity(
        strategy_id="s",
        batch_id="b",
        run_id="r",
        prices=prices,
        strategy_type="momentum",
        params={"signal_window": 2},
        synthetic_demo=True,
    )
    assert ps.gate_status == ParameterSensitivityGateStatus.NOT_APPLICABLE


def test_regime_not_applicable_synthetic() -> None:
    prices = np.linspace(100.0, 110.0, 80)
    reg = evaluate_regime_analysis(
        strategy_id="s",
        batch_id="b",
        run_id="r",
        prices=prices,
        strategy_type="momentum",
        params={"signal_window": 10},
        synthetic_demo=True,
    )
    assert reg.gate_status == "NOT_APPLICABLE"


def test_portfolio_not_applicable_single_strategy() -> None:
    r = StrategyRunResult(
        strategy_id="a",
        status=StrategyRunStatus.PASSED,
        equity_curve_path="",
    )
    p = build_batch_portfolio_summary(batch_id="b", run_id="r", strategies=[r])
    assert p.portfolio_gate_status == "NOT_APPLICABLE"


def test_portfolio_duplicate_stream_high_correlation(tmp_path) -> None:
    import json

    d = tmp_path / "e1.json"
    eq = {"equity": [1.0, 1.01, 1.02, 1.03, 1.04]}
    d.write_text(json.dumps(eq), encoding="utf-8")
    r1 = StrategyRunResult(
        strategy_id="a",
        status=StrategyRunStatus.PASSED,
        data_plane="REAL_LOCAL",
        equity_curve_path=str(d),
    )
    r2 = StrategyRunResult(
        strategy_id="b",
        status=StrategyRunStatus.PASSED,
        data_plane="REAL_LOCAL",
        equity_curve_path=str(d),
    )
    p = build_batch_portfolio_summary(batch_id="b", run_id="r", strategies=[r1, r2])
    assert p.portfolio_gate_status in ("DUPLICATIVE", "WARNING")
