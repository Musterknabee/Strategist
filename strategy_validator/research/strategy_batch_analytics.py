"""Chart-ready analytics from batch strategy prices (evidence-derived; research only)."""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from strategy_validator.contracts.strategy_batch import StrategyRunResult, StrategyRunStatus, StrategyTypeId
from strategy_validator.contracts.strategy_performance_artifacts import (
    PERFORMANCE_DRAWDOWN_SCHEMA,
    PERFORMANCE_EQUITY_SCHEMA,
    PERFORMANCE_FOLD_SCHEMA,
    PERFORMANCE_ROLLING_SCHEMA,
    PERFORMANCE_SCORECARD_SCHEMA,
    PERFORMANCE_TRADE_MARKERS_SCHEMA,
)
from strategy_validator.contracts.strategy_robustness import RobustnessResult
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from strategy_validator.research.strategy_batch_evaluators import log_returns, strategy_returns_series

StrategyType = StrategyTypeId

MAX_CHART_POINTS = 160
ROLLING_MIN = 5


def strategy_log_returns_series(
    prices: np.ndarray,
    strategy_type: StrategyType,
    params: dict[str, Any],
    *,
    opens: np.ndarray | None = None,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> np.ndarray:
    """Per-day strategy log-returns; aligned with ``log_returns(prices)`` (length n-1)."""

    return strategy_returns_series(
        prices,
        strategy_type,
        params,
        opens=opens,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )


def _equity_from_log_returns(strat: np.ndarray) -> np.ndarray:
    if strat.size == 0:
        return np.array([1.0], dtype=np.float64)
    return np.cumprod(np.exp(strat), dtype=np.float64)


def _drawdown_series(equity: np.ndarray) -> np.ndarray:
    if equity.size == 0:
        return np.array([], dtype=np.float64)
    peak = np.maximum.accumulate(equity)
    return 1.0 - equity / np.maximum(peak, 1e-12)


def _annualized_return_like(total_return: float, n_days: int) -> float:
    if n_days < 2:
        return 0.0
    return float((1.0 + total_return) ** (252.0 / float(n_days)) - 1.0)


def _rolling_sharpe(strat: np.ndarray, window: int) -> np.ndarray:
    n = strat.size
    out = np.zeros(n, dtype=np.float64)
    w = max(ROLLING_MIN, min(window, max(3, n // 4)))
    for i in range(n):
        lo = max(0, i - w + 1)
        seg = strat[lo : i + 1]
        if seg.size < 2:
            out[i] = 0.0
            continue
        sd = float(np.std(seg)) or 1e-12
        out[i] = float(np.mean(seg) / sd) * math.sqrt(252.0)
    return out


def _rolling_sum(strat: np.ndarray, window: int) -> np.ndarray:
    n = strat.size
    out = np.zeros(n, dtype=np.float64)
    w = max(ROLLING_MIN, min(window, max(3, n // 4)))
    for i in range(n):
        lo = max(0, i - w + 1)
        seg = strat[lo : i + 1]
        out[i] = float(np.sum(seg)) if seg.size else 0.0
    return out


def _rolling_vol(strat: np.ndarray, window: int) -> np.ndarray:
    n = strat.size
    out = np.zeros(n, dtype=np.float64)
    w = max(ROLLING_MIN, min(window, max(3, n // 4)))
    for i in range(n):
        lo = max(0, i - w + 1)
        seg = strat[lo : i + 1]
        out[i] = float(np.std(seg) * math.sqrt(252.0)) if seg.size > 1 else 0.0
    return out


def downsample_pair(xs: list[Any], ys: list[float], max_points: int) -> tuple[list[Any], list[float]]:
    n = len(xs)
    if n <= max_points or n == 0:
        return xs, ys
    step = max(1, n // max_points)
    return xs[::step], ys[::step]


def build_chart_artifacts(
    *,
    strategy_id: str,
    batch_id: str,
    run_id: str,
    timestamps: list[str],
    prices: np.ndarray,
    strategy_type: StrategyType,
    params: dict[str, Any],
    metrics_payload: dict[str, float],
    rob: RobustnessResult,
    execution_slippage_bps: float | None,
    execution_fee_bps: float | None,
    gate_robustness: str,
    gate_execution: str,
    pit_status: str,
    promotion_eligible: bool,
    status: StrategyRunStatus,
    synthetic_demo: bool,
    gate_data_quality: str,
    gate_parameter_sensitivity: str,
    gate_regime_analysis: str,
    opens: np.ndarray | None = None,
    highs: np.ndarray | None = None,
    lows: np.ndarray | None = None,
    volumes: np.ndarray | None = None,
) -> dict[str, Any]:
    """Returns paths-relative payloads (caller writes JSON), scorecard body, and compact UI bundle."""

    strat = strategy_log_returns_series(
        prices,
        strategy_type,
        params,
        opens=opens,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
    n = int(prices.shape[0])
    n_ret = int(strat.size)
    if len(timestamps) >= n:
        t_equity = list(timestamps[:n])
    else:
        t_equity = [str(i) for i in range(n)]
    if n_ret == 0:
        equity = np.array([1.0], dtype=np.float64)
        dd = np.array([0.0], dtype=np.float64)
        t_eq = [t_equity[0]] if t_equity else ["0"]
    else:
        equity = _equity_from_log_returns(strat)
        dd = _drawdown_series(equity)
        end = min(len(t_equity), 1 + equity.size)
        t_eq = t_equity[1:end]
        while len(t_eq) < equity.size:
            t_eq.append(t_eq[-1] if t_eq else str(len(t_eq)))
        t_eq = t_eq[: equity.size]

    roll_w = max(ROLLING_MIN, min(21, max(5, n_ret // 5 or 5)))
    roll_sh = _rolling_sharpe(strat, roll_w) if n_ret else np.array([])
    roll_vol = _rolling_vol(strat, roll_w) if n_ret else np.array([])
    roll_ret = _rolling_sum(strat, roll_w) if n_ret else np.array([])
    t_roll = t_eq if n_ret else []

    total_return = float(metrics_payload.get("total_return", 0.0))
    vol_ann = float(metrics_payload.get("volatility", 0.0))
    max_dd = float(metrics_payload.get("max_drawdown", 0.0))
    sharpe_like = float(metrics_payload.get("sharpe_like", 0.0))
    win_rate = float(metrics_payload.get("win_rate", 0.0))
    trade_count = int(metrics_payload.get("trade_count", 0.0))

    drag = float((execution_slippage_bps or 0.0) + (execution_fee_bps or 0.0))

    score, rank_expl = _compute_analytics_score(
        total_return=total_return,
        sharpe_like=sharpe_like,
        max_drawdown=max_dd,
        execution_drag_bps=drag,
        robustness_gate=gate_robustness,
        execution_gate=gate_execution,
        pit_status=pit_status,
        data_coverage_ratio=float(metrics_payload.get("data_coverage_ratio", 0.0)),
        status=status,
        synthetic_demo=synthetic_demo,
        data_quality_gate=gate_data_quality,
        parameter_sensitivity_gate=gate_parameter_sensitivity,
        regime_gate=gate_regime_analysis,
    )

    ann_ret = _annualized_return_like(total_return, max(n_ret, 1))

    equity_list = [float(x) for x in equity.tolist()]
    cum_ret_list = [float(x - 1.0) for x in equity_list]
    close_list: list[float] = []
    exposure_list: list[float] = []
    if n_ret > 0 and len(timestamps) >= n:
        for i in range(equity.size):
            idx = min(i + 1, n - 1)
            close_list.append(float(prices[idx]))
            ex = float(np.sign(strat[i])) if abs(float(strat[i])) > 1e-12 else 0.0
            exposure_list.append(ex)
    else:
        close_list = [float(prices[min(i, n - 1)]) for i in range(len(equity_list))]
        exposure_list = [0.0] * len(equity_list)
    dd_list = [float(x) for x in dd.tolist()]
    peak_equity_list = []
    if equity.size:
        peak = np.maximum.accumulate(equity)
        peak_equity_list = [float(x) for x in peak.tolist()]
    else:
        peak_equity_list = []
    fold_perf = [
        {
            "fold_index": f.fold_index,
            "test_return": f.test_return,
            "train_return": f.train_return,
            "test_sharpe_like": f.test_sharpe_like,
            "positive_test_return": f.positive_test_return,
        }
        for f in rob.folds
    ]

    equity_body = {
        "schema_version": PERFORMANCE_EQUITY_SCHEMA,
        "strategy_id": strategy_id,
        "batch_id": batch_id,
        "run_id": run_id,
        "model_note": "From toy evaluator log-returns on filtered closes; not live PnL.",
        "timestamps_utc": t_eq,
        "equity": equity_list,
        "cumulative_return": cum_ret_list,
        "close": close_list[: len(equity_list)],
        "exposure": exposure_list[: len(equity_list)],
    }
    dd_body = {
        "schema_version": PERFORMANCE_DRAWDOWN_SCHEMA,
        "strategy_id": strategy_id,
        "batch_id": batch_id,
        "run_id": run_id,
        "timestamps_utc": t_eq,
        "drawdown": dd_list,
        "peak_equity": peak_equity_list[: len(dd_list)],
    }
    roll_body = {
        "schema_version": PERFORMANCE_ROLLING_SCHEMA,
        "strategy_id": strategy_id,
        "batch_id": batch_id,
        "run_id": run_id,
        "window_bars": roll_w,
        "timestamps_utc": list(t_roll),
        "rolling_return": [float(x) for x in roll_ret.tolist()],
        "rolling_sharpe_like": [float(x) for x in roll_sh.tolist()],
        "rolling_volatility_ann": [float(x) for x in roll_vol.tolist()],
    }
    fold_body = {
        "schema_version": PERFORMANCE_FOLD_SCHEMA,
        "strategy_id": strategy_id,
        "batch_id": batch_id,
        "run_id": run_id,
        "robustness_model": rob.model_label,
        "folds": fold_perf,
    }

    trade_markers = {
        "schema_version": PERFORMANCE_TRADE_MARKERS_SCHEMA,
        "strategy_id": strategy_id,
        "batch_id": batch_id,
        "run_id": run_id,
        "markers": [],
        "note": "Toy evaluators do not emit discrete execution fills; markers intentionally empty.",
    }

    scorecard = {
        "schema_version": PERFORMANCE_SCORECARD_SCHEMA,
        "strategy_id": strategy_id,
        "batch_id": batch_id,
        "run_id": run_id,
        "total_return": total_return,
        "annualized_return_like": ann_ret,
        "volatility": vol_ann,
        "max_drawdown": max_dd,
        "sharpe_like": sharpe_like,
        "win_rate": win_rate,
        "trade_count": trade_count,
        "execution_drag_bps": drag,
        "data_quality_gate": gate_data_quality,
        "pit_status": pit_status,
        "execution_realism_gate": gate_execution,
        "robustness_gate": gate_robustness,
        "parameter_sensitivity_gate": gate_parameter_sensitivity,
        "regime_analysis_gate": gate_regime_analysis,
        "promotion_eligible": promotion_eligible,
        "score": score,
        "rank_explanation": rank_expl,
        "warnings": [],
        "blockers": [],
        "disclaimer": "Research analytics only; no profitability guarantee.",
    }

    t_e_ds, v_e_ds = downsample_pair(list(t_eq), equity_list, MAX_CHART_POINTS)
    _, v_d_ds = downsample_pair(list(t_eq), dd_list, MAX_CHART_POINTS)
    t_r_ds, v_rs_ds = downsample_pair(list(t_roll), [float(x) for x in roll_sh.tolist()], MAX_CHART_POINTS)
    _, v_rv_ds = downsample_pair(list(t_roll), [float(x) for x in roll_vol.tolist()], MAX_CHART_POINTS)

    charts_compact = {
        "schema_version": "strategy_lab_charts_compact/v1",
        "strategy_id": strategy_id,
        "equity": {"t": t_e_ds, "v": v_e_ds},
        "drawdown": {"t": t_e_ds, "v": v_d_ds},
        "rolling": {"t": t_r_ds, "sharpe_like": v_rs_ds, "volatility": v_rv_ds},
        "folds": fold_perf,
        "scatter": {"total_return": total_return, "max_drawdown": max_dd},
        "digests": {
            "equity_curve": canonical_json_sha256(equity_body),
            "drawdown_curve": canonical_json_sha256(dd_body),
            "rolling_metrics": canonical_json_sha256(roll_body),
            "fold_performance": canonical_json_sha256(fold_body),
            "strategy_scorecard": canonical_json_sha256(scorecard),
            "trade_markers": canonical_json_sha256(trade_markers),
        },
    }

    return {
        "equity_curve": equity_body,
        "drawdown_curve": dd_body,
        "rolling_metrics": roll_body,
        "fold_performance": fold_body,
        "strategy_scorecard": scorecard,
        "trade_markers": trade_markers,
        "charts_compact": charts_compact,
        "analytics_score": score,
    }


def _compute_analytics_score(
    *,
    total_return: float,
    sharpe_like: float,
    max_drawdown: float,
    execution_drag_bps: float,
    robustness_gate: str,
    execution_gate: str,
    pit_status: str,
    data_coverage_ratio: float,
    status: StrategyRunStatus,
    synthetic_demo: bool,
    data_quality_gate: str,
    parameter_sensitivity_gate: str,
    regime_gate: str,
) -> tuple[float, str]:
    parts: list[str] = []
    if status in (StrategyRunStatus.BLOCKED, StrategyRunStatus.FAILED):
        return -1_000_000.0, "Not ranked as a top candidate: run BLOCKED or FAILED."

    s = sharpe_like * 1.15 + min(3.0, max(-2.0, total_return * 2.0))
    s -= max_drawdown * 2.5
    s -= (execution_drag_bps / 100.0) * 0.45
    parts.append(f"base_risk_adj={s:.3f}")

    rg = robustness_gate.upper()
    if rg == "PROVEN":
        pass
    elif rg == "WARNING":
        s -= 0.65
        parts.append("robustness_WARN=-0.65")
    elif rg == "NOT_APPLICABLE":
        s -= 1.1
        parts.append("robustness_NA=-1.1")
    else:
        s -= 1.4
        parts.append("robustness_weak=-1.4")

    if execution_gate != "PROVEN":
        s -= 0.85 if execution_gate == "WARNING" else 1.1
        parts.append(f"exec_gate={execution_gate}")

    if pit_status != "PIT_VERIFIED":
        s -= 0.9
        parts.append("pit_penalty=-0.9")

    if data_coverage_ratio < 0.7:
        s -= 0.35
        parts.append("coverage_penalty=-0.35")

    if synthetic_demo:
        s -= 2.0
        parts.append("synthetic_demo=-2.0")

    dq = data_quality_gate.upper()
    if dq == "BLOCKED":
        s -= 2.5
        parts.append("data_quality_BLOCK=-2.5")
    elif dq == "WARNING":
        s -= 0.9
        parts.append("data_quality_WARN=-0.9")
    elif dq == "NOT_APPLICABLE":
        s -= 0.4
        parts.append("data_quality_NA=-0.4")

    pg = parameter_sensitivity_gate.upper()
    if pg == "FRAGILE":
        s -= 2.2
        parts.append("param_FRAGILE=-2.2")
    elif pg == "WARNING":
        s -= 0.55
        parts.append("param_WARN=-0.55")

    rg = regime_gate.upper()
    if rg == "BLOCKED":
        s -= 2.0
        parts.append("regime_BLOCK=-2.0")
    elif rg == "WARNING":
        s -= 0.5
        parts.append("regime_WARN=-0.5")

    expl = "; ".join(parts) + f" → score={s:.4f} (heuristic; not alpha guarantee)."
    return float(s), expl


def apply_batch_ranking(results: list[StrategyRunResult]) -> tuple[list[StrategyRunResult], list[dict[str, Any]]]:
    """Sort by analytics_score; BLOCKED/FAILED never sort above PASSED/PAPER_ONLY."""

    def sort_key(r: StrategyRunResult) -> tuple[int, float, str]:
        bad = r.status in (StrategyRunStatus.BLOCKED, StrategyRunStatus.FAILED)
        tier = 1 if bad else 0
        sc = r.analytics_score
        if sc is None:
            sc = -1e12
        return (tier, -sc, r.strategy_id)

    ordered = sorted(results, key=sort_key)
    ranking: list[dict[str, Any]] = []
    rank = 0
    for r in ordered:
        rank += 1
        ranking.append(
            {
                "strategy_id": r.strategy_id,
                "rank": rank,
                "score": r.analytics_score,
                "status": r.status.value,
                "blocked_tier": r.status in (StrategyRunStatus.BLOCKED, StrategyRunStatus.FAILED),
            }
        )
    id_to_rank = {row["strategy_id"]: row["rank"] for row in ranking}
    out: list[StrategyRunResult] = []
    for r in results:
        out.append(
            r.model_copy(
                update={"analytics_rank": id_to_rank.get(r.strategy_id)},
            )
        )
    return out, ranking


__all__ = [
    "MAX_CHART_POINTS",
    "apply_batch_ranking",
    "build_chart_artifacts",
    "downsample_pair",
    "strategy_log_returns_series",
]
