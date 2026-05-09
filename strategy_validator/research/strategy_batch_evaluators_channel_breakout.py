from __future__ import annotations

from typing import Any

import numpy as np

from strategy_validator.research.strategy_batch_evaluators_common import (
    _atr,
    _coerce_optional,
    _ema,
    _metrics_from_returns,
    _rolling_mean,
    _volume_proxy,
    log_returns,
)


def evaluate_donchian_channel_breakout(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = donchian_channel_breakout_returns(
        prices,
        params,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
    return _metrics_from_returns(strat, trade_count=extras.get("donchian_entry_count", 0.0), extras=extras)


def evaluate_atr_trailing_trend(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = atr_trailing_trend_returns(
        prices,
        params,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
    return _metrics_from_returns(strat, trade_count=extras.get("atr_trend_entry_count", 0.0), extras=extras)


def donchian_channel_breakout_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Donchian/Turtle-style channel breakout with volume and ATR sanity filters.

    The template enters only after a close breaks the prior high/low channel;
    it then holds until an opposite exit channel is crossed. This prevents
    one-bar hindsight signals and gives downstream robustness gates a real
    per-bar return stream to inspect.
    """

    r = log_returns(prices)
    n = prices.size
    entry_lookback = int(params.get("entry_lookback", params.get("lookback", 20)))
    exit_lookback = int(params.get("exit_lookback", max(5, entry_lookback // 2)))
    atr_window = int(params.get("atr_window", 14))
    volume_window = int(params.get("volume_window", 20))
    breakout_buffer = float(params.get("breakout_buffer", 0.001))
    min_volume_ratio = float(params.get("min_volume_ratio", 0.9))
    min_atr_pct = float(params.get("min_atr_pct", 0.001))
    exposure = float(params.get("exposure", 0.85))
    allow_short = bool(params.get("allow_short", False))
    if n < max(entry_lookback, exit_lookback, atr_window, volume_window) + 5 or r.size == 0:
        return np.zeros_like(r), {
            "donchian_entry_count": 0.0,
            "channel_width_ratio": 0.0,
            "volume_confirmation_ratio": 0.0,
            "atr_filter_ratio": 0.0,
        }

    hi = _coerce_optional(highs, prices)
    lo = _coerce_optional(lows, prices)
    vol = _coerce_optional(volumes, _volume_proxy(prices))
    vol_ma = _rolling_mean(vol, volume_window)
    atr = _atr(hi, lo, prices, atr_window)
    signals = np.zeros_like(r)
    position = 0.0
    entries = 0
    attempted = 0
    volume_confirmed = 0
    atr_confirmed = 0
    widths: list[float] = []
    start = max(entry_lookback, exit_lookback, atr_window, volume_window)
    for i in range(start, n - 1):
        entry_high = float(np.max(hi[i - entry_lookback : i]))
        entry_low = float(np.min(lo[i - entry_lookback : i]))
        exit_low = float(np.min(lo[i - exit_lookback : i]))
        exit_high = float(np.max(hi[i - exit_lookback : i]))
        widths.append((entry_high - entry_low) / max(float(prices[i]), 1e-12))
        if position > 0.0 and float(prices[i]) < exit_low:
            position = 0.0
        elif position < 0.0 and float(prices[i]) > exit_high:
            position = 0.0

        long_break = float(prices[i]) > entry_high * (1.0 + breakout_buffer)
        short_break = allow_short and float(prices[i]) < entry_low * (1.0 - breakout_buffer)
        if long_break or short_break:
            attempted += 1
            vol_ok = float(vol[i] / max(vol_ma[i], 1e-12)) >= min_volume_ratio
            atr_pct = float(atr[i] / max(prices[i], 1e-12))
            atr_ok = atr_pct >= min_atr_pct
            if vol_ok:
                volume_confirmed += 1
            if atr_ok:
                atr_confirmed += 1
            if vol_ok and atr_ok:
                entries += 1
                position = exposure if long_break else -exposure
        signals[i] = position

    strat = r * signals
    return strat, {
        "donchian_entry_count": float(entries),
        "channel_width_ratio": float(np.mean(widths)) if widths else 0.0,
        "volume_confirmation_ratio": float(volume_confirmed / attempted) if attempted else 0.0,
        "atr_filter_ratio": float(atr_confirmed / attempted) if attempted else 0.0,
    }


def atr_trailing_trend_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """ATR trailing-stop trend template similar to a conservative SuperTrend idea."""

    r = log_returns(prices)
    n = prices.size
    atr_window = int(params.get("atr_window", 14))
    trend_window = int(params.get("trend_window", 30))
    atr_multiplier = float(params.get("atr_multiplier", 2.5))
    min_atr_pct = float(params.get("min_atr_pct", 0.001))
    exposure = float(params.get("exposure", 0.80))
    allow_short = bool(params.get("allow_short", False))
    if n < max(atr_window, trend_window) + 5 or r.size == 0:
        return np.zeros_like(r), {
            "atr_trend_entry_count": 0.0,
            "atr_stop_touch_count": 0.0,
            "mean_atr_pct": 0.0,
        }

    hi = _coerce_optional(highs, prices)
    lo = _coerce_optional(lows, prices)
    atr = _atr(hi, lo, prices, atr_window)
    trend = _ema(prices, trend_window)
    signals = np.zeros_like(r)
    position = 0.0
    long_stop = -float("inf")
    short_stop = float("inf")
    entries = 0
    stops = 0
    atr_pcts: list[float] = []
    start = max(atr_window, trend_window) + 1
    for i in range(start, n - 1):
        atr_i = float(atr[i])
        atr_pct = atr_i / max(float(prices[i]), 1e-12)
        atr_pcts.append(atr_pct)
        if position > 0.0:
            long_stop = max(long_stop, float(prices[i]) - atr_multiplier * atr_i)
            if float(prices[i]) < long_stop:
                position = 0.0
                stops += 1
        elif position < 0.0:
            short_stop = min(short_stop, float(prices[i]) + atr_multiplier * atr_i)
            if float(prices[i]) > short_stop:
                position = 0.0
                stops += 1

        up = float(prices[i]) > float(trend[i]) + 0.25 * atr_i and float(trend[i]) >= float(trend[i - 1])
        down = allow_short and float(prices[i]) < float(trend[i]) - 0.25 * atr_i and float(trend[i]) <= float(trend[i - 1])
        if atr_pct >= min_atr_pct and position == 0.0 and (up or down):
            entries += 1
            if up:
                position = exposure
                long_stop = float(prices[i]) - atr_multiplier * atr_i
            else:
                position = -exposure
                short_stop = float(prices[i]) + atr_multiplier * atr_i
        signals[i] = position

    strat = r * signals
    return strat, {
        "atr_trend_entry_count": float(entries),
        "atr_stop_touch_count": float(stops),
        "mean_atr_pct": float(np.mean(atr_pcts)) if atr_pcts else 0.0,
    }


__all__ = [
    "evaluate_donchian_channel_breakout",
    "evaluate_atr_trailing_trend",
    "donchian_channel_breakout_returns",
    "atr_trailing_trend_returns",
]
