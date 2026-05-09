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
    "log_returns",
]
