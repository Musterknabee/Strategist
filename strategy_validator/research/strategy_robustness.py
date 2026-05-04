"""Walk-forward robustness evaluation from filtered bars CSV (deterministic; heuristic)."""
from __future__ import annotations

import csv
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from strategy_validator.contracts.strategy_robustness import (
    DSR_LIKE_MODEL_LABEL,
    PBO_LIKE_MODEL_LABEL,
    ROBUSTNESS_MODEL_LABEL,
    RobustnessAssumptions,
    RobustnessGateStatus,
    RobustnessResult,
    WalkForwardFoldResult,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def _parse_ts(raw: str) -> datetime:
    s = raw.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _segment_simple_return(closes: np.ndarray) -> float:
    if closes.size < 2:
        return 0.0
    a, b = float(closes[0]), float(closes[-1])
    if abs(a) < 1e-12:
        return 0.0
    return b / a - 1.0


def _daily_returns(closes: np.ndarray) -> np.ndarray:
    if closes.size < 2:
        return np.array([], dtype=np.float64)
    c = np.maximum(closes.astype(np.float64), 1e-12)
    return np.diff(c) / c[:-1]


def _sharpe_like(closes: np.ndarray) -> float:
    r = _daily_returns(closes)
    if r.size < 2:
        return 0.0
    sd = float(np.std(r))
    if sd < 1e-12:
        return 0.0
    return float(np.mean(r) / sd) * math.sqrt(252.0)


def _max_drawdown(closes: np.ndarray) -> float:
    if closes.size < 2:
        return 0.0
    p = closes.astype(np.float64)
    peak = np.maximum.accumulate(p)
    dd = 1.0 - p / np.maximum(peak, 1e-12)
    return float(np.max(dd))


def evaluate_strategy_robustness(
    *,
    strategy_id: str,
    batch_id: str,
    run_id: str,
    filtered_bars_path: Path | None,
    synthetic_demo: bool,
    assumptions: RobustnessAssumptions,
) -> RobustnessResult:
    """Heuristic walk-forward robustness; not institutional CPCV."""

    base = RobustnessResult(strategy_id=strategy_id, batch_id=batch_id, run_id=run_id)

    if synthetic_demo:
        return base.model_copy(
            update={
                "gate_status": RobustnessGateStatus.NOT_APPLICABLE,
                "blockers": ["SYNTHETIC_DEMO_NOT_ROBUSTNESS_PROOF"],
                "warnings": ["ROBUSTNESS_REQUIRES_REAL_LOCAL_BARS"],
                "robustness_evidence_sha256": canonical_json_sha256(
                    {"gate": "NOT_APPLICABLE", "reason": "synthetic", "strategy_id": strategy_id}
                ),
            }
        )

    if filtered_bars_path is None or not filtered_bars_path.is_file():
        return base.model_copy(
            update={
                "gate_status": RobustnessGateStatus.BLOCKED,
                "blockers": ["MISSING_FILTERED_BARS"],
                "robustness_evidence_sha256": canonical_json_sha256({"gate": "BLOCKED", "reason": "no_csv"}),
            }
        )

    times: list[datetime] = []
    closes: list[float] = []
    with filtered_bars_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return base.model_copy(
                update={
                    "gate_status": RobustnessGateStatus.BLOCKED,
                    "blockers": ["FILTERED_BARS_NO_HEADER"],
                    "robustness_evidence_sha256": canonical_json_sha256({"gate": "BLOCKED", "reason": "header"}),
                }
            )
        fields = {f.strip().lower(): f for f in reader.fieldnames if f}
        if "timestamp_utc" not in fields or "close" not in fields:
            return base.model_copy(
                update={
                    "gate_status": RobustnessGateStatus.BLOCKED,
                    "blockers": ["FILTERED_BARS_MISSING_TIMESTAMP_OR_CLOSE"],
                    "robustness_evidence_sha256": canonical_json_sha256({"gate": "BLOCKED", "reason": "cols"}),
                }
            )
        for row in reader:
            if not row:
                continue
            ts_raw = (row.get(fields["timestamp_utc"]) or "").strip()
            cl_raw = (row.get(fields["close"]) or "").strip()
            if not ts_raw or not cl_raw:
                continue
            times.append(_parse_ts(ts_raw))
            closes.append(float(cl_raw))

    if len(closes) < 2:
        return base.model_copy(
            update={
                "gate_status": RobustnessGateStatus.BLOCKED,
                "blockers": ["INSUFFICIENT_SAMPLE"],
                "sample_count": len(closes),
                "robustness_evidence_sha256": canonical_json_sha256({"gate": "BLOCKED", "reason": "short"}),
            }
        )

    order = sorted(range(len(times)), key=lambda i: times[i])
    t_ord = [times[i] for i in order]
    c_ord = np.array([closes[i] for i in order], dtype=np.float64)
    n = int(c_ord.size)
    F = int(assumptions.fold_count)
    min_tr = int(assumptions.min_train_bars)
    min_te = int(assumptions.min_test_bars)

    L = max(min_te, (n - min_tr) // F)
    if min_tr + F * L > n:
        L = min_te
    if min_tr + F * L > n:
        return base.model_copy(
            update={
                "gate_status": RobustnessGateStatus.BLOCKED,
                "blockers": ["INSUFFICIENT_SAMPLE_FOR_WALK_FORWARD"],
                "warnings": [f"need_at_least_{min_tr + F * min_te}_bars_for_config"],
                "sample_count": n,
                "fold_count": F,
                "robustness_evidence_sha256": canonical_json_sha256({"gate": "BLOCKED", "reason": "fold_fit", "n": n}),
            }
        )

    folds: list[WalkForwardFoldResult] = []
    for i in range(F):
        train_end = min_tr + i * L
        test_end = train_end + L
        if test_end > n:
            return base.model_copy(
                update={
                    "gate_status": RobustnessGateStatus.BLOCKED,
                    "blockers": ["INSUFFICIENT_SAMPLE_FOR_WALK_FORWARD"],
                    "sample_count": n,
                    "fold_count": F,
                    "robustness_evidence_sha256": canonical_json_sha256({"gate": "BLOCKED", "reason": "bounds"}),
                }
            )
        train_c = c_ord[0:train_end]
        test_c = c_ord[train_end:test_end]
        tr_ret = _segment_simple_return(train_c)
        te_ret = _segment_simple_return(test_c)
        tr_sh = _sharpe_like(train_c)
        te_sh = _sharpe_like(test_c)
        folds.append(
            WalkForwardFoldResult(
                fold_index=i,
                train_start_utc=t_ord[0],
                train_end_utc=t_ord[train_end - 1],
                test_start_utc=t_ord[train_end],
                test_end_utc=t_ord[test_end - 1],
                train_bar_count=int(train_c.size),
                test_bar_count=int(test_c.size),
                train_return=tr_ret,
                test_return=te_ret,
                train_sharpe_like=tr_sh,
                test_sharpe_like=te_sh,
                max_drawdown=_max_drawdown(test_c),
                positive_test_return=te_ret > 0,
            )
        )

    test_returns = np.array([f.test_return for f in folds], dtype=np.float64)
    test_sharpes = np.array([f.test_sharpe_like for f in folds], dtype=np.float64)
    med_te_ret = float(np.median(test_returns))
    med_te_sh = float(np.median(test_sharpes))
    worst_fold = float(np.min(test_returns))
    pos_ratio = float(np.mean(test_returns > 0.0))

    bad_flip = sum(1 for f in folds if f.train_sharpe_like > 0 and f.test_sharpe_like <= 0)
    base_pbo = bad_flip / float(F)
    gap_pen = 0.0
    for f in folds:
        if f.train_sharpe_like > f.test_sharpe_like:
            den = max(3.0, abs(f.train_sharpe_like), abs(f.test_sharpe_like))
            gap_pen += (f.train_sharpe_like - f.test_sharpe_like) / den / float(max(F, 1))
    pbo_like = float(min(1.0, max(0.0, base_pbo + 0.35 * gap_pen)))

    consistency = 1.0 - pbo_like * 0.5
    dsr_like = float(
        np.clip(
            med_te_sh / 2.5 + 0.35 * (pos_ratio - 0.5) + 0.15 * min(1.0, n / 120.0) + 0.2 * consistency - 0.35,
            -1.0,
            1.0,
        )
    )

    blockers: list[str] = []
    warnings: list[str] = []
    marginal: list[str] = []

    if pos_ratio < float(assumptions.min_positive_fold_ratio):
        blockers.append("POSITIVE_FOLD_RATIO_BELOW_THRESHOLD")
    elif pos_ratio < float(assumptions.min_positive_fold_ratio) + 0.09:
        marginal.append("positive_fold_ratio")

    if worst_fold < float(assumptions.max_worst_fold_return) - 1e-9:
        blockers.append("WORST_FOLD_RETURN_BELOW_THRESHOLD")
    elif worst_fold < float(assumptions.max_worst_fold_return) + 0.03:
        marginal.append("worst_fold_return")

    if pbo_like > float(assumptions.max_pbo_like_score) + 1e-9:
        blockers.append("PBO_LIKE_ABOVE_THRESHOLD")
    elif pbo_like > float(assumptions.max_pbo_like_score) - 0.08:
        marginal.append("pbo_like")

    if dsr_like < float(assumptions.min_dsr_like_score) - 1e-9:
        blockers.append("DSR_LIKE_BELOW_THRESHOLD")
    elif dsr_like < float(assumptions.min_dsr_like_score) + 0.06:
        marginal.append("dsr_like")

    if blockers:
        gate = RobustnessGateStatus.BLOCKED
    elif marginal:
        gate = RobustnessGateStatus.WARNING
        warnings.append("ROBUSTNESS_MARGINAL:" + ",".join(marginal))
    else:
        gate = RobustnessGateStatus.PROVEN

    result = RobustnessResult(
        strategy_id=strategy_id,
        batch_id=batch_id,
        run_id=run_id,
        model_label=ROBUSTNESS_MODEL_LABEL,
        dsr_like_model_label=DSR_LIKE_MODEL_LABEL,
        pbo_like_model_label=PBO_LIKE_MODEL_LABEL,
        sample_count=n,
        fold_count=F,
        folds=folds,
        median_test_return=med_te_ret,
        median_test_sharpe_like=med_te_sh,
        worst_fold_return=worst_fold,
        positive_fold_ratio=pos_ratio,
        pbo_like_score=pbo_like,
        dsr_like_score=dsr_like,
        gate_status=gate,
        blockers=blockers,
        warnings=warnings,
    )
    body = result.model_dump(mode="json")
    digest = canonical_json_sha256(body)
    return result.model_copy(update={"robustness_evidence_sha256": digest})


__all__ = ["evaluate_strategy_robustness"]
