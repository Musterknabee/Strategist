"""Central registry for strategy-type → evaluator dispatch (research / paper only).

Dispatch tables live here so `strategy_batch_evaluators.py` can stay focused on
deterministic math and per-strategy implementations without giant if-chains.
"""
from __future__ import annotations

from typing import Any, Final

import numpy as np

SUPPORTED_STRATEGY_TYPES: Final[frozenset[str]] = frozenset(
    {
        "momentum",
        "mean_reversion",
        "volatility_breakout",
        "moving_average_trend",
        "trendline_volume_breakout",
        "obv_accumulation_breakout",
        "rsi_volume_reversal",
        "bollinger_squeeze_breakout",
        "vwap_pullback_continuation",
        "donchian_channel_breakout",
        "atr_trailing_trend",
        "macd_volume_momentum",
        "bollinger_mean_reversion",
        "vwap_deviation_reversion",
        "keltner_channel_reversion",
        "ascending_triangle_breakout",
        "bull_flag_continuation",
        "support_resistance_retest",
        "bullish_engulfing_volume_reversal",
        "hammer_volume_reversal",
        "inside_bar_volume_breakout",
    }
)


def dispatch_strategy_returns_series(
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
    import strategy_validator.research.strategy_batch_evaluators as ev

    if strategy_type == "momentum":
        window = int(params.get("signal_window", 20))
        r = ev.log_returns(prices)
        if len(r) < window + 2:
            return np.zeros_like(r)
        sig = np.mean(r[-window:])
        return r * float(np.sign(sig)) if sig != 0 else r * 0.0
    if strategy_type == "mean_reversion":
        z_e = float(params.get("z_entry", 1.5))
        r = ev.log_returns(prices)
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
        r = ev.log_returns(prices)
        if len(prices) < vw + 3:
            return np.zeros_like(r)
        vol = float(np.std(r[-vw:])) or 1e-9
        if abs(float(r[-1])) > k * vol:
            return np.sign(r[-1]) * r * 0.7
        return r * 0.0
    if strategy_type == "moving_average_trend":
        return ev.moving_average_trend_returns(prices, params, volumes=volumes)[0]
    if strategy_type == "trendline_volume_breakout":
        return ev.trendline_volume_breakout_returns(prices, params, highs=highs, lows=lows, volumes=volumes)[0]
    if strategy_type == "obv_accumulation_breakout":
        return ev.obv_accumulation_breakout_returns(prices, params, volumes=volumes)[0]
    if strategy_type == "rsi_volume_reversal":
        return ev.rsi_volume_reversal_returns(prices, params, volumes=volumes)[0]
    if strategy_type == "bollinger_squeeze_breakout":
        return ev.bollinger_squeeze_breakout_returns(prices, params, volumes=volumes)[0]
    if strategy_type == "vwap_pullback_continuation":
        return ev.vwap_pullback_continuation_returns(prices, params, highs=highs, lows=lows, volumes=volumes)[0]
    if strategy_type == "donchian_channel_breakout":
        return ev.donchian_channel_breakout_returns(prices, params, highs=highs, lows=lows, volumes=volumes)[0]
    if strategy_type == "atr_trailing_trend":
        return ev.atr_trailing_trend_returns(prices, params, highs=highs, lows=lows, volumes=volumes)[0]
    if strategy_type == "macd_volume_momentum":
        return ev.macd_volume_momentum_returns(prices, params, volumes=volumes)[0]
    if strategy_type == "bollinger_mean_reversion":
        return ev.bollinger_mean_reversion_returns(prices, params, volumes=volumes)[0]
    if strategy_type == "vwap_deviation_reversion":
        return ev.vwap_deviation_reversion_returns(prices, params, highs=highs, lows=lows, volumes=volumes)[0]
    if strategy_type == "keltner_channel_reversion":
        return ev.keltner_channel_reversion_returns(prices, params, highs=highs, lows=lows, volumes=volumes)[0]
    if strategy_type == "ascending_triangle_breakout":
        return ev.ascending_triangle_breakout_returns(prices, params, highs=highs, lows=lows, volumes=volumes)[0]
    if strategy_type == "bull_flag_continuation":
        return ev.bull_flag_continuation_returns(prices, params, highs=highs, lows=lows, volumes=volumes)[0]
    if strategy_type == "support_resistance_retest":
        return ev.support_resistance_retest_returns(prices, params, highs=highs, lows=lows, volumes=volumes)[0]
    if strategy_type == "bullish_engulfing_volume_reversal":
        return ev.bullish_engulfing_volume_reversal_returns(
            prices, params, opens=opens, highs=highs, lows=lows, volumes=volumes
        )[0]
    if strategy_type == "hammer_volume_reversal":
        return ev.hammer_volume_reversal_returns(prices, params, opens=opens, highs=highs, lows=lows, volumes=volumes)[0]
    if strategy_type == "inside_bar_volume_breakout":
        return ev.inside_bar_volume_breakout_returns(
            prices, params, opens=opens, highs=highs, lows=lows, volumes=volumes
        )[0]
    raise ValueError(f"UNSUPPORTED_STRATEGY_TYPE:{strategy_type}")


def dispatch_evaluate_strategy_metrics(
    *,
    strategy_type: str,
    prices: np.ndarray,
    params: dict[str, Any],
    opens: np.ndarray | None = None,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> dict[str, float]:
    import strategy_validator.research.strategy_batch_evaluators as ev

    if strategy_type == "momentum":
        return ev.evaluate_momentum(prices, params)
    if strategy_type == "mean_reversion":
        return ev.evaluate_mean_reversion(prices, params)
    if strategy_type == "volatility_breakout":
        return ev.evaluate_volatility_breakout(prices, params)
    if strategy_type == "moving_average_trend":
        return ev.evaluate_moving_average_trend(prices, params, volumes=volumes)
    if strategy_type == "trendline_volume_breakout":
        return ev.evaluate_trendline_volume_breakout(prices, params, highs=highs, lows=lows, volumes=volumes)
    if strategy_type == "obv_accumulation_breakout":
        return ev.evaluate_obv_accumulation_breakout(prices, params, volumes=volumes)
    if strategy_type == "rsi_volume_reversal":
        return ev.evaluate_rsi_volume_reversal(prices, params, volumes=volumes)
    if strategy_type == "bollinger_squeeze_breakout":
        return ev.evaluate_bollinger_squeeze_breakout(prices, params, volumes=volumes)
    if strategy_type == "vwap_pullback_continuation":
        return ev.evaluate_vwap_pullback_continuation(prices, params, highs=highs, lows=lows, volumes=volumes)
    if strategy_type == "donchian_channel_breakout":
        return ev.evaluate_donchian_channel_breakout(prices, params, highs=highs, lows=lows, volumes=volumes)
    if strategy_type == "atr_trailing_trend":
        return ev.evaluate_atr_trailing_trend(prices, params, highs=highs, lows=lows, volumes=volumes)
    if strategy_type == "macd_volume_momentum":
        return ev.evaluate_macd_volume_momentum(prices, params, volumes=volumes)
    if strategy_type == "bollinger_mean_reversion":
        return ev.evaluate_bollinger_mean_reversion(prices, params, volumes=volumes)
    if strategy_type == "vwap_deviation_reversion":
        return ev.evaluate_vwap_deviation_reversion(prices, params, highs=highs, lows=lows, volumes=volumes)
    if strategy_type == "keltner_channel_reversion":
        return ev.evaluate_keltner_channel_reversion(prices, params, highs=highs, lows=lows, volumes=volumes)
    if strategy_type == "ascending_triangle_breakout":
        return ev.evaluate_ascending_triangle_breakout(prices, params, highs=highs, lows=lows, volumes=volumes)
    if strategy_type == "bull_flag_continuation":
        return ev.evaluate_bull_flag_continuation(prices, params, highs=highs, lows=lows, volumes=volumes)
    if strategy_type == "support_resistance_retest":
        return ev.evaluate_support_resistance_retest(prices, params, highs=highs, lows=lows, volumes=volumes)
    if strategy_type == "bullish_engulfing_volume_reversal":
        return ev.evaluate_bullish_engulfing_volume_reversal(
            prices, params, opens=opens, highs=highs, lows=lows, volumes=volumes
        )
    if strategy_type == "hammer_volume_reversal":
        return ev.evaluate_hammer_volume_reversal(prices, params, opens=opens, highs=highs, lows=lows, volumes=volumes)
    if strategy_type == "inside_bar_volume_breakout":
        return ev.evaluate_inside_bar_volume_breakout(
            prices, params, opens=opens, highs=highs, lows=lows, volumes=volumes
        )
    raise ValueError(f"UNSUPPORTED_STRATEGY_TYPE:{strategy_type}")
