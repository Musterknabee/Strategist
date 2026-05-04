"""CPCV-inspired purged combinatorial evaluation over local bars (bounded; research only)."""
from __future__ import annotations

import csv
import itertools
from datetime import datetime
from pathlib import Path

import numpy as np

from strategy_validator.contracts.strategy_cpcv import (
    CPCVConfig,
    CPCVPathResult,
    CPCVRobustnessResult,
    CPCV_ROBUSTNESS_MODEL_LABEL,
)
from strategy_validator.contracts.strategy_robustness import (
    DSR_LIKE_MODEL_LABEL,
    PBO_LIKE_MODEL_LABEL,
    RobustnessGateStatus,
    RobustnessResult,
    WalkForwardFoldResult,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from strategy_validator.research.strategy_robustness import (
    _max_drawdown,
    _parse_ts,
    _segment_simple_return,
    _sharpe_like,
)


def _load_closes(path: Path) -> tuple[list[datetime], np.ndarray] | None:
    times: list[datetime] = []
    closes: list[float] = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return None
        fields = {f.strip().lower(): f for f in reader.fieldnames if f}
        if "timestamp_utc" not in fields or "close" not in fields:
            return None
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
        return None
    order = sorted(range(len(times)), key=lambda i: times[i])
    t_ord = [times[i] for i in order]
    c_ord = np.array([closes[i] for i in order], dtype=np.float64)
    return t_ord, c_ord


def _group_bounds(n: int, g: int) -> list[tuple[int, int]]:
    edges = [int(round(i * n / g)) for i in range(g + 1)]
    return [(edges[i], edges[i + 1]) for i in range(g)]


def _expand_mask(
    bounds: list[tuple[int, int]],
    test_groups: tuple[int, ...],
    *,
    n: int,
    purge_bars: int,
) -> tuple[set[int], set[int]]:
    test_idx: set[int] = set()
    for gi in test_groups:
        a, b = bounds[gi]
        for i in range(a, b):
            test_idx.add(i)
    train_idx = set(range(n)) - test_idx
    if purge_bars > 0:
        purge_drop = set()
        for i in train_idx:
            for t in test_idx:
                if abs(i - t) <= purge_bars:
                    purge_drop.add(i)
                    break
        train_idx -= purge_drop
    return train_idx, test_idx


def evaluate_strategy_cpcv(
    *,
    strategy_id: str,
    batch_id: str,
    run_id: str,
    filtered_bars_path: Path | None,
    synthetic_demo: bool,
    config: CPCVConfig | None = None,
) -> CPCVRobustnessResult:
    cfg = config or CPCVConfig()
    base = CPCVRobustnessResult(strategy_id=strategy_id, batch_id=batch_id, run_id=run_id)

    if synthetic_demo:
        return base.model_copy(
            update={
                "gate_status": RobustnessGateStatus.NOT_APPLICABLE,
                "blockers": ["SYNTHETIC_DEMO_NOT_CPCV_PROOF"],
                "warnings": ["CPCV_REQUIRES_REAL_LOCAL_BARS"],
                "cpcv_evidence_sha256": canonical_json_sha256(
                    {"gate": "NOT_APPLICABLE", "reason": "synthetic", "strategy_id": strategy_id}
                ),
            }
        )

    if filtered_bars_path is None or not filtered_bars_path.is_file():
        return base.model_copy(
            update={
                "gate_status": RobustnessGateStatus.BLOCKED,
                "blockers": ["MISSING_FILTERED_BARS"],
                "cpcv_evidence_sha256": canonical_json_sha256({"gate": "BLOCKED", "reason": "no_csv"}),
            }
        )

    loaded = _load_closes(filtered_bars_path)
    if loaded is None:
        return base.model_copy(
            update={
                "gate_status": RobustnessGateStatus.BLOCKED,
                "blockers": ["FILTERED_BARS_UNREADABLE"],
                "cpcv_evidence_sha256": canonical_json_sha256({"gate": "BLOCKED", "reason": "cols"}),
            }
        )
    t_ord, c_ord = loaded
    n = int(c_ord.size)
    if n < cfg.min_train_bars + cfg.min_test_bars + cfg.purge_bars * 2:
        return base.model_copy(
            update={
                "gate_status": RobustnessGateStatus.NOT_APPLICABLE,
                "warnings": [
                    "INSUFFICIENT_SAMPLE_FOR_CPCV",
                    f"need_more_bars_than_{cfg.min_train_bars + cfg.min_test_bars}",
                    "CPCV_FALLBACK_TO_WALK_FORWARD_ONLY",
                ],
                "sample_count": n,
                "cpcv_evidence_sha256": canonical_json_sha256(
                    {"gate": "NOT_APPLICABLE", "reason": "short", "n": n}
                ),
            }
        )

    bounds = _group_bounds(n, cfg.n_groups)
    combos = list(itertools.combinations(range(cfg.n_groups), cfg.n_test_groups))
    combos.sort()
    combos = combos[: cfg.max_paths]

    paths: list[CPCVPathResult] = []
    for pi, combo in enumerate(combos):
        train_idx, test_idx = _expand_mask(bounds, combo, n=n, purge_bars=cfg.purge_bars)
        if len(train_idx) < cfg.min_train_bars or len(test_idx) < cfg.min_test_bars:
            continue
        tr_list = sorted(train_idx)
        te_list = sorted(test_idx)
        train_c = c_ord[tr_list]
        test_c = c_ord[te_list]
        tr_ret = _segment_simple_return(train_c)
        te_ret = _segment_simple_return(test_c)
        tr_sh = _sharpe_like(train_c)
        te_sh = _sharpe_like(test_c)
        paths.append(
            CPCVPathResult(
                path_index=pi,
                train_start_utc=t_ord[tr_list[0]],
                train_end_utc=t_ord[tr_list[-1]],
                test_start_utc=t_ord[te_list[0]],
                test_end_utc=t_ord[te_list[-1]],
                train_bar_count=int(train_c.size),
                test_bar_count=int(test_c.size),
                train_return=tr_ret,
                test_return=te_ret,
                train_sharpe_like=tr_sh,
                test_sharpe_like=te_sh,
                max_drawdown_test=_max_drawdown(test_c),
            )
        )

    if not paths:
        return base.model_copy(
            update={
                "gate_status": RobustnessGateStatus.NOT_APPLICABLE,
                "warnings": ["NO_VALID_CPCV_PATHS", "CPCV_FALLBACK_TO_WALK_FORWARD_ONLY"],
                "sample_count": n,
                "cpcv_evidence_sha256": canonical_json_sha256(
                    {"gate": "NOT_APPLICABLE", "reason": "no_paths", "n": n}
                ),
            }
        )

    test_returns = np.array([p.test_return for p in paths], dtype=np.float64)
    test_sharpes = np.array([p.test_sharpe_like for p in paths], dtype=np.float64)
    med_te_ret = float(np.median(test_returns))
    med_te_sh = float(np.median(test_sharpes))
    worst_path = float(np.min(test_returns))
    pos_ratio = float(np.mean(test_returns > 0.0))

    bad_flip = sum(1 for p in paths if p.train_sharpe_like > 0 and p.test_sharpe_like <= 0)
    base_pbo = bad_flip / float(len(paths))
    gap_pen = 0.0
    for p in paths:
        if p.train_sharpe_like > p.test_sharpe_like:
            den = max(3.0, abs(p.train_sharpe_like), abs(p.test_sharpe_like))
            gap_pen += (p.train_sharpe_like - p.test_sharpe_like) / den / float(len(paths))
    pbo_like = float(min(1.0, max(0.0, base_pbo + 0.4 * gap_pen)))

    trials_penalty = min(1.0, len(paths) / 50.0)
    consistency = 1.0 - pbo_like * 0.55
    dsr_like = float(
        np.clip(
            med_te_sh / 2.5
            + 0.35 * (pos_ratio - 0.5)
            + 0.12 * min(1.0, n / 200.0)
            + 0.2 * consistency
            - 0.25 * trials_penalty
            - 0.35,
            -1.0,
            1.0,
        )
    )

    blockers: list[str] = []
    warnings: list[str] = []
    marginal: list[str] = []

    if pos_ratio < float(cfg.min_positive_path_ratio):
        blockers.append("POSITIVE_PATH_RATIO_BELOW_THRESHOLD")
    elif pos_ratio < float(cfg.min_positive_path_ratio) + 0.08:
        marginal.append("positive_path_ratio")

    if worst_path < float(cfg.max_worst_path_return) - 1e-9:
        blockers.append("WORST_PATH_RETURN_BELOW_THRESHOLD")
    elif worst_path < float(cfg.max_worst_path_return) + 0.04:
        marginal.append("worst_path_return")

    if pbo_like > float(cfg.max_pbo_like_score) + 1e-9:
        blockers.append("PBO_LIKE_ABOVE_THRESHOLD")
    elif pbo_like > float(cfg.max_pbo_like_score) - 0.08:
        marginal.append("pbo_like")

    if dsr_like < float(cfg.min_dsr_like_score) - 1e-9:
        blockers.append("DSR_LIKE_BELOW_THRESHOLD")
    elif dsr_like < float(cfg.min_dsr_like_score) + 0.06:
        marginal.append("dsr_like")

    if blockers:
        gate = RobustnessGateStatus.BLOCKED
    elif marginal:
        gate = RobustnessGateStatus.WARNING
        warnings.append("CPCV_MARGINAL:" + ",".join(marginal))
    else:
        gate = RobustnessGateStatus.PROVEN

    result = CPCVRobustnessResult(
        strategy_id=strategy_id,
        batch_id=batch_id,
        run_id=run_id,
        model_label=CPCV_ROBUSTNESS_MODEL_LABEL,
        sample_count=n,
        path_count=len(paths),
        paths=paths,
        median_test_return=med_te_ret,
        median_test_sharpe_like=med_te_sh,
        worst_path_return=worst_path,
        positive_path_ratio=pos_ratio,
        pbo_like_score=pbo_like,
        dsr_like_score=dsr_like,
        trials_penalty=trials_penalty,
        gate_status=gate,
        blockers=blockers,
        warnings=warnings,
    )
    body = result.model_dump(mode="json")
    digest = canonical_json_sha256(body)
    return result.model_copy(update={"cpcv_evidence_sha256": digest})


def cpcv_to_robustness_result(cpcv: CPCVRobustnessResult) -> RobustnessResult:
    folds: list[WalkForwardFoldResult] = []
    for p in cpcv.paths:
        folds.append(
            WalkForwardFoldResult(
                fold_index=p.path_index,
                train_start_utc=p.train_start_utc,
                train_end_utc=p.train_end_utc,
                test_start_utc=p.test_start_utc,
                test_end_utc=p.test_end_utc,
                train_bar_count=p.train_bar_count,
                test_bar_count=p.test_bar_count,
                train_return=p.train_return,
                test_return=p.test_return,
                train_sharpe_like=p.train_sharpe_like,
                test_sharpe_like=p.test_sharpe_like,
                max_drawdown=p.max_drawdown_test,
                positive_test_return=p.test_return > 0,
            )
        )
    rob = RobustnessResult(
        strategy_id=cpcv.strategy_id,
        batch_id=cpcv.batch_id,
        run_id=cpcv.run_id,
        model_label=CPCV_ROBUSTNESS_MODEL_LABEL,
        dsr_like_model_label=DSR_LIKE_MODEL_LABEL,
        pbo_like_model_label=PBO_LIKE_MODEL_LABEL,
        sample_count=cpcv.sample_count,
        fold_count=len(folds),
        folds=folds,
        median_test_return=cpcv.median_test_return,
        median_test_sharpe_like=cpcv.median_test_sharpe_like,
        worst_fold_return=cpcv.worst_path_return,
        positive_fold_ratio=cpcv.positive_path_ratio,
        pbo_like_score=cpcv.pbo_like_score,
        dsr_like_score=cpcv.dsr_like_score,
        gate_status=cpcv.gate_status,
        blockers=list(cpcv.blockers),
        warnings=list(cpcv.warnings),
        robustness_evidence_sha256=cpcv.cpcv_evidence_sha256,
    )
    body = rob.model_dump(mode="json")
    return rob.model_copy(update={"robustness_evidence_sha256": canonical_json_sha256(body)})


__all__ = ["cpcv_to_robustness_result", "evaluate_strategy_cpcv"]
