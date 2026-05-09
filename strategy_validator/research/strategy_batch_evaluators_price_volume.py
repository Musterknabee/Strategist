from __future__ import annotations

from typing import Any

import numpy as np

from strategy_validator.research.strategy_batch_evaluators_common import (
    _atr,
    _coerce_optional,
    _empty_metrics,
    _ema,
    _linear_slope_pct,
    _metrics_from_returns,
    _rolling_mean,
    _rolling_std,
    _rolling_vwap,
    _rsi,
    _signal_transition_count,
    _true_range,
    _volume_proxy,
    log_returns,
)


def evaluate_moving_average_trend(prices: np.ndarray, params: dict[str, Any], volumes: np.ndarray | None = None) -> dict[str, float]:
    strat, extras = moving_average_trend_returns(prices, params, volumes=volumes)
    trade_count = _signal_transition_count(strat)
    return _metrics_from_returns(strat, trade_count=trade_count, extras=extras)


def evaluate_trendline_volume_breakout(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = trendline_volume_breakout_returns(
        prices,
        params,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
    return _metrics_from_returns(strat, trade_count=extras.get("breakout_signal_count", 0.0), extras=extras)


def evaluate_obv_accumulation_breakout(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = obv_accumulation_breakout_returns(prices, params, volumes=volumes)
    return _metrics_from_returns(strat, trade_count=extras.get("obv_signal_count", 0.0), extras=extras)


def moving_average_trend_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Trend-following template: fast/slow MA alignment with optional volume confirmation."""

    fast = int(params.get("fast_window", params.get("signal_window", 20)))
    slow = int(params.get("slow_window", 50))
    vol_window = int(params.get("volume_window", 20))
    min_volume_ratio = float(params.get("min_volume_ratio", 1.0))
    exposure = float(params.get("exposure", 0.75))
    allow_short = bool(params.get("allow_short", False))
    r = log_returns(prices)
    n = prices.size
    if n < max(slow, fast, vol_window) + 3 or r.size == 0:
        return np.zeros_like(r), {"volume_confirmation_ratio": 0.0, "trend_signal_count": 0.0}

    vol = _coerce_optional(volumes, _volume_proxy(prices))
    fast_ma = _rolling_mean(prices, fast)
    slow_ma = _rolling_mean(prices, slow)
    vol_ma = _rolling_mean(vol, vol_window)
    signals = np.zeros_like(r)
    confirmed = 0
    eligible = 0
    for i in range(max(slow, fast, vol_window), n - 1):
        direction = 1.0 if fast_ma[i] > slow_ma[i] else (-1.0 if fast_ma[i] < slow_ma[i] and allow_short else 0.0)
        if direction == 0.0:
            continue
        eligible += 1
        vol_ratio = float(vol[i] / max(vol_ma[i], 1e-12))
        if vol_ratio >= min_volume_ratio:
            confirmed += 1
            signals[i] = direction * exposure
    strat = r * signals
    return strat, {
        "volume_confirmation_ratio": float(confirmed / eligible) if eligible else 0.0,
        "trend_signal_count": float(np.count_nonzero(signals)),
    }


def _fit_pivot_line(values: np.ndarray, *, pivot_window: int, min_touches: int, high: bool) -> tuple[float, float, int]:
    pivots: list[tuple[int, float]] = []
    w = max(1, int(pivot_window))
    for i in range(w, values.size - w):
        seg = values[i - w : i + w + 1]
        v = float(values[i])
        if high:
            if v >= float(np.max(seg)):
                pivots.append((i, v))
        else:
            if v <= float(np.min(seg)):
                pivots.append((i, v))
    if len(pivots) >= min_touches:
        recent = pivots[-max(min_touches, min(8, len(pivots))) :]
        x = np.array([p[0] for p in recent], dtype=np.float64)
        y = np.array([p[1] for p in recent], dtype=np.float64)
        x_mean = float(np.mean(x))
        y_mean = float(np.mean(y))
        denom = float(np.sum((x - x_mean) ** 2))
        slope = 0.0 if denom <= 1e-12 else float(np.sum((x - x_mean) * (y - y_mean)) / denom)
        intercept = y_mean - slope * x_mean
        return float(slope), float(intercept), len(recent)
    # Conservative fallback: horizontal support/resistance from the lookback window.
    level = float(np.max(values)) if high else float(np.min(values))
    return 0.0, level, len(pivots)


def trendline_volume_breakout_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Diagonal resistance/support breakout with volume expansion confirmation."""

    r = log_returns(prices)
    n = prices.size
    lookback = int(params.get("lookback", 45))
    pivot_window = int(params.get("pivot_window", 3))
    min_touches = int(params.get("min_touches", 2))
    breakout_buffer = float(params.get("breakout_buffer", 0.0025))
    volume_window = int(params.get("volume_window", 20))
    min_volume_ratio = float(params.get("min_volume_ratio", 1.25))
    exposure = float(params.get("exposure", 0.85))
    allow_short = bool(params.get("allow_short", False))
    if n < max(lookback, volume_window) + 5 or r.size == 0:
        return np.zeros_like(r), {
            "breakout_signal_count": 0.0,
            "trendline_touch_count": 0.0,
            "volume_confirmation_ratio": 0.0,
        }

    hi = _coerce_optional(highs, prices)
    lo = _coerce_optional(lows, prices)
    vol = _coerce_optional(volumes, _volume_proxy(prices))
    vol_ma = _rolling_mean(vol, volume_window)
    signals = np.zeros_like(r)
    touches: list[int] = []
    confirmed = 0
    attempted = 0

    start = max(lookback, volume_window, pivot_window * 2 + 2)
    for i in range(start, n - 1):
        lo_idx = i - lookback
        hi_win = hi[lo_idx:i]
        lo_win = lo[lo_idx:i]
        res_slope, res_intercept, res_touches = _fit_pivot_line(
            hi_win,
            pivot_window=pivot_window,
            min_touches=min_touches,
            high=True,
        )
        sup_slope, sup_intercept, sup_touches = _fit_pivot_line(
            lo_win,
            pivot_window=pivot_window,
            min_touches=min_touches,
            high=False,
        )
        x = hi_win.size
        resistance = res_slope * x + res_intercept
        support = sup_slope * x + sup_intercept
        volume_ok = float(vol[i] / max(vol_ma[i], 1e-12)) >= min_volume_ratio
        long_break = float(prices[i]) > resistance * (1.0 + breakout_buffer)
        short_break = allow_short and float(prices[i]) < support * (1.0 - breakout_buffer)
        if long_break or short_break:
            attempted += 1
            touches.append(max(res_touches, sup_touches))
            if volume_ok:
                confirmed += 1
                signals[i] = exposure if long_break else -exposure

    strat = r * signals
    return strat, {
        "breakout_signal_count": float(np.count_nonzero(signals)),
        "trendline_touch_count": float(np.mean(touches)) if touches else 0.0,
        "volume_confirmation_ratio": float(confirmed / attempted) if attempted else 0.0,
    }


def _obv(prices: np.ndarray, volumes: np.ndarray) -> np.ndarray:
    out = np.zeros_like(prices, dtype=np.float64)
    for i in range(1, prices.size):
        if prices[i] > prices[i - 1]:
            out[i] = out[i - 1] + volumes[i]
        elif prices[i] < prices[i - 1]:
            out[i] = out[i - 1] - volumes[i]
        else:
            out[i] = out[i - 1]
    return out


def obv_accumulation_breakout_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Price breakout confirmed by on-balance-volume accumulation."""

    r = log_returns(prices)
    n = prices.size
    lookback = int(params.get("lookback", 35))
    breakout_buffer = float(params.get("breakout_buffer", 0.0015))
    volume_window = int(params.get("volume_window", 20))
    min_volume_ratio = float(params.get("min_volume_ratio", 1.1))
    exposure = float(params.get("exposure", 0.80))
    if n < max(lookback, volume_window) + 5 or r.size == 0:
        return np.zeros_like(r), {"obv_signal_count": 0.0, "obv_confirmation_ratio": 0.0}
    vol = _coerce_optional(volumes, _volume_proxy(prices))
    obv = _obv(prices, vol)
    vol_ma = _rolling_mean(vol, volume_window)
    signals = np.zeros_like(r)
    attempted = 0
    confirmed = 0
    for i in range(max(lookback, volume_window), n - 1):
        px_break = float(prices[i]) > float(np.max(prices[i - lookback : i])) * (1.0 + breakout_buffer)
        if not px_break:
            continue
        attempted += 1
        obv_confirm = float(obv[i]) >= float(np.max(obv[i - lookback : i]))
        volume_ok = float(vol[i] / max(vol_ma[i], 1e-12)) >= min_volume_ratio
        if obv_confirm and volume_ok:
            confirmed += 1
            signals[i] = exposure
    strat = r * signals
    return strat, {
        "obv_signal_count": float(np.count_nonzero(signals)),
        "obv_confirmation_ratio": float(confirmed / attempted) if attempted else 0.0,
    }


__all__ = [
    "evaluate_moving_average_trend",
    "evaluate_trendline_volume_breakout",
    "evaluate_obv_accumulation_breakout",
    "moving_average_trend_returns",
    "trendline_volume_breakout_returns",
    "obv_accumulation_breakout_returns",
]
