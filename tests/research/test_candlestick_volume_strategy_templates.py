from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from strategy_validator.application.strategy_batch_loader import load_strategy_batch_spec
from strategy_validator.research.strategy_batch_evaluators import (
    evaluate_bullish_engulfing_volume_reversal,
    evaluate_hammer_volume_reversal,
    evaluate_inside_bar_volume_breakout,
)
from strategy_validator.research.strategy_batch_runner import run_strategy_batch

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests/fixtures/strategy_data/candlestick_volume_bars.csv"


def _fixture_ohlcv() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    opens: list[float] = []
    closes: list[float] = []
    highs: list[float] = []
    lows: list[float] = []
    volumes: list[float] = []
    with FIXTURE.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            opens.append(float(row["open"]))
            closes.append(float(row["close"]))
            highs.append(float(row["high"]))
            lows.append(float(row["low"]))
            volumes.append(float(row["volume"]))
    return (
        np.array(opens, dtype=np.float64),
        np.array(closes, dtype=np.float64),
        np.array(highs, dtype=np.float64),
        np.array(lows, dtype=np.float64),
        np.array(volumes, dtype=np.float64),
    )


def test_bullish_engulfing_volume_reversal_uses_open_close_body_and_volume() -> None:
    opens, prices, highs, lows, volumes = _fixture_ohlcv()
    metrics = evaluate_bullish_engulfing_volume_reversal(
        prices,
        {
            "trend_lookback": 8,
            "volume_window": 20,
            "min_downtrend_return": -0.035,
            "min_volume_ratio": 1.05,
            "min_body_ratio": 1.05,
            "exposure": 0.70,
            "max_hold_bars": 4,
        },
        opens=opens,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )

    assert metrics["bullish_engulfing_entry_count"] > 0
    assert metrics["mean_prior_downtrend_return"] < -0.03
    assert metrics["mean_engulfing_body_ratio"] > 1.0
    assert metrics["volume_confirmation_ratio"] >= 1.0
    assert metrics["total_return"] > 0.0


def test_hammer_volume_reversal_detects_lower_wick_reversal() -> None:
    opens, prices, highs, lows, volumes = _fixture_ohlcv()
    metrics = evaluate_hammer_volume_reversal(
        prices,
        {
            "trend_lookback": 8,
            "volume_window": 20,
            "min_downtrend_return": -0.03,
            "min_lower_shadow_ratio": 2.0,
            "max_upper_shadow_ratio": 1.1,
            "min_volume_ratio": 1.0,
            "exposure": 0.65,
            "max_hold_bars": 4,
        },
        opens=opens,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )

    assert metrics["hammer_entry_count"] > 0
    assert metrics["mean_lower_shadow_ratio"] > 2.0
    assert metrics["mean_prior_downtrend_return"] < -0.03
    assert metrics["volume_confirmation_ratio"] >= 1.0
    assert metrics["total_return"] > 0.0


def test_inside_bar_volume_breakout_detects_compression_breakout() -> None:
    opens, prices, highs, lows, volumes = _fixture_ohlcv()
    metrics = evaluate_inside_bar_volume_breakout(
        prices,
        {
            "cluster_window": 4,
            "volume_window": 20,
            "breakout_buffer": 0.001,
            "min_volume_ratio": 1.0,
            "min_trend_return": 0.015,
            "trend_lookback": 12,
            "exposure": 0.68,
            "max_hold_bars": 4,
        },
        opens=opens,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )

    assert metrics["inside_bar_breakout_entry_count"] > 0
    assert metrics["inside_bar_cluster_count"] > 0
    assert metrics["mean_breakout_volume_ratio"] > 1.0
    assert metrics["volume_confirmation_ratio"] >= 1.0
    assert metrics["total_return"] > 0.0


def test_candlestick_volume_batch_runs_new_strategy_types(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(REPO)
    spec = load_strategy_batch_spec("configs/strategy_batches/example_candlestick_volume_batch.json")
    spec = spec.model_copy(update={"output_root": str(tmp_path / "runs")})
    summary = run_strategy_batch(spec, allow_synthetic=False, run_id="candlestick-volume-test", overwrite=True)

    assert summary.ok is True
    assert summary.strategy_count == 3
    assert summary.passed_count == 3
    assert summary.failed_count == 0
    assert {r.strategy_type for r in summary.strategies} == {
        "bullish_engulfing_volume_reversal",
        "hammer_volume_reversal",
        "inside_bar_volume_breakout",
    }
    assert all(r.data_plane == "REAL_LOCAL" for r in summary.strategies)
    assert all(r.execution_realism_gate == "PROVEN" for r in summary.strategies)
    assert all(r.metrics.get("synthetic_demo_flag") == 0.0 for r in summary.strategies)

    metrics_by_type = {r.strategy_type: r.metrics for r in summary.strategies}
    assert metrics_by_type["bullish_engulfing_volume_reversal"]["bullish_engulfing_entry_count"] > 0
    assert metrics_by_type["hammer_volume_reversal"]["hammer_entry_count"] > 0
    assert metrics_by_type["inside_bar_volume_breakout"]["inside_bar_breakout_entry_count"] > 0

    manifest = (
        Path(summary.output_dir)
        / "strategies"
        / "candle-bullish-engulfing-volume-1"
        / "evidence_manifest.json"
    )
    body = json.loads(manifest.read_text(encoding="utf-8"))
    assert body["strategy_type"] == "bullish_engulfing_volume_reversal"
    assert body["synthetic_demo"] is False
