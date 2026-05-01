"""Deterministic toy strategy evaluators over synthetic price paths (demo / paper only)."""
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


def _empty_metrics() -> dict[str, float]:
    return {
        "total_return": 0.0,
        "volatility": 0.0,
        "max_drawdown": 0.0,
        "sharpe_like": 0.0,
        "trade_count": 0.0,
        "win_rate": 0.0,
    }


def _metrics_from_returns(strat: np.ndarray, *, trade_count: float) -> dict[str, float]:
    if strat.size == 0:
        return _empty_metrics()
    equity = np.cumprod(np.exp(strat))
    total_return = float(equity[-1] - 1.0) if equity.size else 0.0
    vol = float(np.std(strat) * math.sqrt(252)) if strat.size > 1 else 0.0
    peak = np.maximum.accumulate(equity)
    dd = float(np.max(1.0 - equity / np.maximum(peak, 1e-12))) if equity.size else 0.0
    mu = float(np.mean(strat))
    sd = float(np.std(strat)) or 1e-12
    sharpe = float((mu / sd) * math.sqrt(252)) if strat.size > 2 else 0.0
    wins = float(np.mean(strat > 0)) if strat.size else 0.0
    return {
        "total_return": total_return,
        "volatility": vol,
        "max_drawdown": dd,
        "sharpe_like": sharpe,
        "trade_count": trade_count,
        "win_rate": wins,
    }


__all__ = [
    "deterministic_prices",
    "evaluate_mean_reversion",
    "evaluate_momentum",
    "evaluate_volatility_breakout",
    "log_returns",
]
