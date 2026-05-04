from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from strategy_validator.application.strategy_batch_loader import load_strategy_batch_spec
from strategy_validator.research.strategy_batch_evaluators import (
    evaluate_moving_average_trend,
    evaluate_obv_accumulation_breakout,
    evaluate_trendline_volume_breakout,
)
from strategy_validator.research.strategy_batch_runner import run_strategy_batch

REPO = Path(__file__).resolve().parents[2]


def _rising_ohlcv(n: int = 96) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    base = np.linspace(100.0, 118.0, n, dtype=np.float64)
    base[-6:] += np.linspace(0.0, 8.0, 6, dtype=np.float64)
    highs = base * 1.004
    lows = base * 0.996
    volumes = np.linspace(1000.0, 1800.0, n, dtype=np.float64)
    volumes[-6:] *= 2.0
    return base, highs, lows, volumes


def test_moving_average_trend_uses_volume_confirmed_trend() -> None:
    prices, _highs, _lows, volumes = _rising_ohlcv()
    metrics = evaluate_moving_average_trend(
        prices,
        {
            "fast_window": 8,
            "slow_window": 24,
            "volume_window": 12,
            "min_volume_ratio": 0.75,
            "exposure": 0.75,
        },
        volumes=volumes,
    )
    assert metrics["trend_signal_count"] > 0
    assert metrics["volume_confirmation_ratio"] > 0.5
    assert metrics["total_return"] > 0


def test_diagonal_trendline_breakout_finds_price_volume_breaks() -> None:
    prices, highs, lows, volumes = _rising_ohlcv()
    metrics = evaluate_trendline_volume_breakout(
        prices,
        {
            "lookback": 28,
            "pivot_window": 3,
            "min_touches": 2,
            "breakout_buffer": 0.001,
            "volume_window": 12,
            "min_volume_ratio": 0.75,
            "exposure": 0.85,
        },
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
    assert metrics["breakout_signal_count"] > 0
    assert metrics["volume_confirmation_ratio"] > 0.5
    assert metrics["total_return"] > 0


def test_obv_accumulation_breakout_requires_obv_confirmation() -> None:
    prices, _highs, _lows, volumes = _rising_ohlcv()
    metrics = evaluate_obv_accumulation_breakout(
        prices,
        {
            "lookback": 28,
            "breakout_buffer": 0.001,
            "volume_window": 12,
            "min_volume_ratio": 0.75,
            "exposure": 0.8,
        },
        volumes=volumes,
    )
    assert metrics["obv_signal_count"] > 0
    assert metrics["obv_confirmation_ratio"] > 0.5
    assert metrics["total_return"] > 0


def test_price_volume_batch_runs_new_strategy_types(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(REPO)
    spec = load_strategy_batch_spec("configs/strategy_batches/example_price_volume_batch.json")
    spec = spec.model_copy(update={"output_root": str(tmp_path / "runs")})
    summary = run_strategy_batch(spec, allow_synthetic=False, run_id="price-volume-test", overwrite=True)

    assert summary.strategy_count == 3
    assert summary.failed_count == 0
    assert {r.strategy_type for r in summary.strategies} == {
        "moving_average_trend",
        "trendline_volume_breakout",
        "obv_accumulation_breakout",
    }
    assert all(r.data_plane == "REAL_LOCAL" for r in summary.strategies)
    assert all(r.metrics.get("synthetic_demo_flag") == 0.0 for r in summary.strategies)

    metrics_by_type = {r.strategy_type: r.metrics for r in summary.strategies}
    assert metrics_by_type["moving_average_trend"]["trend_signal_count"] > 0
    assert metrics_by_type["trendline_volume_breakout"]["breakout_signal_count"] > 0
    assert metrics_by_type["obv_accumulation_breakout"]["obv_signal_count"] > 0

    manifest = Path(summary.output_dir) / "strategies" / "pv-diagonal-trendline-breakout-1" / "evidence_manifest.json"
    body = json.loads(manifest.read_text(encoding="utf-8"))
    assert body["strategy_type"] == "trendline_volume_breakout"
    assert body["synthetic_demo"] is False
