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


def evaluate_bullish_engulfing_volume_reversal(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    opens: np.ndarray | None = None,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = bullish_engulfing_volume_reversal_returns(
        prices,
        params,
        opens=opens,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
    return _metrics_from_returns(strat, trade_count=extras.get("bullish_engulfing_entry_count", 0.0), extras=extras)


def evaluate_hammer_volume_reversal(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    opens: np.ndarray | None = None,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = hammer_volume_reversal_returns(
        prices,
        params,
        opens=opens,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
    return _metrics_from_returns(strat, trade_count=extras.get("hammer_entry_count", 0.0), extras=extras)


def evaluate_inside_bar_volume_breakout(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    opens: np.ndarray | None = None,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = inside_bar_volume_breakout_returns(
        prices,
        params,
        opens=opens,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
    return _metrics_from_returns(strat, trade_count=extras.get("inside_bar_breakout_entry_count", 0.0), extras=extras)


def _body_size(opens: np.ndarray, closes: np.ndarray) -> np.ndarray:
    return np.abs(closes - opens)


def bullish_engulfing_volume_reversal_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    opens: np.ndarray | None = None,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Bullish engulfing reversal template with downtrend and volume confirmation.

    The signal requires a red candle followed by a green candle whose real body
    engulfs the prior real body, after a negative short lookback return. It is
    deliberately long-only and paper/research scoped.
    """

    r = log_returns(prices)
    n = prices.size
    trend_lookback = int(params.get("trend_lookback", 8))
    volume_window = int(params.get("volume_window", 20))
    min_downtrend_return = float(params.get("min_downtrend_return", -0.035))
    min_volume_ratio = float(params.get("min_volume_ratio", 1.05))
    min_body_ratio = float(params.get("min_body_ratio", 1.05))
    exposure = float(params.get("exposure", 0.70))
    max_hold_bars = int(params.get("max_hold_bars", 4))
    if n < max(trend_lookback, volume_window, max_hold_bars) + 5 or r.size == 0:
        return np.zeros_like(r), {
            "bullish_engulfing_entry_count": 0.0,
            "mean_prior_downtrend_return": 0.0,
            "mean_engulfing_body_ratio": 0.0,
            "volume_confirmation_ratio": 0.0,
        }

    op = _coerce_optional(opens, prices)
    vol = _coerce_optional(volumes, _volume_proxy(prices))
    vol_ma = _rolling_mean(vol, volume_window)
    body = _body_size(op, prices)
    signals = np.zeros_like(r)
    position = 0.0
    hold = 0
    entries = 0
    attempted = 0
    confirmed = 0
    down_obs: list[float] = []
    ratio_obs: list[float] = []
    start = max(trend_lookback, volume_window, 2)
    for i in range(start, n - 1):
        if position > 0.0:
            hold += 1
            if hold >= max_hold_bars:
                position = 0.0
                hold = 0

        prior_down = float(prices[i - 1] / max(prices[i - trend_lookback], 1e-12) - 1.0)
        prev_red = float(prices[i - 1]) < float(op[i - 1])
        curr_green = float(prices[i]) > float(op[i])
        engulfed = float(op[i]) <= float(prices[i - 1]) and float(prices[i]) >= float(op[i - 1])
        body_ratio = float(body[i] / max(body[i - 1], 1e-12))
        if position == 0.0 and prior_down <= min_downtrend_return and prev_red and curr_green and engulfed and body_ratio >= min_body_ratio:
            attempted += 1
            down_obs.append(prior_down)
            ratio_obs.append(body_ratio)
            volume_ok = float(vol[i] / max(vol_ma[i], 1e-12)) >= min_volume_ratio
            if volume_ok:
                confirmed += 1
                entries += 1
                position = exposure
                hold = 0
        signals[i] = position

    strat = r * signals
    return strat, {
        "bullish_engulfing_entry_count": float(entries),
        "mean_prior_downtrend_return": float(np.mean(down_obs)) if down_obs else 0.0,
        "mean_engulfing_body_ratio": float(np.mean(ratio_obs)) if ratio_obs else 0.0,
        "volume_confirmation_ratio": float(confirmed / attempted) if attempted else 0.0,
    }


def hammer_volume_reversal_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    opens: np.ndarray | None = None,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Hammer reversal template: long lower wick after downtrend, confirmed by volume."""

    r = log_returns(prices)
    n = prices.size
    trend_lookback = int(params.get("trend_lookback", 8))
    volume_window = int(params.get("volume_window", 20))
    min_downtrend_return = float(params.get("min_downtrend_return", -0.03))
    min_lower_shadow_ratio = float(params.get("min_lower_shadow_ratio", 2.0))
    max_upper_shadow_ratio = float(params.get("max_upper_shadow_ratio", 0.80))
    min_volume_ratio = float(params.get("min_volume_ratio", 1.0))
    exposure = float(params.get("exposure", 0.65))
    max_hold_bars = int(params.get("max_hold_bars", 4))
    if n < max(trend_lookback, volume_window, max_hold_bars) + 5 or r.size == 0:
        return np.zeros_like(r), {
            "hammer_entry_count": 0.0,
            "mean_lower_shadow_ratio": 0.0,
            "mean_prior_downtrend_return": 0.0,
            "volume_confirmation_ratio": 0.0,
        }

    op = _coerce_optional(opens, prices)
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
    shadow_obs: list[float] = []
    down_obs: list[float] = []
    start = max(trend_lookback, volume_window, 2)
    for i in range(start, n - 1):
        if position > 0.0:
            hold += 1
            if hold >= max_hold_bars:
                position = 0.0
                hold = 0

        prior_down = float(prices[i - 1] / max(prices[i - trend_lookback], 1e-12) - 1.0)
        real_body = max(abs(float(prices[i]) - float(op[i])), max(float(prices[i]) * 0.001, 1e-12))
        lower_shadow = min(float(op[i]), float(prices[i])) - float(lo[i])
        upper_shadow = float(hi[i]) - max(float(op[i]), float(prices[i]))
        lower_ratio = lower_shadow / real_body
        upper_ratio = upper_shadow / real_body
        closed_off_low = float(prices[i]) > float(lo[i]) + 0.55 * max(float(hi[i]) - float(lo[i]), 1e-12)
        if (
            position == 0.0
            and prior_down <= min_downtrend_return
            and lower_ratio >= min_lower_shadow_ratio
            and upper_ratio <= max_upper_shadow_ratio
            and closed_off_low
        ):
            attempted += 1
            shadow_obs.append(lower_ratio)
            down_obs.append(prior_down)
            volume_ok = float(vol[i] / max(vol_ma[i], 1e-12)) >= min_volume_ratio
            if volume_ok:
                confirmed += 1
                entries += 1
                position = exposure
                hold = 0
        signals[i] = position

    strat = r * signals
    return strat, {
        "hammer_entry_count": float(entries),
        "mean_lower_shadow_ratio": float(np.mean(shadow_obs)) if shadow_obs else 0.0,
        "mean_prior_downtrend_return": float(np.mean(down_obs)) if down_obs else 0.0,
        "volume_confirmation_ratio": float(confirmed / attempted) if attempted else 0.0,
    }


def inside_bar_volume_breakout_returns(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    opens: np.ndarray | None = None,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> tuple[np.ndarray, dict[str, float]]:
    """Inside-bar compression breakout template with volume confirmation."""

    r = log_returns(prices)
    n = prices.size
    cluster_window = int(params.get("cluster_window", 4))
    volume_window = int(params.get("volume_window", 20))
    breakout_buffer = float(params.get("breakout_buffer", 0.001))
    min_volume_ratio = float(params.get("min_volume_ratio", 1.0))
    min_trend_return = float(params.get("min_trend_return", 0.015))
    trend_lookback = int(params.get("trend_lookback", 12))
    exposure = float(params.get("exposure", 0.68))
    max_hold_bars = int(params.get("max_hold_bars", 4))
    if n < max(cluster_window + 2, volume_window, trend_lookback, max_hold_bars) + 5 or r.size == 0:
        return np.zeros_like(r), {
            "inside_bar_breakout_entry_count": 0.0,
            "inside_bar_cluster_count": 0.0,
            "mean_breakout_volume_ratio": 0.0,
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
    clusters = 0
    vol_obs: list[float] = []
    start = max(cluster_window + 2, volume_window, trend_lookback)
    for i in range(start, n - 1):
        if position > 0.0:
            hold += 1
            if hold >= max_hold_bars:
                position = 0.0
                hold = 0

        mother_idx = i - cluster_window - 1
        mother_high = float(hi[mother_idx])
        mother_low = float(lo[mother_idx])
        inside = True
        for j in range(mother_idx + 1, i):
            if float(hi[j]) > mother_high or float(lo[j]) < mother_low:
                inside = False
                break
        prior_trend = float(prices[i - 1] / max(prices[i - trend_lookback], 1e-12) - 1.0)
        breakout = float(prices[i]) > mother_high * (1.0 + breakout_buffer)
        if position == 0.0 and inside and prior_trend >= min_trend_return and breakout:
            attempted += 1
            clusters += 1
            vol_ratio = float(vol[i] / max(vol_ma[i], 1e-12))
            if vol_ratio >= min_volume_ratio:
                confirmed += 1
                entries += 1
                vol_obs.append(vol_ratio)
                position = exposure
                hold = 0
        signals[i] = position

    strat = r * signals
    return strat, {
        "inside_bar_breakout_entry_count": float(entries),
        "inside_bar_cluster_count": float(clusters),
        "mean_breakout_volume_ratio": float(np.mean(vol_obs)) if vol_obs else 0.0,
        "volume_confirmation_ratio": float(confirmed / attempted) if attempted else 0.0,
    }


__all__ = [
    "evaluate_bullish_engulfing_volume_reversal",
    "evaluate_hammer_volume_reversal",
    "evaluate_inside_bar_volume_breakout",
    "bullish_engulfing_volume_reversal_returns",
    "hammer_volume_reversal_returns",
    "inside_bar_volume_breakout_returns",
]
