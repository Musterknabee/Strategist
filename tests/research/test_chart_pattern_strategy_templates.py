from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from strategy_validator.application.strategy_batch_loader import load_strategy_batch_spec
from strategy_validator.research.strategy_batch_evaluators import (
    evaluate_ascending_triangle_breakout,
    evaluate_bull_flag_continuation,
    evaluate_support_resistance_retest,
)
from strategy_validator.research.strategy_batch_runner import run_strategy_batch

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests/fixtures/strategy_data/chart_pattern_bars.csv"


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


def test_ascending_triangle_breakout_uses_resistance_rising_lows_and_volume() -> None:
    prices, highs, lows, volumes = _fixture_ohlcv()
    metrics = evaluate_ascending_triangle_breakout(
        prices,
        {
            "lookback": 45,
            "min_touches": 2,
            "resistance_tolerance_pct": 0.02,
            "min_low_slope_pct": 0.00010,
            "breakout_buffer": 0.001,
            "volume_window": 16,
            "min_volume_ratio": 0.9,
            "exposure": 0.8,
            "max_hold_bars": 6,
        },
        highs=highs,
        lows=lows,
        volumes=volumes,
    )

    assert metrics["ascending_triangle_entry_count"] > 0
    assert metrics["resistance_touch_count"] >= 2
    assert metrics["rising_lows_slope_pct"] > 0.0
    assert metrics["volume_confirmation_ratio"] > 0.5
    assert metrics["total_return"] > 0.0


def test_bull_flag_continuation_detects_impulse_flag_breakout() -> None:
    prices, highs, lows, volumes = _fixture_ohlcv()
    metrics = evaluate_bull_flag_continuation(
        prices,
        {
            "impulse_lookback": 18,
            "flag_lookback": 12,
            "min_impulse_return": 0.06,
            "max_flag_depth": 0.09,
            "breakout_buffer": 0.0,
            "volume_window": 16,
            "min_volume_ratio": 0.85,
            "exposure": 0.78,
            "max_hold_bars": 5,
        },
        highs=highs,
        lows=lows,
        volumes=volumes,
    )

    assert metrics["bull_flag_entry_count"] > 0
    assert metrics["mean_impulse_return"] > 0.06
    assert 0.0 < metrics["mean_flag_depth"] < 0.10
    assert metrics["volume_confirmation_ratio"] > 0.5
    assert metrics["total_return"] > 0.0


def test_support_resistance_retest_detects_breakout_reclaim() -> None:
    prices, highs, lows, volumes = _fixture_ohlcv()
    metrics = evaluate_support_resistance_retest(
        prices,
        {
            "resistance_lookback": 35,
            "retest_window": 8,
            "breakout_buffer": 0.002,
            "retest_band": 0.02,
            "volume_window": 16,
            "min_volume_ratio": 0.80,
            "exposure": 0.72,
            "max_hold_bars": 5,
        },
        highs=highs,
        lows=lows,
        volumes=volumes,
    )

    assert metrics["retest_entry_count"] > 0
    assert metrics["support_retest_count"] > 0
    assert 0.0 < metrics["mean_retest_distance_pct"] < 0.03
    assert metrics["volume_confirmation_ratio"] > 0.5
    assert metrics["total_return"] > 0.0


def test_chart_pattern_batch_runs_new_strategy_types(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(REPO)
    spec = load_strategy_batch_spec("configs/strategy_batches/example_chart_pattern_batch.json")
    spec = spec.model_copy(update={"output_root": str(tmp_path / "runs")})
    summary = run_strategy_batch(spec, allow_synthetic=False, run_id="chart-pattern-test", overwrite=True)

    assert summary.ok is True
    assert summary.strategy_count == 3
    assert summary.passed_count == 3
    assert summary.failed_count == 0
    assert {r.strategy_type for r in summary.strategies} == {
        "ascending_triangle_breakout",
        "bull_flag_continuation",
        "support_resistance_retest",
    }
    assert all(r.data_plane == "REAL_LOCAL" for r in summary.strategies)
    assert all(r.execution_realism_gate == "PROVEN" for r in summary.strategies)
    assert all(r.metrics.get("synthetic_demo_flag") == 0.0 for r in summary.strategies)

    metrics_by_type = {r.strategy_type: r.metrics for r in summary.strategies}
    assert metrics_by_type["ascending_triangle_breakout"]["ascending_triangle_entry_count"] > 0
    assert metrics_by_type["bull_flag_continuation"]["bull_flag_entry_count"] > 0
    assert metrics_by_type["support_resistance_retest"]["retest_entry_count"] > 0

    manifest = (
        Path(summary.output_dir)
        / "strategies"
        / "chart-ascending-triangle-breakout-1"
        / "evidence_manifest.json"
    )
    body = json.loads(manifest.read_text(encoding="utf-8"))
    assert body["strategy_type"] == "ascending_triangle_breakout"
    assert body["synthetic_demo"] is False
