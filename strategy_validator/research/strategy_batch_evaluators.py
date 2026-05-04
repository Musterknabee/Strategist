"""Deterministic strategy evaluators over OHLCV price paths (research / paper only)."""
from __future__ import annotations

import math
from typing import Any

import numpy as np


def deterministic_prices(*, seed: str, n: int) -> np.ndarray:
    """Length-*n* positive price series; seed mixes batch/strategy/as_of."""

    if n < 8:
        n = 8
    out = np.empty(n, dtype=np.float64)
    out[0] = 100.0
    for i in range(1, n):
        u = _unit_float(f"{seed}:{i}")
        drift = 0.0002 * (u - 0.5)
        out[i] = max(1e-6, out[i - 1] * (1.0 + drift))
    return out


def _unit_float(key: str) -> float:
    import hashlib

    h = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big", signed=False) / float(2**64)


def log_returns(prices: np.ndarray) -> np.ndarray:
    return np.diff(np.log(np.maximum(prices, 1e-12)))


def _rolling_mean(x: np.ndarray, window: int) -> np.ndarray:
    w = max(1, int(window))
    out = np.zeros_like(x, dtype=np.float64)
    for i in range(x.size):
        lo = max(0, i - w + 1)
        out[i] = float(np.mean(x[lo : i + 1]))
    return out


def _rolling_std(x: np.ndarray, window: int) -> np.ndarray:
    w = max(1, int(window))
    out = np.zeros_like(x, dtype=np.float64)
    for i in range(x.size):
        lo = max(0, i - w + 1)
        out[i] = float(np.std(x[lo : i + 1]))
    return out


def _rsi(prices: np.ndarray, window: int) -> np.ndarray:
    """Wilder-style RSI approximation; deterministic and local-window only."""

    w = max(2, int(window))
    out = np.full(prices.size, 50.0, dtype=np.float64)
    if prices.size < w + 2:
        return out
    deltas = np.diff(prices)
    gains = np.maximum(deltas, 0.0)
    losses = np.maximum(-deltas, 0.0)
    for i in range(w, prices.size):
        lo = max(0, i - w)
        g = float(np.mean(gains[lo:i])) if i > lo else 0.0
        l = float(np.mean(losses[lo:i])) if i > lo else 0.0
        if l <= 1e-12:
            out[i] = 100.0 if g > 1e-12 else 50.0
        else:
            rs = g / l
            out[i] = 100.0 - (100.0 / (1.0 + rs))
    return out


def _rolling_vwap(
    prices: np.ndarray,
    volumes: np.ndarray,
    window: int,
    *,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
) -> np.ndarray:
    w = max(2, int(window))
    hi = _coerce_optional(highs, prices)
    lo = _coerce_optional(lows, prices)
    typical = (hi + lo + prices) / 3.0
    out = np.zeros_like(prices, dtype=np.float64)
    for i in range(prices.size):
        start = max(0, i - w + 1)
        v = volumes[start : i + 1]
        tv = typical[start : i + 1] * v
        denom = float(np.sum(v))
        out[i] = float(np.sum(tv) / max(denom, 1e-12))
    return out


def _coerce_optional(values: np.ndarray | None, fallback: np.ndarray) -> np.ndarray:
    if values is None or values.size != fallback.size:
        return fallback.astype(np.float64, copy=True)
    return values.astype(np.float64, copy=True)


def _volume_proxy(prices: np.ndarray) -> np.ndarray:
    """Deterministic synthetic volume proxy for demo paths; never live evidence."""

    r = np.abs(log_returns(prices))
    if r.size == 0:
        return np.ones_like(prices, dtype=np.float64) * 1000.0
    vol = np.empty_like(prices, dtype=np.float64)
    vol[0] = 1000.0
    vol[1:] = 1000.0 * (1.0 + np.minimum(5.0, r / (float(np.std(r)) or 1e-6)))
    return vol


def _empty_metrics() -> dict[str, float]:
    return {
        "total_return": 0.0,
        "volatility": 0.0,
        "max_drawdown": 0.0,
        "sharpe_like": 0.0,
        "trade_count": 0.0,
        "win_rate": 0.0,
    }


