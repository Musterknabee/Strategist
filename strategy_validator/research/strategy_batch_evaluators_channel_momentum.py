"""Legacy facade for channel/momentum/reversion strategy evaluators.

The original channel-momentum family grew into multiple strategy styles.  Keep
this import path stable while subfamily modules own the actual deterministic
research implementations.
"""
from __future__ import annotations

from strategy_validator.research.strategy_batch_evaluators_channel_breakout import (
    atr_trailing_trend_returns,
    donchian_channel_breakout_returns,
    evaluate_atr_trailing_trend,
    evaluate_donchian_channel_breakout,
)
from strategy_validator.research.strategy_batch_evaluators_channel_reversion import (
    bollinger_mean_reversion_returns,
    evaluate_bollinger_mean_reversion,
    evaluate_keltner_channel_reversion,
    evaluate_vwap_deviation_reversion,
    keltner_channel_reversion_returns,
    vwap_deviation_reversion_returns,
)
from strategy_validator.research.strategy_batch_evaluators_momentum import (
    evaluate_macd_volume_momentum,
    macd_volume_momentum_returns,
)

__all__ = [
    "evaluate_donchian_channel_breakout",
    "evaluate_atr_trailing_trend",
    "evaluate_macd_volume_momentum",
    "evaluate_bollinger_mean_reversion",
    "evaluate_vwap_deviation_reversion",
    "evaluate_keltner_channel_reversion",
    "donchian_channel_breakout_returns",
    "atr_trailing_trend_returns",
    "macd_volume_momentum_returns",
    "bollinger_mean_reversion_returns",
    "vwap_deviation_reversion_returns",
    "keltner_channel_reversion_returns",
]
