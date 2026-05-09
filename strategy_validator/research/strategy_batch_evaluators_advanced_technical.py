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


def evaluate_rsi_volume_reversal(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = rsi_volume_reversal_returns(prices, params, volumes=volumes)
    return _metrics_from_returns(strat, trade_count=extras.get("rsi_reversal_signal_count", 0.0), extras=extras)


def evaluate_bollinger_squeeze_breakout(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = bollinger_squeeze_breakout_returns(prices, params, volumes=volumes)
    return _metrics_from_returns(strat, trade_count=extras.get("squeeze_breakout_signal_count", 0.0), extras=extras)


def evaluate_vwap_pullback_continuation(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = vwap_pullback_continuation_returns(
        prices,
        params,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
    return _metrics_from_returns(strat, trade_count=extras.get("vwap_pullback_signal_count", 0.0), extras=extras)


def rsi_volume_reversal_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """RSI exhaustion reversal template confirmed by volume expansion.

    Signals are emitted for the next bar only after the current close has recovered
    from an oversold/overbought zone. This keeps the evaluator deterministic and
    avoids using future bars to decide entries.
    """

    r = log_returns(prices)
    n = prices.size
    rsi_window = int(params.get("rsi_window", 14))
    volume_window = int(params.get("volume_window", 20))
    lookback = int(params.get("lookback", 12))
    oversold = float(params.get("oversold", 32.0))
    overbought = float(params.get("overbought", 68.0))
    min_volume_ratio = float(params.get("min_volume_ratio", 1.1))
    recovery_buffer = float(params.get("recovery_buffer", 0.002))
    exposure = float(params.get("exposure", 0.70))
    allow_short = bool(params.get("allow_short", False))
    if n < max(rsi_window, volume_window, lookback) + 5 or r.size == 0:
        return np.zeros_like(r), {
            "rsi_reversal_signal_count": 0.0,
            "volume_confirmation_ratio": 0.0,
            "mean_entry_rsi": 0.0,
        }

    vol = _coerce_optional(volumes, _volume_proxy(prices))
    vol_ma = _rolling_mean(vol, volume_window)
    rsi = _rsi(prices, rsi_window)
    signals = np.zeros_like(r)
    attempted = 0
    confirmed = 0
    entry_rsis: list[float] = []
    start = max(rsi_window + 1, volume_window, lookback)
    for i in range(start, n - 1):
        recent_rsi = rsi[max(0, i - lookback) : i + 1]
        volume_ok = float(vol[i] / max(vol_ma[i], 1e-12)) >= min_volume_ratio
        recent_low = float(np.min(prices[i - lookback : i]))
        long_recovery = (
            float(rsi[i - 1]) <= oversold
            and float(rsi[i]) > float(rsi[i - 1])
            and float(prices[i]) > recent_low * (1.0 + recovery_buffer)
        )
        recent_high = float(np.max(prices[i - lookback : i]))
        short_rejection = (
            allow_short
            and float(rsi[i - 1]) >= overbought
            and float(rsi[i]) < float(rsi[i - 1])
            and float(prices[i]) < recent_high * (1.0 - recovery_buffer)
        )
        if long_recovery or short_rejection:
            attempted += 1
            if volume_ok:
                confirmed += 1
                entry_rsis.append(float(rsi[i]))
                signals[i] = exposure if long_recovery else -exposure
    strat = r * signals
    return strat, {
        "rsi_reversal_signal_count": float(np.count_nonzero(signals)),
        "volume_confirmation_ratio": float(confirmed / attempted) if attempted else 0.0,
        "mean_entry_rsi": float(np.mean(entry_rsis)) if entry_rsis else 0.0,
    }


def bollinger_squeeze_breakout_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Bollinger-band squeeze expansion with volume-confirmed breakout."""

    r = log_returns(prices)
    n = prices.size
    window = int(params.get("window", 20))
    squeeze_lookback = int(params.get("squeeze_lookback", 12))
    band_k = float(params.get("band_k", 2.0))
    max_squeeze_width = float(params.get("max_squeeze_width", 0.06))
    breakout_buffer = float(params.get("breakout_buffer", 0.001))
    volume_window = int(params.get("volume_window", 20))
    min_volume_ratio = float(params.get("min_volume_ratio", 1.1))
    exposure = float(params.get("exposure", 0.80))
    allow_short = bool(params.get("allow_short", False))
    if n < max(window, squeeze_lookback, volume_window) + 5 or r.size == 0:
        return np.zeros_like(r), {
            "squeeze_breakout_signal_count": 0.0,
            "squeeze_observation_count": 0.0,
            "volume_confirmation_ratio": 0.0,
        }

    vol = _coerce_optional(volumes, _volume_proxy(prices))
    vol_ma = _rolling_mean(vol, volume_window)
    signals = np.zeros_like(r)
    attempted = 0
    confirmed = 0
    squeezes = 0
    start = max(window + squeeze_lookback, volume_window)
    for i in range(start, n - 1):
        widths: list[float] = []
        for j in range(i - squeeze_lookback, i):
            seg = prices[j - window : j]
            if seg.size < window:
                continue
            mid_j = float(np.mean(seg))
            sd_j = float(np.std(seg))
            widths.append(float((2.0 * band_k * sd_j) / max(abs(mid_j), 1e-12)))
        if not widths or min(widths) > max_squeeze_width:
            continue
        squeezes += 1
        seg = prices[i - window : i]
        mid = float(np.mean(seg))
        sd = float(np.std(seg))
        upper = mid + band_k * sd
        lower = mid - band_k * sd
        long_break = float(prices[i]) > upper * (1.0 + breakout_buffer)
        short_break = allow_short and float(prices[i]) < lower * (1.0 - breakout_buffer)
        if long_break or short_break:
            attempted += 1
            volume_ok = float(vol[i] / max(vol_ma[i], 1e-12)) >= min_volume_ratio
            if volume_ok:
                confirmed += 1
                signals[i] = exposure if long_break else -exposure
    strat = r * signals
    return strat, {
        "squeeze_breakout_signal_count": float(np.count_nonzero(signals)),
        "squeeze_observation_count": float(squeezes),
        "volume_confirmation_ratio": float(confirmed / attempted) if attempted else 0.0,
    }


def vwap_pullback_continuation_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Rolling-VWAP pullback continuation template.

    The signal requires an established trend, a pullback into the VWAP area, and
    a close back above VWAP with volume participation.
    """

    r = log_returns(prices)
    n = prices.size
    vwap_window = int(params.get("vwap_window", 20))
    trend_window = int(params.get("trend_window", 35))
    volume_window = int(params.get("volume_window", 20))
    pullback_band = float(params.get("pullback_band", 0.012))
    resume_buffer = float(params.get("resume_buffer", 0.001))
    min_volume_ratio = float(params.get("min_volume_ratio", 0.95))
    exposure = float(params.get("exposure", 0.75))
    allow_short = bool(params.get("allow_short", False))
    if n < max(vwap_window, trend_window, volume_window) + 5 or r.size == 0:
        return np.zeros_like(r), {
            "vwap_pullback_signal_count": 0.0,
            "vwap_reclaim_ratio": 0.0,
            "volume_confirmation_ratio": 0.0,
        }

    vol = _coerce_optional(volumes, _volume_proxy(prices))
    vwap = _rolling_vwap(prices, vol, vwap_window, highs=highs, lows=lows)
    vol_ma = _rolling_mean(vol, volume_window)
    trend_ma = _rolling_mean(prices, trend_window)
    signals = np.zeros_like(r)
    attempted = 0
    confirmed = 0
    reclaim_count = 0
    start = max(vwap_window, trend_window, volume_window) + 1
    for i in range(start, n - 1):
        uptrend = float(prices[i]) > float(trend_ma[i]) and float(trend_ma[i]) >= float(trend_ma[i - 3])
        downtrend = allow_short and float(prices[i]) < float(trend_ma[i]) and float(trend_ma[i]) <= float(trend_ma[i - 3])
        pulled_back_long = float(prices[i - 1]) <= float(vwap[i - 1]) * (1.0 + pullback_band)
        reclaimed_long = float(prices[i]) >= float(vwap[i]) * (1.0 + resume_buffer)
        rejected_short = allow_short and float(prices[i]) <= float(vwap[i]) * (1.0 - resume_buffer)
        pulled_back_short = allow_short and float(prices[i - 1]) >= float(vwap[i - 1]) * (1.0 - pullback_band)
        long_signal = uptrend and pulled_back_long and reclaimed_long
        short_signal = downtrend and pulled_back_short and rejected_short
        if long_signal or short_signal:
            attempted += 1
            if long_signal:
                reclaim_count += 1
            volume_ok = float(vol[i] / max(vol_ma[i], 1e-12)) >= min_volume_ratio
            if volume_ok:
                confirmed += 1
                signals[i] = exposure if long_signal else -exposure
    strat = r * signals
    return strat, {
        "vwap_pullback_signal_count": float(np.count_nonzero(signals)),
        "vwap_reclaim_ratio": float(reclaim_count / attempted) if attempted else 0.0,
        "volume_confirmation_ratio": float(confirmed / attempted) if attempted else 0.0,
    }


__all__ = [
    "evaluate_rsi_volume_reversal",
    "evaluate_bollinger_squeeze_breakout",
    "evaluate_vwap_pullback_continuation",
    "rsi_volume_reversal_returns",
    "bollinger_squeeze_breakout_returns",
    "vwap_pullback_continuation_returns",
]
