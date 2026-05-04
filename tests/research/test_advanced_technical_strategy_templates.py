from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from strategy_validator.application.strategy_batch_loader import load_strategy_batch_spec
from strategy_validator.research.strategy_batch_evaluators import (
    evaluate_bollinger_squeeze_breakout,
    evaluate_rsi_volume_reversal,
    evaluate_vwap_pullback_continuation,
)
from strategy_validator.research.strategy_batch_runner import run_strategy_batch

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests/fixtures/strategy_data/advanced_technical_bars.csv"


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


def test_rsi_volume_reversal_detects_exhaustion_bounce() -> None:
    prices, _highs, _lows, volumes = _fixture_ohlcv()
    metrics = evaluate_rsi_volume_reversal(
        prices,
        {
            "rsi_window": 8,
            "lookback": 10,
            "oversold": 35.0,
            "volume_window": 10,
            "min_volume_ratio": 0.8,
            "recovery_buffer": 0.001,
            "exposure": 0.7,
        },
        volumes=volumes,
    )

    assert metrics["rsi_reversal_signal_count"] > 0
    assert metrics["volume_confirmation_ratio"] > 0.5
    assert 20.0 <= metrics["mean_entry_rsi"] <= 55.0
    assert metrics["total_return"] > 0


def test_bollinger_squeeze_breakout_detects_compression_expansion() -> None:
    prices, _highs, _lows, volumes = _fixture_ohlcv()
    metrics = evaluate_bollinger_squeeze_breakout(
        prices,
        {
            "window": 18,
            "squeeze_lookback": 12,
            "band_k": 2.0,
            "max_squeeze_width": 0.035,
            "breakout_buffer": 0.001,
            "volume_window": 10,
            "min_volume_ratio": 0.8,
            "exposure": 0.8,
        },
        volumes=volumes,
    )

    assert metrics["squeeze_observation_count"] > 0
    assert metrics["squeeze_breakout_signal_count"] > 0
    assert metrics["volume_confirmation_ratio"] > 0.5
    assert metrics["total_return"] > 0


def test_vwap_pullback_continuation_detects_reclaim_after_pullback() -> None:
    prices, highs, lows, volumes = _fixture_ohlcv()
    metrics = evaluate_vwap_pullback_continuation(
        prices,
        {
            "vwap_window": 18,
            "trend_window": 30,
            "volume_window": 10,
            "pullback_band": 0.03,
            "resume_buffer": 0.001,
            "min_volume_ratio": 0.8,
            "exposure": 0.75,
        },
        highs=highs,
        lows=lows,
        volumes=volumes,
    )

    assert metrics["vwap_pullback_signal_count"] > 0
    assert metrics["vwap_reclaim_ratio"] > 0.5
    assert metrics["volume_confirmation_ratio"] > 0.5
    assert metrics["total_return"] > 0


def test_advanced_technical_batch_runs_new_strategy_types(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(REPO)
    spec = load_strategy_batch_spec("configs/strategy_batches/example_advanced_technical_batch.json")
    spec = spec.model_copy(update={"output_root": str(tmp_path / "runs")})
    summary = run_strategy_batch(spec, allow_synthetic=False, run_id="advanced-technical-test", overwrite=True)

    assert summary.ok is True
    assert summary.strategy_count == 3
    assert summary.passed_count == 3
    assert summary.failed_count == 0
    assert {r.strategy_type for r in summary.strategies} == {
        "rsi_volume_reversal",
        "bollinger_squeeze_breakout",
        "vwap_pullback_continuation",
    }
    assert all(r.data_plane == "REAL_LOCAL" for r in summary.strategies)
    assert all(r.execution_realism_gate == "PROVEN" for r in summary.strategies)
    assert all(r.metrics.get("synthetic_demo_flag") == 0.0 for r in summary.strategies)

    metrics_by_type = {r.strategy_type: r.metrics for r in summary.strategies}
    assert metrics_by_type["rsi_volume_reversal"]["rsi_reversal_signal_count"] > 0
    assert metrics_by_type["bollinger_squeeze_breakout"]["squeeze_breakout_signal_count"] > 0
    assert metrics_by_type["vwap_pullback_continuation"]["vwap_pullback_signal_count"] > 0

    manifest = (
        Path(summary.output_dir)
        / "strategies"
        / "technical-bollinger-squeeze-breakout-1"
        / "evidence_manifest.json"
    )
    body = json.loads(manifest.read_text(encoding="utf-8"))
    assert body["strategy_type"] == "bollinger_squeeze_breakout"
    assert body["synthetic_demo"] is False
