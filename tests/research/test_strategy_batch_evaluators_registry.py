from __future__ import annotations

import numpy as np

from strategy_validator.research.strategy_batch_evaluators_registry import (
    SUPPORTED_STRATEGY_TYPES,
    dispatch_evaluate_strategy_metrics,
    dispatch_strategy_returns_series,
)


def test_registry_momentum_matches_direct_evaluator() -> None:
    import strategy_validator.research.strategy_batch_evaluators as ev

    prices = ev.deterministic_prices(seed="reg-test", n=120)
    params = {"signal_window": 12}
    a = ev.evaluate_momentum(prices, params)
    b = dispatch_evaluate_strategy_metrics(strategy_type="momentum", prices=prices, params=params)
    assert a.keys() == b.keys()
    for k in a:
        assert abs(float(a[k]) - float(b[k])) < 1e-9


def test_registry_returns_series_shape() -> None:
    from strategy_validator.research.strategy_batch_evaluators import deterministic_prices, log_returns

    prices = deterministic_prices(seed="r2", n=80)
    r = dispatch_strategy_returns_series(prices, "momentum", {"signal_window": 10})
    assert r.shape == log_returns(prices).shape


def test_supported_types_coverage() -> None:
    assert "momentum" in SUPPORTED_STRATEGY_TYPES
    assert "inside_bar_volume_breakout" in SUPPORTED_STRATEGY_TYPES