def _metrics_from_returns(strat: np.ndarray, *, trade_count: float, extras: dict[str, float] | None = None) -> dict[str, float]:
    if strat.size == 0:
        base = _empty_metrics()
        if extras:
            base.update({k: float(v) for k, v in extras.items()})
        return base
    equity = np.cumprod(np.exp(strat))
    total_return = float(equity[-1] - 1.0) if equity.size else 0.0
    vol = float(np.std(strat) * math.sqrt(252)) if strat.size > 1 else 0.0
    peak = np.maximum.accumulate(equity)
    dd = float(np.max(1.0 - equity / np.maximum(peak, 1e-12))) if equity.size else 0.0
    mu = float(np.mean(strat))
    sd = float(np.std(strat)) or 1e-12
    sharpe = float((mu / sd) * math.sqrt(252)) if strat.size > 2 else 0.0
    active = np.abs(strat) > 1e-12
    wins = float(np.mean(strat[active] > 0)) if np.any(active) else 0.0
    out = {
        "total_return": total_return,
        "volatility": vol,
        "max_drawdown": dd,
        "sharpe_like": sharpe,
        "trade_count": float(trade_count),
        "win_rate": wins,
    }
    if extras:
        out.update({k: float(v) for k, v in extras.items()})
    return out


def evaluate_momentum(prices: np.ndarray, params: dict[str, Any]) -> dict[str, float]:
    window = int(params.get("signal_window", 20))
    r = log_returns(prices)
    if len(r) < window + 2:
        return _empty_metrics()
    sig = np.mean(r[-window:])
    trades = 1.0 if abs(sig) > 1e-6 else 0.0
    strat = r * np.sign(sig) if sig != 0 else r * 0.0
    return _metrics_from_returns(strat, trade_count=trades)


def evaluate_mean_reversion(prices: np.ndarray, params: dict[str, Any]) -> dict[str, float]:
    z_e = float(params.get("z_entry", 1.5))
    w = min(len(prices) - 1, 60)
    if w < 10:
        return _empty_metrics()
    window = prices[-w:]
    mu = float(np.mean(window))
    sd = float(np.std(window)) or 1e-9
    z = (float(prices[-1]) - mu) / sd
    r = log_returns(prices)
    # fade extreme moves
    if z > z_e:
        strat = -r * 0.5
        trades = 1.0
    elif z < -z_e:
        strat = r * 0.5
        trades = 1.0
    else:
        strat = r * 0.0
        trades = 0.0
    return _metrics_from_returns(strat, trade_count=trades)


def evaluate_volatility_breakout(prices: np.ndarray, params: dict[str, Any]) -> dict[str, float]:
    vw = int(params.get("vol_window", 20))
    k = float(params.get("breakout_k", 1.25))
    if len(prices) < vw + 3:
        return _empty_metrics()
    r = log_returns(prices)
    vol = float(np.std(r[-vw:])) or 1e-9
    last = abs(float(r[-1]))
    strat = r * 0.0
    trades = 0.0
    if last > k * vol:
        strat = np.sign(r[-1]) * r * 0.7
        trades = 1.0
    return _metrics_from_returns(strat, trade_count=trades)


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



def _ema(values: np.ndarray, window: int) -> np.ndarray:
    """Deterministic exponential moving average using only current/prior samples."""

    w = max(1, int(window))
    out = np.zeros_like(values, dtype=np.float64)
    if values.size == 0:
        return out
    alpha = 2.0 / float(w + 1)
    out[0] = float(values[0])
    for i in range(1, values.size):
        out[i] = alpha * float(values[i]) + (1.0 - alpha) * float(out[i - 1])
    return out


def _true_range(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> np.ndarray:
    out = np.zeros_like(closes, dtype=np.float64)
    if closes.size == 0:
        return out
    out[0] = max(float(highs[0] - lows[0]), 1e-12)
    for i in range(1, closes.size):
        out[i] = max(
            float(highs[i] - lows[i]),
            abs(float(highs[i] - closes[i - 1])),
            abs(float(lows[i] - closes[i - 1])),
            1e-12,
        )
    return out


def _atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, window: int) -> np.ndarray:
    return _rolling_mean(_true_range(highs, lows, closes), max(1, int(window)))


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


