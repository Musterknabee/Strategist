from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RESEARCH = REPO / "strategy_validator" / "research"


def _module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _function_names(path: Path) -> set[str]:
    return {node.name for node in _module(path).body if isinstance(node, ast.FunctionDef)}


def test_strategy_batch_evaluators_is_public_facade() -> None:
    path = RESEARCH / "strategy_batch_evaluators.py"
    names = _function_names(path)

    assert len(path.read_text(encoding="utf-8").splitlines()) <= 180
    assert names == {"strategy_returns_series", "evaluate_strategy_metrics"}
    assert "strategy_batch_evaluators_registry" in path.read_text(encoding="utf-8")


def test_strategy_evaluator_families_own_expected_templates() -> None:
    expected = {
        "strategy_batch_evaluators_base.py": {
            "evaluate_momentum",
            "evaluate_mean_reversion",
            "evaluate_volatility_breakout",
        },
        "strategy_batch_evaluators_price_volume.py": {
            "evaluate_moving_average_trend",
            "evaluate_trendline_volume_breakout",
            "evaluate_obv_accumulation_breakout",
            "moving_average_trend_returns",
            "trendline_volume_breakout_returns",
            "obv_accumulation_breakout_returns",
        },
        "strategy_batch_evaluators_advanced_technical.py": {
            "evaluate_rsi_volume_reversal",
            "evaluate_bollinger_squeeze_breakout",
            "evaluate_vwap_pullback_continuation",
            "rsi_volume_reversal_returns",
            "bollinger_squeeze_breakout_returns",
            "vwap_pullback_continuation_returns",
        },
        "strategy_batch_evaluators_channel_breakout.py": {
            "evaluate_donchian_channel_breakout",
            "evaluate_atr_trailing_trend",
            "donchian_channel_breakout_returns",
            "atr_trailing_trend_returns",
        },
        "strategy_batch_evaluators_momentum.py": {
            "evaluate_macd_volume_momentum",
            "macd_volume_momentum_returns",
        },
        "strategy_batch_evaluators_channel_reversion.py": {
            "evaluate_bollinger_mean_reversion",
            "evaluate_vwap_deviation_reversion",
            "evaluate_keltner_channel_reversion",
            "bollinger_mean_reversion_returns",
            "vwap_deviation_reversion_returns",
            "keltner_channel_reversion_returns",
        },
        "strategy_batch_evaluators_chart_patterns.py": {
            "evaluate_ascending_triangle_breakout",
            "evaluate_bull_flag_continuation",
            "evaluate_support_resistance_retest",
            "ascending_triangle_breakout_returns",
            "bull_flag_continuation_returns",
            "support_resistance_retest_returns",
        },
        "strategy_batch_evaluators_candlestick_volume.py": {
            "evaluate_bullish_engulfing_volume_reversal",
            "evaluate_hammer_volume_reversal",
            "evaluate_inside_bar_volume_breakout",
            "bullish_engulfing_volume_reversal_returns",
            "hammer_volume_reversal_returns",
            "inside_bar_volume_breakout_returns",
        },
    }

    for filename, required in expected.items():
        assert required <= _function_names(RESEARCH / filename)



def test_channel_momentum_evaluator_is_subfamily_facade() -> None:
    path = RESEARCH / "strategy_batch_evaluators_channel_momentum.py"
    text = path.read_text(encoding="utf-8")

    assert len(text.splitlines()) <= 60
    assert _function_names(path) == set()
    assert "strategy_batch_evaluators_channel_breakout" in text
    assert "strategy_batch_evaluators_momentum" in text
    assert "strategy_batch_evaluators_channel_reversion" in text


def test_channel_momentum_subfamily_exports_match_legacy_facade() -> None:
    import strategy_validator.research.strategy_batch_evaluators_channel_momentum as facade
    from strategy_validator.research import strategy_batch_evaluators_channel_breakout as breakout
    from strategy_validator.research import strategy_batch_evaluators_channel_reversion as reversion
    from strategy_validator.research import strategy_batch_evaluators_momentum as momentum

    expected = [*breakout.__all__, *momentum.__all__, *reversion.__all__]
    assert sorted(facade.__all__) == sorted(expected)
    for name in expected:
        assert getattr(facade, name) is not None

def test_legacy_strategy_evaluator_exports_remain_complete() -> None:
    import strategy_validator.research.strategy_batch_evaluators as evaluators
    from strategy_validator.research.strategy_batch_evaluators_registry import SUPPORTED_STRATEGY_TYPES

    for strategy_type in SUPPORTED_STRATEGY_TYPES:
        evaluate_name = f"evaluate_{strategy_type}"
        assert hasattr(evaluators, evaluate_name)

    assert hasattr(evaluators, "deterministic_prices")
    assert hasattr(evaluators, "log_returns")
    assert hasattr(evaluators, "strategy_returns_series")
