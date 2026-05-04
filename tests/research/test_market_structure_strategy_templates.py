from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from strategy_validator.application.strategy_batch_loader import load_strategy_batch_spec
from strategy_validator.research.strategy_batch_evaluators import (
    evaluate_atr_trailing_trend,
    evaluate_donchian_channel_breakout,
    evaluate_macd_volume_momentum,
)
from strategy_validator.research.strategy_batch_runner import run_strategy_batch

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests/fixtures/strategy_data/market_structure_bars.csv"


def _fixture_ohlcv() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    closes: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    volumes: list[float] = []
    with FIXTURE.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            closes.append(float(row["close"]))
            highs.append(float(row["high"]))
            lows.append(float(row["low"]))
            volumes.append(float(row["volume"]))
    return (
        np.array(closes, dtype=np.float64),
        np.array(highs, dtype=np.float64),
        np.array(lows, dtype=np.float64),
        np.array(volumes, dtype=np.float64),
    )


def test_donchian_channel_breakout_follows_confirmed_channel_break() -> None:
    prices, highs, lows, volumes = _fixture_ohlcv()
    metrics = evaluate_donchian_channel_breakout(
        prices,
        {
            "entry_lookback": 24,
            "exit_lookback": 10,
            "atr_window": 14,
            "volume_window": 16,
            "breakout_buffer": 0.001,
            "min_volume_ratio": 0.75,
            "min_atr_pct": 0.001,
            "exposure": 0.85,
        },
        highs=highs,
        lows=lows,
        volumes=volumes,
    )

    assert metrics["donchian_entry_count"] > 0
    assert metrics["channel_width_ratio"] > 0.0
    assert metrics["volume_confirmation_ratio"] > 0.5
    assert metrics["atr_filter_ratio"] > 0.5
    assert metrics["total_return"] > 0.0


def test_atr_trailing_trend_holds_until_trailing_stop() -> None:
    prices, highs, lows, volumes = _fixture_ohlcv()
    metrics = evaluate_atr_trailing_trend(
        prices,
        {
            "atr_window": 14,
            "trend_window": 28,
            "atr_multiplier": 2.4,
            "min_atr_pct": 0.001,
            "exposure": 0.8,
        },
        highs=highs,
        lows=lows,
        volumes=volumes,
    )

    assert metrics["atr_trend_entry_count"] > 0
    assert metrics["mean_atr_pct"] > 0.001
    assert metrics["total_return"] > 0.0


def test_macd_volume_momentum_confirms_cross_with_volume() -> None:
    prices, _highs, _lows, volumes = _fixture_ohlcv()
    metrics = evaluate_macd_volume_momentum(
        prices,
        {
            "fast_window": 8,
            "slow_window": 21,
            "signal_window": 7,
            "volume_window": 16,
            "min_volume_ratio": 0.75,
            "exposure": 0.75,
        },
        volumes=volumes,
    )

    assert metrics["macd_entry_count"] > 0
    assert metrics["volume_confirmation_ratio"] > 0.5
    assert metrics["mean_macd_histogram"] > 0.0
    assert metrics["total_return"] > 0.0


def test_market_structure_batch_runs_new_strategy_types(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(REPO)
    spec = load_strategy_batch_spec("configs/strategy_batches/example_market_structure_batch.json")
    spec = spec.model_copy(update={"output_root": str(tmp_path / "runs")})
    summary = run_strategy_batch(spec, allow_synthetic=False, run_id="market-structure-test", overwrite=True)

    assert summary.ok is True
    assert summary.strategy_count == 3
    assert summary.passed_count == 3
    assert summary.failed_count == 0
    assert {r.strategy_type for r in summary.strategies} == {
        "donchian_channel_breakout",
        "atr_trailing_trend",
        "macd_volume_momentum",
    }
    assert all(r.data_plane == "REAL_LOCAL" for r in summary.strategies)
    assert all(r.execution_realism_gate == "PROVEN" for r in summary.strategies)
    assert all(r.metrics.get("synthetic_demo_flag") == 0.0 for r in summary.strategies)

    metrics_by_type = {r.strategy_type: r.metrics for r in summary.strategies}
    assert metrics_by_type["donchian_channel_breakout"]["donchian_entry_count"] > 0
    assert metrics_by_type["atr_trailing_trend"]["atr_trend_entry_count"] > 0
    assert metrics_by_type["macd_volume_momentum"]["macd_entry_count"] > 0

    manifest = (
        Path(summary.output_dir)
        / "strategies"
        / "market-donchian-channel-breakout-1"
        / "evidence_manifest.json"
    )
    body = json.loads(manifest.read_text(encoding="utf-8"))
    assert body["strategy_type"] == "donchian_channel_breakout"
    assert body["synthetic_demo"] is False