def evaluate_macd_volume_momentum(
    prices: np.ndarray,
    params: dict[str, Any],
    *,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    strat, extras = macd_volume_momentum_returns(prices, params, volumes=volumes)
    return _metrics_from_returns(strat, trade_count=extras.get("macd_entry_count", 0.0), extras=extras)


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


def _linear_slope_pct(values: np.ndarray) -> float:
    if values.size < 3:
        return 0.0
    x = np.arange(values.size, dtype=np.float64)
    xm = float(np.mean(x))
    ym = float(np.mean(values))
    denom = float(np.sum((x - xm) ** 2))
    if denom <= 1e-12:
        return 0.0
    slope = float(np.sum((x - xm) * (values - ym)) / denom)
    return slope / max(abs(ym), 1e-12)


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

def strategy_returns_series(
    prices: np.ndarray,
    strategy_type: str,
    params: dict[str, Any],
    *,
    opens: np.ndarray | None = None,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> np.ndarray:
    """Per-bar strategy log returns aligned with ``log_returns(prices)``."""

    if strategy_type == "momentum":
        window = int(params.get("signal_window", 20))
        r = log_returns(prices)
        if len(r) < window + 2:
            return np.zeros_like(r)
        sig = np.mean(r[-window:])
        return r * float(np.sign(sig)) if sig != 0 else r * 0.0
    if strategy_type == "mean_reversion":
        z_e = float(params.get("z_entry", 1.5))
        r = log_returns(prices)
        w = min(len(prices) - 1, 60)
        if w < 10:
            return np.zeros_like(r)
        window = prices[-w:]
        mu = float(np.mean(window))
        sd = float(np.std(window)) or 1e-9
        z = (float(prices[-1]) - mu) / sd
        if z > z_e:
            return -r * 0.5
        if z < -z_e:
            return r * 0.5
        return r * 0.0
    if strategy_type == "volatility_breakout":
        vw = int(params.get("vol_window", 20))
        k = float(params.get("breakout_k", 1.25))
        r = log_returns(prices)
        if len(prices) < vw + 3:
            return np.zeros_like(r)
        vol = float(np.std(r[-vw:])) or 1e-9
        if abs(float(r[-1])) > k * vol:
            return np.sign(r[-1]) * r * 0.7
        return r * 0.0
    if strategy_type == "moving_average_trend":
        return moving_average_trend_returns(prices, params, volumes=volumes)[0]
    if strategy_type == "trendline_volume_breakout":
        return trendline_volume_breakout_returns(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )[0]
    if strategy_type == "obv_accumulation_breakout":
        return obv_accumulation_breakout_returns(prices, params, volumes=volumes)[0]
    if strategy_type == "rsi_volume_reversal":
        return rsi_volume_reversal_returns(prices, params, volumes=volumes)[0]
    if strategy_type == "bollinger_squeeze_breakout":
        return bollinger_squeeze_breakout_returns(prices, params, volumes=volumes)[0]
    if strategy_type == "vwap_pullback_continuation":
        return vwap_pullback_continuation_returns(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )[0]
    if strategy_type == "donchian_channel_breakout":
        return donchian_channel_breakout_returns(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )[0]
    if strategy_type == "atr_trailing_trend":
        return atr_trailing_trend_returns(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )[0]
    if strategy_type == "macd_volume_momentum":
        return macd_volume_momentum_returns(prices, params, volumes=volumes)[0]
    if strategy_type == "bollinger_mean_reversion":
        return bollinger_mean_reversion_returns(prices, params, volumes=volumes)[0]
    if strategy_type == "vwap_deviation_reversion":
        return vwap_deviation_reversion_returns(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )[0]
    if strategy_type == "keltner_channel_reversion":
        return keltner_channel_reversion_returns(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )[0]
    if strategy_type == "ascending_triangle_breakout":
        return ascending_triangle_breakout_returns(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )[0]
    if strategy_type == "bull_flag_continuation":
        return bull_flag_continuation_returns(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )[0]
    if strategy_type == "support_resistance_retest":
        return support_resistance_retest_returns(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )[0]
    if strategy_type == "bullish_engulfing_volume_reversal":
        return bullish_engulfing_volume_reversal_returns(
            prices,
            params,
            opens=opens,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )[0]
    if strategy_type == "hammer_volume_reversal":
        return hammer_volume_reversal_returns(
            prices,
            params,
            opens=opens,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )[0]
    if strategy_type == "inside_bar_volume_breakout":
        return inside_bar_volume_breakout_returns(
            prices,
            params,
            opens=opens,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )[0]
    raise ValueError(f"UNSUPPORTED_STRATEGY_TYPE:{strategy_type}")


def evaluate_strategy_metrics(
    *,
    strategy_type: str,
    prices: np.ndarray,
    params: dict[str, Any],
    opens: np.ndarray | None = None,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    if strategy_type == "momentum":
        return evaluate_momentum(prices, params)
    if strategy_type == "mean_reversion":
        return evaluate_mean_reversion(prices, params)
    if strategy_type == "volatility_breakout":
        return evaluate_volatility_breakout(prices, params)
    if strategy_type == "moving_average_trend":
        return evaluate_moving_average_trend(prices, params, volumes=volumes)
    if strategy_type == "trendline_volume_breakout":
        return evaluate_trendline_volume_breakout(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )
    if strategy_type == "obv_accumulation_breakout":
        return evaluate_obv_accumulation_breakout(prices, params, volumes=volumes)
    if strategy_type == "rsi_volume_reversal":
        return evaluate_rsi_volume_reversal(prices, params, volumes=volumes)
    if strategy_type == "bollinger_squeeze_breakout":
        return evaluate_bollinger_squeeze_breakout(prices, params, volumes=volumes)
    if strategy_type == "vwap_pullback_continuation":
        return evaluate_vwap_pullback_continuation(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )
    if strategy_type == "donchian_channel_breakout":
        return evaluate_donchian_channel_breakout(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )
    if strategy_type == "atr_trailing_trend":
        return evaluate_atr_trailing_trend(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )
    if strategy_type == "macd_volume_momentum":
        return evaluate_macd_volume_momentum(prices, params, volumes=volumes)
    if strategy_type == "bollinger_mean_reversion":
        return evaluate_bollinger_mean_reversion(prices, params, volumes=volumes)
    if strategy_type == "vwap_deviation_reversion":
        return evaluate_vwap_deviation_reversion(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )
    if strategy_type == "keltner_channel_reversion":
        return evaluate_keltner_channel_reversion(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )
    if strategy_type == "ascending_triangle_breakout":
        return evaluate_ascending_triangle_breakout(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )
    if strategy_type == "bull_flag_continuation":
        return evaluate_bull_flag_continuation(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )
    if strategy_type == "support_resistance_retest":
        return evaluate_support_resistance_retest(
            prices,
            params,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )
    if strategy_type == "bullish_engulfing_volume_reversal":
        return evaluate_bullish_engulfing_volume_reversal(
            prices,
            params,
            opens=opens,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )
    if strategy_type == "hammer_volume_reversal":
        return evaluate_hammer_volume_reversal(
            prices,
            params,
            opens=opens,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )
    if strategy_type == "inside_bar_volume_breakout":
        return evaluate_inside_bar_volume_breakout(
            prices,
            params,
            opens=opens,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )
    raise ValueError(f"UNSUPPORTED_STRATEGY_TYPE:{strategy_type}")


def _signal_transition_count(strat: np.ndarray) -> float:
    if strat.size == 0:
        return 0.0
    active = np.abs(strat) > 1e-12
    if not np.any(active):
        return 0.0
    # proxy: active islands rather than every active bar
    count = 0
    prev = False
    for x in active.tolist():
        if x and not prev:
            count += 1
        prev = bool(x)
    return float(count)


__all__ = [
    "deterministic_prices",
    "evaluate_mean_reversion",
    "evaluate_momentum",
    "evaluate_vwap_pullback_continuation",
    "evaluate_rsi_volume_reversal",
    "evaluate_bollinger_squeeze_breakout",
    "evaluate_donchian_channel_breakout",
    "evaluate_atr_trailing_trend",
    "evaluate_macd_volume_momentum",
    "evaluate_bollinger_mean_reversion",
    "evaluate_vwap_deviation_reversion",
    "evaluate_keltner_channel_reversion",
    "evaluate_ascending_triangle_breakout",
    "evaluate_bull_flag_continuation",
    "evaluate_support_resistance_retest",
    "evaluate_bullish_engulfing_volume_reversal",
    "evaluate_hammer_volume_reversal",
    "evaluate_inside_bar_volume_breakout",
    "evaluate_moving_average_trend",
    "evaluate_obv_accumulation_breakout",
    "evaluate_strategy_metrics",
    "evaluate_trendline_volume_breakout",
    "evaluate_volatility_breakout",
    "log_returns",
    "moving_average_trend_returns",
    "obv_accumulation_breakout_returns",
    "strategy_returns_series",
    "donchian_channel_breakout_returns",
    "atr_trailing_trend_returns",
    "macd_volume_momentum_returns",
    "bollinger_mean_reversion_returns",
    "vwap_deviation_reversion_returns",
    "keltner_channel_reversion_returns",
    "ascending_triangle_breakout_returns",
    "bull_flag_continuation_returns",
    "support_resistance_retest_returns",
    "bullish_engulfing_volume_reversal_returns",
    "hammer_volume_reversal_returns",
    "inside_bar_volume_breakout_returns",
    "vwap_pullback_continuation_returns",
    "rsi_volume_reversal_returns",
    "bollinger_squeeze_breakout_returns",
    "trendline_volume_breakout_returns",
]
