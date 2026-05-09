from __future__ import annotations

from typing import Any

import numpy as np

from strategy_validator.research.strategy_batch_evaluators_common import (
    _atr,
    _coerce_optional,
    _ema,
    _metrics_from_returns,
    _rolling_mean,
    _rolling_vwap,
    _rsi,
    _volume_proxy,
    log_returns,
)


def evaluate_bollinger_mean_reversion(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = bollinger_mean_reversion_returns(prices, params, volumes=volumes)
    return _metrics_from_returns(strat, trade_count=extras.get("bollinger_reversion_entry_count", 0.0), extras=extras)


def evaluate_vwap_deviation_reversion(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = vwap_deviation_reversion_returns(
        prices,
        params,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
    return _metrics_from_returns(strat, trade_count=extras.get("vwap_deviation_entry_count", 0.0), extras=extras)


def evaluate_keltner_channel_reversion(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = keltner_channel_reversion_returns(
        prices,
        params,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
    return _metrics_from_returns(strat, trade_count=extras.get("keltner_reversion_entry_count", 0.0), extras=extras)


def bollinger_mean_reversion_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Bollinger-band mean-reversion template with RSI and volume context.

    The evaluator fades statistically stretched closes only after the current
    bar is already observable. The return stream is therefore aligned to the
    next bar and remains valid for PIT batch evidence.
    """

    r = log_returns(prices)
    n = prices.size
    window = int(params.get("window", 20))
    band_k = float(params.get("band_k", 1.8))
    rsi_window = int(params.get("rsi_window", 14))
    volume_window = int(params.get("volume_window", 20))
    oversold = float(params.get("oversold", 38.0))
    overbought = float(params.get("overbought", 62.0))
    min_abs_z = float(params.get("min_abs_z", 1.25))
    min_volume_ratio = float(params.get("min_volume_ratio", 0.70))
    max_hold_bars = int(params.get("max_hold_bars", 4))
    exposure = float(params.get("exposure", 0.65))
    allow_short = bool(params.get("allow_short", False))
    if n < max(window, rsi_window, volume_window, max_hold_bars) + 5 or r.size == 0:
        return np.zeros_like(r), {
            "bollinger_reversion_entry_count": 0.0,
            "mean_entry_zscore": 0.0,
            "volume_confirmation_ratio": 0.0,
            "mean_reversion_exit_count": 0.0,
        }

    vol = _coerce_optional(volumes, _volume_proxy(prices))
    vol_ma = _rolling_mean(vol, volume_window)
    rsi = _rsi(prices, rsi_window)
    signals = np.zeros_like(r)
    position = 0.0
    hold = 0
    entries = 0
    exits = 0
    attempted = 0
    confirmed = 0
    entry_z: list[float] = []
    start = max(window, rsi_window, volume_window)
    for i in range(start, n - 1):
        seg = prices[i - window : i]
        mid = float(np.mean(seg))
        sd = float(np.std(seg)) or 1e-12
        upper = mid + band_k * sd
        lower = mid - band_k * sd
        z = (float(prices[i]) - mid) / sd
        if position > 0.0:
            hold += 1
            if float(prices[i]) >= mid or hold >= max_hold_bars:
                position = 0.0
                hold = 0
                exits += 1
        elif position < 0.0:
            hold += 1
            if float(prices[i]) <= mid or hold >= max_hold_bars:
                position = 0.0
                hold = 0
                exits += 1

        long_signal = float(prices[i]) <= lower and z <= -min_abs_z and float(rsi[i]) <= oversold
        short_signal = allow_short and float(prices[i]) >= upper and z >= min_abs_z and float(rsi[i]) >= overbought
        if position == 0.0 and (long_signal or short_signal):
            attempted += 1
            volume_ok = float(vol[i] / max(vol_ma[i], 1e-12)) >= min_volume_ratio
            if volume_ok:
                confirmed += 1
                entries += 1
                entry_z.append(z)
                position = exposure if long_signal else -exposure
                hold = 0
        signals[i] = position

    strat = r * signals
    return strat, {
        "bollinger_reversion_entry_count": float(entries),
        "mean_entry_zscore": float(np.mean(entry_z)) if entry_z else 0.0,
        "volume_confirmation_ratio": float(confirmed / attempted) if attempted else 0.0,
        "mean_reversion_exit_count": float(exits),
    }


def vwap_deviation_reversion_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Rolling-VWAP deviation mean-reversion template.

    The strategy enters after a stretched close starts to recover back toward
    rolling VWAP and exits on VWAP touch/reclaim or a bounded holding period.
    """

    r = log_returns(prices)
    n = prices.size
    vwap_window = int(params.get("vwap_window", 24))
    deviation_window = int(params.get("deviation_window", 24))
    volume_window = int(params.get("volume_window", 20))
    min_deviation_pct = float(params.get("min_deviation_pct", 0.012))
    recovery_buffer = float(params.get("recovery_buffer", 0.0005))
    min_volume_ratio = float(params.get("min_volume_ratio", 0.70))
    max_hold_bars = int(params.get("max_hold_bars", 5))
    exposure = float(params.get("exposure", 0.70))
    allow_short = bool(params.get("allow_short", False))
    if n < max(vwap_window, deviation_window, volume_window, max_hold_bars) + 5 or r.size == 0:
        return np.zeros_like(r), {
            "vwap_deviation_entry_count": 0.0,
            "mean_vwap_deviation": 0.0,
            "vwap_reversion_exit_count": 0.0,
            "volume_confirmation_ratio": 0.0,
        }

    vol = _coerce_optional(volumes, _volume_proxy(prices))
    vwap = _rolling_vwap(prices, vol, vwap_window, highs=highs, lows=lows)
    vol_ma = _rolling_mean(vol, volume_window)
    signals = np.zeros_like(r)
    position = 0.0
    hold = 0
    entries = 0
    exits = 0
    attempted = 0
    confirmed = 0
    deviations: list[float] = []
    start = max(vwap_window, deviation_window, volume_window) + 1
    for i in range(start, n - 1):
        vw = float(vwap[i])
        deviation = (float(prices[i]) - vw) / max(abs(vw), 1e-12)
        if position > 0.0:
            hold += 1
            if float(prices[i]) >= vw or hold >= max_hold_bars:
                position = 0.0
                hold = 0
                exits += 1
        elif position < 0.0:
            hold += 1
            if float(prices[i]) <= vw or hold >= max_hold_bars:
                position = 0.0
                hold = 0
                exits += 1

        recovering_long = float(prices[i]) > float(prices[i - 1]) * (1.0 + recovery_buffer)
        rejecting_short = allow_short and float(prices[i]) < float(prices[i - 1]) * (1.0 - recovery_buffer)
        long_signal = deviation <= -min_deviation_pct and recovering_long
        short_signal = allow_short and deviation >= min_deviation_pct and rejecting_short
        if position == 0.0 and (long_signal or short_signal):
            attempted += 1
            volume_ok = float(vol[i] / max(vol_ma[i], 1e-12)) >= min_volume_ratio
            if volume_ok:
                confirmed += 1
                entries += 1
                deviations.append(abs(deviation))
                position = exposure if long_signal else -exposure
                hold = 0
        signals[i] = position

    strat = r * signals
    return strat, {
        "vwap_deviation_entry_count": float(entries),
        "mean_vwap_deviation": float(np.mean(deviations)) if deviations else 0.0,
        "vwap_reversion_exit_count": float(exits),
        "volume_confirmation_ratio": float(confirmed / attempted) if attempted else 0.0,
    }


def keltner_channel_reversion_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Keltner-channel range-fade template using EMA/ATR envelopes.

    It is deliberately conservative: entries require a channel breach plus RSI
    exhaustion and volume participation, then exits at the center EMA or after a
    bounded hold period.
    """

    r = log_returns(prices)
    n = prices.size
    ema_window = int(params.get("ema_window", 20))
    atr_window = int(params.get("atr_window", 14))
    rsi_window = int(params.get("rsi_window", 14))
    volume_window = int(params.get("volume_window", 20))
    atr_multiplier = float(params.get("atr_multiplier", 1.35))
    oversold = float(params.get("oversold", 40.0))
    overbought = float(params.get("overbought", 60.0))
    min_volume_ratio = float(params.get("min_volume_ratio", 0.70))
    max_hold_bars = int(params.get("max_hold_bars", 5))
    exposure = float(params.get("exposure", 0.65))
    allow_short = bool(params.get("allow_short", False))
    if n < max(ema_window, atr_window, rsi_window, volume_window, max_hold_bars) + 5 or r.size == 0:
        return np.zeros_like(r), {
            "keltner_reversion_entry_count": 0.0,
            "mean_channel_deviation": 0.0,
            "keltner_reversion_exit_count": 0.0,
            "volume_confirmation_ratio": 0.0,
        }

    hi = _coerce_optional(highs, prices)
    lo = _coerce_optional(lows, prices)
    vol = _coerce_optional(volumes, _volume_proxy(prices))
    ema = _ema(prices, ema_window)
    atr = _atr(hi, lo, prices, atr_window)
    rsi = _rsi(prices, rsi_window)
    vol_ma = _rolling_mean(vol, volume_window)
    signals = np.zeros_like(r)
    position = 0.0
    hold = 0
    entries = 0
    exits = 0
    attempted = 0
    confirmed = 0
    deviations: list[float] = []
    start = max(ema_window, atr_window, rsi_window, volume_window)
    for i in range(start, n - 1):
        center = float(ema[i])
        atr_i = float(atr[i])
        upper = center + atr_multiplier * atr_i
        lower = center - atr_multiplier * atr_i
        if position > 0.0:
            hold += 1
            if float(prices[i]) >= center or hold >= max_hold_bars:
                position = 0.0
                hold = 0
                exits += 1
        elif position < 0.0:
            hold += 1
            if float(prices[i]) <= center or hold >= max_hold_bars:
                position = 0.0
                hold = 0
                exits += 1

        long_signal = float(prices[i]) <= lower and float(rsi[i]) <= oversold
        short_signal = allow_short and float(prices[i]) >= upper and float(rsi[i]) >= overbought
        if position == 0.0 and (long_signal or short_signal):
            attempted += 1
            volume_ok = float(vol[i] / max(vol_ma[i], 1e-12)) >= min_volume_ratio
            if volume_ok:
                confirmed += 1
                entries += 1
                deviations.append(abs(float(prices[i]) - center) / max(atr_i, 1e-12))
                position = exposure if long_signal else -exposure
                hold = 0
        signals[i] = position

    strat = r * signals
    return strat, {
        "keltner_reversion_entry_count": float(entries),
        "mean_channel_deviation": float(np.mean(deviations)) if deviations else 0.0,
        "keltner_reversion_exit_count": float(exits),
        "volume_confirmation_ratio": float(confirmed / attempted) if attempted else 0.0,
    }


__all__ = [
    "evaluate_bollinger_mean_reversion",
    "evaluate_vwap_deviation_reversion",
    "evaluate_keltner_channel_reversion",
    "bollinger_mean_reversion_returns",
    "vwap_deviation_reversion_returns",
    "keltner_channel_reversion_returns",
]
