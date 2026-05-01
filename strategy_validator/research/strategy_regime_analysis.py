"""Deterministic regime tagging vs toy strategy returns (research)."""
from __future__ import annotations

import math
from typing import Any, Literal

import numpy as np

from strategy_validator.contracts.strategy_regime_analysis import RegimeAnalysisResult, RegimeStat
from strategy_validator.research.strategy_batch_analytics import strategy_log_returns_series
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from strategy_validator.research.strategy_batch_evaluators import log_returns

StrategyType = Literal["momentum", "mean_reversion", "volatility_breakout"]

_ROLL = 20
_VOL_HI = 0.02
_VOL_LO = 0.005
_TREND = 0.0003


def evaluate_regime_analysis(
    *,
    strategy_id: str,
    batch_id: str,
    run_id: str,
    prices: np.ndarray,
    strategy_type: StrategyType,
    params: dict[str, Any],
    synthetic_demo: bool,
) -> RegimeAnalysisResult:
    if synthetic_demo:
        body = RegimeAnalysisResult(
            strategy_id=strategy_id,
            batch_id=batch_id,
            run_id=run_id,
            gate_status="NOT_APPLICABLE",
            warnings=["SYNTHETIC_DEMO_NOT_REGIME_PROOF"],
        )
        plain = body.model_dump(mode="json")
        return body.model_copy(
            update={"regime_analysis_evidence_sha256": canonical_json_sha256(plain)}
        )

    n = int(prices.shape[0])
    if n < _ROLL + 5:
        body = RegimeAnalysisResult(
            strategy_id=strategy_id,
            batch_id=batch_id,
            run_id=run_id,
            gate_status="BLOCKED",
            blockers=["INSUFFICIENT_SAMPLE_FOR_REGIME_ANALYSIS"],
        )
        plain = body.model_dump(mode="json")
        return body.model_copy(
            update={"regime_analysis_evidence_sha256": canonical_json_sha256(plain)}
        )

    r_px = log_returns(prices)
    strat = strategy_log_returns_series(prices, strategy_type, params)
    if strat.size == 0:
        body = RegimeAnalysisResult(
            strategy_id=strategy_id,
            batch_id=batch_id,
            run_id=run_id,
            gate_status="NOT_APPLICABLE",
            warnings=["NO_STRATEGY_RETURNS"],
        )
        plain = body.model_dump(mode="json")
        return body.model_copy(
            update={"regime_analysis_evidence_sha256": canonical_json_sha256(plain)}
        )

    # Align strat[i] with bar transition i -> i+1; use price index i+1 for regime label
    tags: list[str] = []
    for i in range(1, n):
        lo = max(0, i - _ROLL)
        window = r_px[lo:i]
        if window.size < 5:
            tags.append("SIDEWAYS")
            continue
        mu = float(np.mean(window))
        vol = float(np.std(window)) or 1e-12
        trend = "SIDEWAYS"
        if mu > _TREND:
            trend = "UP_TREND"
        elif mu < -_TREND:
            trend = "DOWN_TREND"
        vol_tag = "HIGH_VOLATILITY" if vol > _VOL_HI else "LOW_VOLATILITY"
        tags.append(f"{trend}|{vol_tag}")

    # strat length n-1; tags for indices 1..n-1 => len n-1
    m = min(strat.size, len(tags))
    buckets: dict[str, list[float]] = {}
    for i in range(m):
        label = tags[i]
        buckets.setdefault(label, []).append(float(strat[i]))

    regimes: list[RegimeStat] = []
    for label, xs in sorted(buckets.items()):
        arr = np.array(xs, dtype=np.float64)
        mean_lr = float(np.mean(arr)) if arr.size else 0.0
        cum = float(np.sum(arr)) if arr.size else 0.0
        regimes.append(
            RegimeStat(regime=label, bar_count=int(arr.size), mean_strategy_log_return=mean_lr, cumulative_strategy_return=cum)
        )

    best = max(regimes, key=lambda x: x.cumulative_strategy_return) if regimes else None
    worst = min(regimes, key=lambda x: x.cumulative_strategy_return) if regimes else None
    failed = sum(1 for x in regimes if x.cumulative_strategy_return < -0.02)

    gate: Literal["PROVEN", "WARNING", "BLOCKED", "NOT_APPLICABLE"] = "PROVEN"
    warnings: list[str] = []
    blockers: list[str] = []
    if failed >= 3:
        gate = "BLOCKED"
        blockers.append("MULTIPLE_REGIME_FAILURES")
    elif failed >= 1:
        gate = "WARNING"
        warnings.append("REGIME_STRESS_DETECTED")

    body = RegimeAnalysisResult(
        strategy_id=strategy_id,
        batch_id=batch_id,
        run_id=run_id,
        regime_count=len(regimes),
        regimes=regimes,
        best_regime=best.regime if best else "",
        worst_regime=worst.regime if worst else "",
        failed_regime_count=failed,
        gate_status=gate,
        blockers=blockers,
        warnings=warnings,
    )
    plain = body.model_dump(mode="json")
    return body.model_copy(
        update={"regime_analysis_evidence_sha256": canonical_json_sha256(plain)}
    )


__all__ = ["evaluate_regime_analysis"]
