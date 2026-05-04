"""Out-of-sample holdout evaluation over per-bar strategy returns (research / paper only)."""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from strategy_validator.research.strategy_batch_evaluators import strategy_returns_series


def evaluate_oos_holdout(
    *,
    strategy_type: str,
    prices: np.ndarray,
    params: dict[str, Any],
    holdout_bars: int,
    opens: np.ndarray | None = None,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> dict[str, Any]:
    """Split tail *holdout_bars* as OOS; compare Sharpe-like ratios vs threshold in params."""
    hb = int(holdout_bars)
    if hb <= 0:
        return {"oos_holdout_gate": "NOT_RUN", "oos_holdout_reason": "holdout_bars_not_set"}
    r = strategy_returns_series(
        prices,
        strategy_type,
        params,
        opens=opens,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
    if r.size < hb + 20:
        return {
            "oos_holdout_gate": "NOT_APPLICABLE",
            "oos_holdout_reason": "insufficient_bars",
            "oos_holdout_bars": float(hb),
        }
    is_seg = r[:-hb]
    oos_seg = r[-hb:]

    def sharpe_like(seg: np.ndarray) -> float:
        if seg.size < 5:
            return 0.0
        mu = float(np.mean(seg))
        sd = float(np.std(seg)) or 1e-12
        return float((mu / sd) * math.sqrt(252))

    is_s = sharpe_like(is_seg)
    oos_s = sharpe_like(oos_seg)
    min_oos = float(params.get("oos_min_sharpe", -0.75))
    gate = "PASS" if oos_s >= min_oos else "BLOCKED"
    return {
        "oos_holdout_gate": gate,
        "oos_holdout_bars": float(hb),
        "oos_sharpe_like": oos_s,
        "is_sharpe_like": is_s,
        "oos_min_sharpe": min_oos,
    }
