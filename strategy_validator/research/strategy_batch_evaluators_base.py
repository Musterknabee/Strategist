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


__all__ = [
    "evaluate_momentum",
    "evaluate_mean_reversion",
    "evaluate_volatility_breakout",
]
