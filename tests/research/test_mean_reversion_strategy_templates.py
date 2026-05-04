from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from strategy_validator.application.strategy_batch_loader import load_strategy_batch_spec
from strategy_validator.research.strategy_batch_evaluators import (
    evaluate_bollinger_mean_reversion,
    evaluate_keltner_channel_reversion,
    evaluate_vwap_deviation_reversion,
)
from strategy_validator.research.strategy_batch_runner import run_strategy_batch

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests/fixtures/strategy_data/mean_reversion_bars.csv"


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


def test_bollinger_mean_reversion_fades_oversold_band_stretches() -> None:
    prices, _highs, _lows, volumes = _fixture_ohlcv()
    metrics = evaluate_bollinger_mean_reversion(
        prices,
        {
            "window": 20,
            "band_k": 1.45,
            "rsi_window": 10,
            "volume_window": 16,
            "oversold": 45.0,
            "overbought": 58.0,
            "min_abs_z": 1.0,
            "min_volume_ratio": 0.70,
            "max_hold_bars": 4,
            "exposure": 0.70,
        },
        volumes=volumes,
    )

    assert metrics["bollinger_reversion_entry_count"] > 0
    assert metrics["mean_entry_zscore"] < -1.0
    assert metrics["volume_confirmation_ratio"] > 0.5
    assert metrics["mean_reversion_exit_count"] > 0
    assert metrics["total_return"] > 0.0


def test_vwap_deviation_reversion_detects_stretch_recovery() -> None:
    prices, highs, lows, volumes = _fixture_ohlcv()
    metrics = evaluate_vwap_deviation_reversion(
        prices,
        {
            "vwap_window": 20,
            "deviation_window": 20,
            "volume_window": 16,
            "min_deviation_pct": 0.012,
            "recovery_buffer": -0.01,
            "min_volume_ratio": 0.70,
            "max_hold_bars": 5,
            "exposure": 0.70,
        },
        highs=highs,
        lows=lows,
        volumes=volumes,
    )

    assert metrics["vwap_deviation_entry_count"] > 0
    assert metrics["mean_vwap_deviation"] > 0.01
    assert metrics["vwap_reversion_exit_count"] > 0
    assert metrics["volume_confirmation_ratio"] > 0.5
    assert metrics["total_return"] > 0.0


def test_keltner_channel_reversion_uses_atr_range_fade() -> None:
    prices, highs, lows, volumes = _fixture_ohlcv()
    metrics = evaluate_keltner_channel_reversion(
        prices,
        {
            "ema_window": 20,
            "atr_window": 12,
            "rsi_window": 10,
            "volume_window": 16,
            "atr_multiplier": 1.05,
            "oversold": 45.0,
            "overbought": 58.0,
            "min_volume_ratio": 0.70,
            "max_hold_bars": 5,
            "exposure": 0.65,
        },
        highs=highs,
        lows=lows,
        volumes=volumes,
    )

    assert metrics["keltner_reversion_entry_count"] > 0
    assert metrics["mean_channel_deviation"] > 1.0
    assert metrics["keltner_reversion_exit_count"] > 0
    assert metrics["volume_confirmation_ratio"] > 0.5
    assert metrics["total_return"] > 0.0


def test_mean_reversion_batch_runs_new_strategy_types(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(REPO)
    spec = load_strategy_batch_spec("configs/strategy_batches/example_mean_reversion_batch.json")
    spec = spec.model_copy(update={"output_root": str(tmp_path / "runs")})
    summary = run_strategy_batch(spec, allow_synthetic=False, run_id="mean-reversion-test", overwrite=True)

    assert summary.ok is True
    assert summary.strategy_count == 3
    assert summary.passed_count == 3
    assert summary.failed_count == 0
    assert {r.strategy_type for r in summary.strategies} == {
        "bollinger_mean_reversion",
        "vwap_deviation_reversion",
        "keltner_channel_reversion",
    }
    assert all(r.data_plane == "REAL_LOCAL" for r in summary.strategies)
    assert all(r.execution_realism_gate == "PROVEN" for r in summary.strategies)
    assert all(r.metrics.get("synthetic_demo_flag") == 0.0 for r in summary.strategies)

    metrics_by_type = {r.strategy_type: r.metrics for r in summary.strategies}
    assert metrics_by_type["bollinger_mean_reversion"]["bollinger_reversion_entry_count"] > 0
    assert metrics_by_type["vwap_deviation_reversion"]["vwap_deviation_entry_count"] > 0
    assert metrics_by_type["keltner_channel_reversion"]["keltner_reversion_entry_count"] > 0

    manifest = (
        Path(summary.output_dir)
        / "strategies"
        / "mean-bollinger-reversion-1"
        / "evidence_manifest.json"
    )
    body = json.loads(manifest.read_text(encoding="utf-8"))
    assert body["strategy_type"] == "bollinger_mean_reversion"
    assert body["synthetic_demo"] is False
