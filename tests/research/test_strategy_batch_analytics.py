from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from strategy_validator.contracts.strategy_batch import PitPolicy, StrategyBatchSpec, StrategyCandidateSpec, StrategyRunStatus
from strategy_validator.research.strategy_batch_analytics import apply_batch_ranking, strategy_log_returns_series
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from strategy_validator.research.strategy_batch_evaluators import deterministic_prices, evaluate_momentum
from strategy_validator.research.strategy_batch_runner import run_strategy_batch


def test_strategy_returns_match_evaluator_momentum() -> None:
    prices = deterministic_prices(seed="x", n=80)
    params = {"signal_window": 15}
    m = evaluate_momentum(prices, params)
    strat = strategy_log_returns_series(prices, "momentum", params)
    equity = np.cumprod(np.exp(strat))
    tr = float(equity[-1] - 1.0) if equity.size else 0.0
    assert abs(tr - m["total_return"]) < 1e-9


def test_equity_curve_deterministic() -> None:
    prices = deterministic_prices(seed="det", n=50)
    params = {"signal_window": 10}
    strat = strategy_log_returns_series(prices, "momentum", params)
    e1 = np.cumprod(np.exp(strat)).tolist()
    strat2 = strategy_log_returns_series(prices, "momentum", params)
    e2 = np.cumprod(np.exp(strat2)).tolist()
    assert e1 == e2


def test_blocked_strategies_rank_last() -> None:
    from strategy_validator.contracts.strategy_batch import StrategyRunResult

    good = StrategyRunResult(
        strategy_id="a",
        status=StrategyRunStatus.PASSED,
        analytics_score=5.0,
    )
    bad = StrategyRunResult(
        strategy_id="b",
        status=StrategyRunStatus.BLOCKED,
        analytics_score=99.0,
    )
    out, ranking = apply_batch_ranking([bad, good])
    assert ranking[0]["strategy_id"] == "a"
    assert ranking[1]["strategy_id"] == "b"
    by_id = {r.strategy_id: r for r in out}
    assert by_id["a"].analytics_rank == 1
    assert by_id["b"].analytics_rank == 2


def test_run_writes_chart_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "chart-run")
    spec = StrategyBatchSpec(
        batch_id="chart-batch",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        mode="paper",
        max_workers=2,
        pit_policy=PitPolicy.DEGRADE_TO_PAPER_ONLY,
        output_root=str(tmp_path / "runs"),
        strategies=[
            StrategyCandidateSpec(
                strategy_id="solo",
                strategy_type="momentum",
                universe="U",
                timeframe="1d",
                as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
                lookback_days=50,
                params={"signal_window": 10},
            ),
        ],
    )
    summary = run_strategy_batch(spec, allow_synthetic=True)
    sd = Path(summary.output_dir) / "strategies" / "solo"
    assert (sd / "equity_curve.json").is_file()
    assert (sd / "drawdown_curve.json").is_file()
    assert (sd / "rolling_metrics.json").is_file()
    assert (sd / "fold_performance.json").is_file()
    assert (sd / "strategy_scorecard.json").is_file()
    assert (sd / "trade_markers.json").is_file()
    assert (sd / "data_quality_result.json").is_file()
    eq = json.loads((sd / "equity_curve.json").read_text(encoding="utf-8"))
    assert "equity" in eq and len(eq["equity"]) >= 1
    body = {k: v for k, v in eq.items() if k != "equity_curve_sha256"}
    assert eq["equity_curve_sha256"] == canonical_json_sha256(body)
    assert summary.batch_ranking and summary.batch_ranking[0]["strategy_id"] == "solo"
    assert summary.strategies[0].charts_compact is not None


def test_read_plane_latest_includes_charts(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from strategy_validator.application.ui_strategy_batch import build_ui_strategy_batch_latest_payload

    root = tmp_path / "runs"
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT", str(root))
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "ui-charts")
    spec = StrategyBatchSpec(
        batch_id="ui-chart-batch",
        as_of_utc=datetime(2026, 5, 2, tzinfo=timezone.utc),
        mode="paper",
        max_workers=2,
        pit_policy=PitPolicy.DEGRADE_TO_PAPER_ONLY,
        output_root=str(root),
        strategies=[
            StrategyCandidateSpec(
                strategy_id="one",
                strategy_type="momentum",
                universe="U",
                timeframe="1d",
                as_of_utc=datetime(2026, 5, 2, tzinfo=timezone.utc),
                lookback_days=40,
            ),
        ],
    )
    run_strategy_batch(spec, allow_synthetic=True)
    payload = build_ui_strategy_batch_latest_payload()
    latest = payload["latest"]
    assert latest is not None
    assert latest["batch_ranking"]
    row = latest["strategies"][0]
    assert row.get("charts_compact") is not None
    assert row.get("equity_curve_path")
