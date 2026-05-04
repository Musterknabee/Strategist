from __future__ import annotations

import numpy as np

from strategy_validator.research.strategy_batch_evaluators import deterministic_prices
from strategy_validator.research.strategy_holdout_gate import evaluate_oos_holdout


def test_holdout_not_run_when_disabled() -> None:
    prices = deterministic_prices(seed="ho0", n=100)
    out = evaluate_oos_holdout(
        strategy_type="momentum",
        prices=prices,
        params={"signal_window": 10},
        holdout_bars=0,
    )
    assert out["oos_holdout_gate"] == "NOT_RUN"


def test_holdout_produces_metrics() -> None:
    prices = deterministic_prices(seed="ho1", n=200)
    out = evaluate_oos_holdout(
        strategy_type="momentum",
        prices=prices,
        params={"signal_window": 10, "oos_min_sharpe": -99.0},
        holdout_bars=30,
    )
    assert out["oos_holdout_gate"] in {"PASS", "BLOCKED", "NOT_APPLICABLE"}
    assert "oos_sharpe_like" in out
