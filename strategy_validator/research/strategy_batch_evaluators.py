"""Public facade for deterministic strategy evaluators (research / paper only).

The evaluator implementations are split by strategy family so this legacy import
path remains stable without becoming another high-gravity monolith.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from strategy_validator.research.strategy_batch_evaluators_advanced_technical import (
    bollinger_squeeze_breakout_returns,
    evaluate_bollinger_squeeze_breakout,
    evaluate_rsi_volume_reversal,
    evaluate_vwap_pullback_continuation,
    rsi_volume_reversal_returns,
    vwap_pullback_continuation_returns,
)
from strategy_validator.research.strategy_batch_evaluators_base import (
    evaluate_mean_reversion,
    evaluate_momentum,
    evaluate_volatility_breakout,
)
from strategy_validator.research.strategy_batch_evaluators_candlestick_volume import (
    bullish_engulfing_volume_reversal_returns,
    evaluate_bullish_engulfing_volume_reversal,
    evaluate_hammer_volume_reversal,
    evaluate_inside_bar_volume_breakout,
    hammer_volume_reversal_returns,
    inside_bar_volume_breakout_returns,
)
from strategy_validator.research.strategy_batch_evaluators_channel_momentum import (
    atr_trailing_trend_returns,
    bollinger_mean_reversion_returns,
    donchian_channel_breakout_returns,
    evaluate_atr_trailing_trend,
    evaluate_bollinger_mean_reversion,
    evaluate_donchian_channel_breakout,
    evaluate_keltner_channel_reversion,
    evaluate_macd_volume_momentum,
    evaluate_vwap_deviation_reversion,
    keltner_channel_reversion_returns,
    macd_volume_momentum_returns,
    vwap_deviation_reversion_returns,
)
from strategy_validator.research.strategy_batch_evaluators_chart_patterns import (
    ascending_triangle_breakout_returns,
    bull_flag_continuation_returns,
    evaluate_ascending_triangle_breakout,
    evaluate_bull_flag_continuation,
    evaluate_support_resistance_retest,
    support_resistance_retest_returns,
)
from strategy_validator.research.strategy_batch_evaluators_common import deterministic_prices, log_returns
from strategy_validator.research.strategy_batch_evaluators_price_volume import (
    evaluate_moving_average_trend,
    evaluate_obv_accumulation_breakout,
    evaluate_trendline_volume_breakout,
    moving_average_trend_returns,
    obv_accumulation_breakout_returns,
    trendline_volume_breakout_returns,
)


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
    from strategy_validator.research.strategy_batch_evaluators_registry import dispatch_strategy_returns_series

    return dispatch_strategy_returns_series(
        prices, strategy_type, params, opens=opens, highs=highs, lows=lows, volumes=volumes
    )


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
    from strategy_validator.research.strategy_batch_evaluators_registry import dispatch_evaluate_strategy_metrics

    return dispatch_evaluate_strategy_metrics(
        strategy_type=strategy_type,
        prices=prices,
        params=params,
        opens=opens,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )


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
