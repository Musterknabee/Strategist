from __future__ import annotations

from typing import Any

import numpy as np

from strategy_validator.research.strategy_batch_evaluators_common import (
    _coerce_optional,
    _ema,
    _metrics_from_returns,
    _rolling_mean,
    _volume_proxy,
    log_returns,
)


def evaluate_macd_volume_momentum(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = macd_volume_momentum_returns(prices, params, volumes=volumes)
    return _metrics_from_returns(strat, trade_count=extras.get("macd_entry_count", 0.0), extras=extras)


def macd_volume_momentum_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """MACD trend-momentum template gated by volume participation."""

    r = log_returns(prices)
    n = prices.size
    fast = int(params.get("fast_window", 12))
    slow = int(params.get("slow_window", 26))
    signal_window = int(params.get("signal_window", 9))
    volume_window = int(params.get("volume_window", 20))
    min_volume_ratio = float(params.get("min_volume_ratio", 0.9))
    exposure = float(params.get("exposure", 0.75))
    allow_short = bool(params.get("allow_short", False))
    if n < max(fast, slow, signal_window, volume_window) + 5 or r.size == 0:
        return np.zeros_like(r), {
            "macd_entry_count": 0.0,
            "volume_confirmation_ratio": 0.0,
            "mean_macd_histogram": 0.0,
        }

    vol = _coerce_optional(volumes, _volume_proxy(prices))
    vol_ma = _rolling_mean(vol, volume_window)
    ema_fast = _ema(prices, fast)
    ema_slow = _ema(prices, slow)
    macd = ema_fast - ema_slow
    signal = _ema(macd, signal_window)
    hist = macd - signal
    signals = np.zeros_like(r)
    position = 0.0
    entries = 0
    attempted = 0
    confirmed = 0
    hist_obs: list[float] = []
    start = max(fast, slow, signal_window, volume_window) + 1
    for i in range(start, n - 1):
        cross_up = float(hist[i]) > 0.0 and float(hist[i - 1]) <= 0.0 and float(macd[i]) > 0.0
        cross_down = float(hist[i]) < 0.0 and float(hist[i - 1]) >= 0.0
        if position > 0.0 and cross_down:
            position = 0.0
        elif position < 0.0 and (not allow_short or cross_up):
            position = 0.0

        short_cross = allow_short and cross_down and float(macd[i]) < 0.0
        if cross_up or short_cross:
            attempted += 1
            vol_ok = float(vol[i] / max(vol_ma[i], 1e-12)) >= min_volume_ratio
            if vol_ok:
                confirmed += 1
                entries += 1
                position = exposure if cross_up else -exposure
                hist_obs.append(float(hist[i]))
        signals[i] = position

    strat = r * signals
    return strat, {
        "macd_entry_count": float(entries),
        "volume_confirmation_ratio": float(confirmed / attempted) if attempted else 0.0,
        "mean_macd_histogram": float(np.mean(hist_obs)) if hist_obs else 0.0,
    }


__all__ = [
    "evaluate_macd_volume_momentum",
    "macd_volume_momentum_returns",
]
