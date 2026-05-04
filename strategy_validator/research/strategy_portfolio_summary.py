"""Batch-level return correlation from equity curves (research)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from strategy_validator.contracts.strategy_batch import StrategyRunResult, StrategyRunStatus
from strategy_validator.contracts.strategy_portfolio_summary import PortfolioCorrelationSummary
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def _read_equity_series(path: Path) -> np.ndarray | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    eq = data.get("equity")
    if not isinstance(eq, list) or len(eq) < 3:
        return None
    return np.array([float(x) for x in eq], dtype=np.float64)


def _log_returns_from_equity(eq: np.ndarray) -> np.ndarray:
    eq = np.maximum(eq, 1e-12)
    return np.diff(np.log(eq))


def build_batch_portfolio_summary(
    *,
    batch_id: str,
    run_id: str,
    strategies: list[StrategyRunResult],
) -> PortfolioCorrelationSummary:
    real_rows: list[tuple[str, np.ndarray]] = []
    for r in strategies:
        if r.status in (StrategyRunStatus.FAILED, StrategyRunStatus.BLOCKED):
            continue
        if r.gate_summary.data_gate == "SYNTHETIC_DEMO" or r.data_plane == "SYNTHETIC":
            continue
        p = r.equity_curve_path
        if not p:
            continue
        path = Path(p)
        eq = _read_equity_series(path)
        if eq is None:
            continue
        lr = _log_returns_from_equity(eq)
        if lr.size < 3:
            continue
        real_rows.append((r.strategy_id, lr))

    if len(real_rows) < 2:
        body = PortfolioCorrelationSummary(
            batch_id=batch_id,
            run_id=run_id,
            strategy_ids=[s for s, _ in real_rows],
            portfolio_gate_status="NOT_APPLICABLE",
            warnings=["INSUFFICIENT_STRATEGIES_FOR_CORRELATION"],
        )
        plain = body.model_dump(mode="json")
        return body.model_copy(
            update={"portfolio_summary_evidence_sha256": canonical_json_sha256(plain)}
        )

    ids = [s for s, _ in real_rows]
    series_list = [s for _, s in real_rows]
    min_len = min(x.size for x in series_list)
    mat = np.stack([x[-min_len:] for x in series_list], axis=1)
    corr = np.corrcoef(mat, rowvar=False)
    n = corr.shape[0]
    matrix = [[float(corr[i, j]) for j in range(n)] for i in range(n)]

    pairs: list[dict[str, str | float]] = []
    for i in range(n):
        for j in range(i + 1, n):
            c = float(corr[i, j])
            if c > 0.90:
                pairs.append({"a": ids[i], "b": ids[j], "correlation": c})

    tri = n * (n - 1) / 2
    off = []
    for i in range(n):
        for j in range(i + 1, n):
            off.append(float(corr[i, j]))
    avg = float(np.mean(np.array(off, dtype=np.float64))) if off else 0.0

    dup_warn = [f"DUPLICATE_ALPHA:{p['a']}:{p['b']}:{p['correlation']:.3f}" for p in pairs]
    div_score = float(max(0.0, 1.0 - max(0.0, avg)))

    gate: Any = "DIVERSIFYING"
    warnings: list[str] = []
    blockers: list[str] = []
    if len(pairs) >= max(1, n - 1):
        gate = "DUPLICATIVE"
        blockers.append("HIGH_CORRELATION_CLUSTER")
    elif len(pairs) > 0 or avg > 0.75:
        gate = "WARNING"
        warnings.append("ELEVATED_CROSS_STRATEGY_CORRELATION")

    body = PortfolioCorrelationSummary(
        batch_id=batch_id,
        run_id=run_id,
        strategy_ids=ids,
        correlation_matrix=matrix,
        high_correlation_pairs=pairs,
        average_correlation=avg,
        diversification_score=div_score,
        duplicate_alpha_warnings=dup_warn,
        portfolio_gate_status=gate,
        blockers=blockers,
        warnings=warnings,
    )
    plain = body.model_dump(mode="json")
    return body.model_copy(
        update={"portfolio_summary_evidence_sha256": canonical_json_sha256(plain)}
    )


__all__ = ["build_batch_portfolio_summary"]
