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


def evaluate_ascending_triangle_breakout(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = ascending_triangle_breakout_returns(
        prices,
        params,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
    return _metrics_from_returns(strat, trade_count=extras.get("ascending_triangle_entry_count", 0.0), extras=extras)


def evaluate_bull_flag_continuation(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = bull_flag_continuation_returns(
        prices,
        params,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
    return _metrics_from_returns(strat, trade_count=extras.get("bull_flag_entry_count", 0.0), extras=extras)


def evaluate_support_resistance_retest(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = support_resistance_retest_returns(
        prices,
        params,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
    return _metrics_from_returns(strat, trade_count=extras.get("retest_entry_count", 0.0), extras=extras)


def ascending_triangle_breakout_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Ascending-triangle breakout template with horizontal resistance and rising-low confirmation."""

    r = log_returns(prices)
    n = prices.size
    lookback = int(params.get("lookback", 45))
    min_touches = int(params.get("min_touches", 2))
    resistance_tolerance_pct = float(params.get("resistance_tolerance_pct", 0.018))
    min_low_slope_pct = float(params.get("min_low_slope_pct", 0.00015))
    breakout_buffer = float(params.get("breakout_buffer", 0.0015))
    volume_window = int(params.get("volume_window", 20))
    min_volume_ratio = float(params.get("min_volume_ratio", 1.05))
    exposure = float(params.get("exposure", 0.80))
    max_hold_bars = int(params.get("max_hold_bars", 6))
    if n < max(lookback, volume_window, max_hold_bars) + 5 or r.size == 0:
        return np.zeros_like(r), {
            "ascending_triangle_entry_count": 0.0,
            "resistance_touch_count": 0.0,
            "rising_lows_slope_pct": 0.0,
            "volume_confirmation_ratio": 0.0,
        }

    hi = _coerce_optional(highs, prices)
    lo = _coerce_optional(lows, prices)
    vol = _coerce_optional(volumes, _volume_proxy(prices))
    vol_ma = _rolling_mean(vol, volume_window)
    signals = np.zeros_like(r)
    position = 0.0
    hold = 0
    entries = 0
    attempted = 0
    confirmed = 0
    touch_obs: list[int] = []
    slope_obs: list[float] = []
    start = max(lookback, volume_window)
    for i in range(start, n - 1):
        if position > 0.0:
            hold += 1
            if hold >= max_hold_bars or float(prices[i]) < float(np.mean(prices[i - min(10, lookback) : i])):
                position = 0.0
                hold = 0

        win_hi = hi[i - lookback : i]
        win_lo = lo[i - lookback : i]
        resistance = float(np.max(win_hi))
        touches = int(np.sum(win_hi >= resistance * (1.0 - resistance_tolerance_pct)))
        slope_pct = _linear_slope_pct(win_lo)
        horizontal_ok = touches >= min_touches
        rising_lows = slope_pct >= min_low_slope_pct
        broke = float(prices[i]) > resistance * (1.0 + breakout_buffer)
        if position == 0.0 and horizontal_ok and rising_lows and broke:
            attempted += 1
            touch_obs.append(touches)
            slope_obs.append(slope_pct)
            volume_ok = float(vol[i] / max(vol_ma[i], 1e-12)) >= min_volume_ratio
            if volume_ok:
                confirmed += 1
                entries += 1
                position = exposure
                hold = 0
        signals[i] = position

    strat = r * signals
    return strat, {
        "ascending_triangle_entry_count": float(entries),
        "resistance_touch_count": float(np.mean(touch_obs)) if touch_obs else 0.0,
        "rising_lows_slope_pct": float(np.mean(slope_obs)) if slope_obs else 0.0,
        "volume_confirmation_ratio": float(confirmed / attempted) if attempted else 0.0,
    }


def bull_flag_continuation_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Bull-flag continuation template: impulse leg, shallow drift/pullback, breakout, volume."""

    r = log_returns(prices)
    n = prices.size
    impulse_lookback = int(params.get("impulse_lookback", 18))
    flag_lookback = int(params.get("flag_lookback", 12))
    min_impulse_return = float(params.get("min_impulse_return", 0.06))
    max_flag_depth = float(params.get("max_flag_depth", 0.055))
    breakout_buffer = float(params.get("breakout_buffer", 0.001))
    volume_window = int(params.get("volume_window", 20))
    min_volume_ratio = float(params.get("min_volume_ratio", 1.0))
    exposure = float(params.get("exposure", 0.78))
    max_hold_bars = int(params.get("max_hold_bars", 5))
    if n < impulse_lookback + flag_lookback + max(volume_window, max_hold_bars) + 5 or r.size == 0:
        return np.zeros_like(r), {
            "bull_flag_entry_count": 0.0,
            "mean_impulse_return": 0.0,
            "mean_flag_depth": 0.0,
            "volume_confirmation_ratio": 0.0,
        }

    hi = _coerce_optional(highs, prices)
    vol = _coerce_optional(volumes, _volume_proxy(prices))
    vol_ma = _rolling_mean(vol, volume_window)
    signals = np.zeros_like(r)
    position = 0.0
    hold = 0
    entries = 0
    attempted = 0
    confirmed = 0
    impulses: list[float] = []
    depths: list[float] = []
    start = max(impulse_lookback + flag_lookback, volume_window)
    for i in range(start, n - 1):
        if position > 0.0:
            hold += 1
            if hold >= max_hold_bars:
                position = 0.0
                hold = 0

        impulse_start = i - flag_lookback - impulse_lookback
        flag_start = i - flag_lookback
        impulse_return = float(prices[flag_start] / max(prices[impulse_start], 1e-12) - 1.0)
        flag_high = float(np.max(hi[flag_start:i]))
        flag_low = float(np.min(prices[flag_start:i]))
        flag_depth = (flag_high - flag_low) / max(flag_high, 1e-12)
        flag_slope_pct = _linear_slope_pct(prices[flag_start:i])
        shallow_flag = flag_depth <= max_flag_depth and flag_slope_pct <= 0.0015
        broke = float(prices[i]) > flag_high * (1.0 + breakout_buffer)
        if position == 0.0 and impulse_return >= min_impulse_return and shallow_flag and broke:
            attempted += 1
            impulses.append(impulse_return)
            depths.append(flag_depth)
            volume_ok = float(vol[i] / max(vol_ma[i], 1e-12)) >= min_volume_ratio
            if volume_ok:
                confirmed += 1
                entries += 1
                position = exposure
                hold = 0
        signals[i] = position

    strat = r * signals
    return strat, {
        "bull_flag_entry_count": float(entries),
        "mean_impulse_return": float(np.mean(impulses)) if impulses else 0.0,
        "mean_flag_depth": float(np.mean(depths)) if depths else 0.0,
        "volume_confirmation_ratio": float(confirmed / attempted) if attempted else 0.0,
    }


def support_resistance_retest_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Breakout-retest template: old resistance becomes support, then price reclaims with volume."""

    r = log_returns(prices)
    n = prices.size
    resistance_lookback = int(params.get("resistance_lookback", 35))
    retest_window = int(params.get("retest_window", 8))
    breakout_buffer = float(params.get("breakout_buffer", 0.002))
    retest_band = float(params.get("retest_band", 0.018))
    volume_window = int(params.get("volume_window", 20))
    min_volume_ratio = float(params.get("min_volume_ratio", 0.9))
    exposure = float(params.get("exposure", 0.72))
    max_hold_bars = int(params.get("max_hold_bars", 5))
    if n < resistance_lookback + retest_window + max(volume_window, max_hold_bars) + 5 or r.size == 0:
        return np.zeros_like(r), {
            "retest_entry_count": 0.0,
            "support_retest_count": 0.0,
            "mean_retest_distance_pct": 0.0,
            "volume_confirmation_ratio": 0.0,
        }

    hi = _coerce_optional(highs, prices)
    lo = _coerce_optional(lows, prices)
    vol = _coerce_optional(volumes, _volume_proxy(prices))
    vol_ma = _rolling_mean(vol, volume_window)
    signals = np.zeros_like(r)
    position = 0.0
    hold = 0
    entries = 0
    attempted = 0
    confirmed = 0
    retests = 0
    distances: list[float] = []
    start = max(resistance_lookback + retest_window, volume_window)
    for i in range(start, n - 1):
        if position > 0.0:
            hold += 1
            if hold >= max_hold_bars:
                position = 0.0
                hold = 0

        base_end = i - retest_window
        resistance = float(np.max(hi[base_end - resistance_lookback : base_end]))
        recent_prices = prices[base_end:i]
        broke_before = bool(np.max(recent_prices) > resistance * (1.0 + breakout_buffer))
        touched_support = float(lo[i]) <= resistance * (1.0 + retest_band)
        held_support = float(prices[i]) >= resistance * (1.0 - retest_band)
        reclaimed = float(prices[i]) >= float(prices[i - 1])
        if broke_before and touched_support and held_support and reclaimed and position == 0.0:
            attempted += 1
            retests += 1
            distance = abs(float(prices[i]) - resistance) / max(resistance, 1e-12)
            distances.append(distance)
            volume_ok = float(vol[i] / max(vol_ma[i], 1e-12)) >= min_volume_ratio
            if volume_ok:
                confirmed += 1
                entries += 1
                position = exposure
                hold = 0
        signals[i] = position

    strat = r * signals
    return strat, {
        "retest_entry_count": float(entries),
        "support_retest_count": float(retests),
        "mean_retest_distance_pct": float(np.mean(distances)) if distances else 0.0,
        "volume_confirmation_ratio": float(confirmed / attempted) if attempted else 0.0,
    }


__all__ = [
    "evaluate_ascending_triangle_breakout",
    "evaluate_bull_flag_continuation",
    "evaluate_support_resistance_retest",
    "ascending_triangle_breakout_returns",
    "bull_flag_continuation_returns",
    "support_resistance_retest_returns",
]
