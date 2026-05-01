"""Deterministic portfolio allocation simulation over batch scorecards (research/paper only)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.contracts.portfolio_allocation import (
    AllocationGateStatus,
    AllocationMethod,
    PortfolioAllocationRequest,
    PortfolioAllocationResult,
    PortfolioRiskSummary,
    StrategyAllocation,
)
from strategy_validator.contracts.strategy_batch import StrategyBatchRunSummary, StrategyRunStatus
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def _load_scorecard(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _corr_cluster_exposure(
    summary: StrategyBatchRunSummary,
    weights: dict[str, float],
    max_cluster: float,
) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    blockers: list[str] = []
    raw = summary.portfolio_correlation_summary
    if not isinstance(raw, dict):
        return warnings, blockers
    pairs = raw.get("high_correlation_pairs") or []
    if not isinstance(pairs, list):
        return warnings, blockers
    for p in pairs:
        if not isinstance(p, dict):
            continue
        a = str(p.get("a") or p.get("strategy_a") or "")
        b = str(p.get("b") or p.get("strategy_b") or "")
        if not a or not b:
            continue
        exp = float(weights.get(a, 0.0)) + float(weights.get(b, 0.0))
        if exp > max_cluster + 1e-9:
            warnings.append(f"CLUSTER_EXPOSURE_{a}_{b}_{exp:.3f}_EXCEEDS_{max_cluster:.3f}")
    dups = raw.get("duplicate_alpha_warnings") or []
    if isinstance(dups, list) and dups:
        warnings.extend(f"PORTFOLIO_DUP_ALPHA:{x}" for x in dups if isinstance(x, str))
    gate = str(raw.get("portfolio_gate_status") or "")
    if gate == "DUPLICATIVE":
        blockers.append("PORTFOLIO_CORRELATION_MARKED_DUPLICATIVE")
    return warnings, blockers


def simulate_portfolio_allocation(
    summary: StrategyBatchRunSummary,
    *,
    run_dir: Path,
    request: PortfolioAllocationRequest,
) -> PortfolioAllocationResult:
    warnings: list[str] = []
    blockers: list[str] = []
    excluded: list[dict[str, Any]] = []
    candidates: list[tuple[str, dict[str, Any]]] = []

    strat_root = run_dir / "strategies"
    for row in summary.strategies:
        sid = row.strategy_id
        st = row.status
        if request.exclude_blocked and st in (StrategyRunStatus.BLOCKED, StrategyRunStatus.FAILED):
            excluded.append({"strategy_id": sid, "reason": f"STATUS_{st.value}"})
            continue
        sc_path = strat_root / sid / "strategy_scorecard.json"
        sc = _load_scorecard(sc_path) if sc_path.is_file() else None
        if sc is None:
            excluded.append({"strategy_id": sid, "reason": "MISSING_SCORECARD"})
            continue
        pit = str(sc.get("pit_status") or "")
        if request.exclude_synthetic and pit == "SYNTHETIC_DEMO":
            excluded.append({"strategy_id": sid, "reason": "SYNTHETIC_DEMO"})
            continue
        candidates.append((sid, sc))

    if not candidates:
        res = PortfolioAllocationResult(
            request=request,
            allocations=[],
            excluded=excluded,
            allocation_gate_status=AllocationGateStatus.NOT_APPLICABLE,
            warnings=["NO_ALLOCATABLE_STRATEGIES"],
            blockers=["NO_CANDIDATES"],
        )
        body = res.model_dump(mode="json", exclude_none=True)
        stable = {k: v for k, v in body.items() if k not in ("evidence_digest", "generated_at_utc")}
        return res.model_copy(update={"evidence_digest": canonical_json_sha256(stable)})

    ids = [c[0] for c in candidates]
    n = len(ids)
    vols = [max(float(sc.get("volatility") or 1e-6), 1e-6) for _, sc in candidates]
    scores = [float(sc.get("score") or 0.0) for _, sc in candidates]
    weights_raw: dict[str, float] = {sid: 0.0 for sid in ids}

    if request.method == AllocationMethod.equal_weight:
        w = 1.0 / n
        for sid in ids:
            weights_raw[sid] = w
    elif request.method == AllocationMethod.inverse_volatility:
        inv = [1.0 / v for v in vols]
        s = sum(inv)
        for sid, iv in zip(ids, inv, strict=True):
            weights_raw[sid] = iv / s
    elif request.method == AllocationMethod.risk_budget:
        inv = [1.0 / v for v in vols]
        s = sum(inv)
        for sid, iv in zip(ids, inv, strict=True):
            weights_raw[sid] = iv / s
    else:  # capped_score_weight
        pos = [max(sc, 0.0) for sc in scores]
        sp = sum(pos)
        if sp < 1e-12:
            w = 1.0 / n
            for sid in ids:
                weights_raw[sid] = w
        else:
            for sid, p in zip(ids, pos, strict=True):
                weights_raw[sid] = p / sp

    dup_set = set(request.duplicative_strategy_ids)
    if dup_set:
        dup_share = request.max_weight / max(1, len(dup_set))
        for sid in ids:
            if sid in dup_set:
                weights_raw[sid] = min(weights_raw[sid], dup_share)

    # Enforce max/min by iterative capping
    def _renorm(wd: dict[str, float]) -> dict[str, float]:
        s = sum(wd.values())
        if s <= 0:
            return {k: 1.0 / len(wd) for k in wd}
        return {k: v / s for k, v in wd.items()}

    weights = _renorm(weights_raw)
    for _ in range(12):
        over = {k: v for k, v in weights.items() if v > request.max_weight + 1e-12}
        if not over:
            break
        for k in over:
            weights[k] = request.max_weight
        weights = _renorm(weights)

    if request.min_weight > 0:
        weights = {k: max(v, request.min_weight) for k, v in weights.items()}
        weights = _renorm(weights)

    cw, cb = _corr_cluster_exposure(summary, weights, request.max_correlation_cluster_exposure)
    warnings.extend(cw)
    blockers.extend(cb)

    allocations: list[StrategyAllocation] = []
    for sid, sc in candidates:
        allocations.append(
            StrategyAllocation(
                strategy_id=sid,
                weight=float(weights.get(sid, 0.0)),
                score=float(sc.get("score") or 0.0),
                volatility=float(sc.get("volatility") or 0.0),
            )
        )

    # Risk summary: naive variance proxy (weights * scalar vol from scorecard).
    port_var = 0.0
    mdd = 0.0
    for (sid, sc), vol in zip(candidates, vols, strict=True):
        w = float(weights.get(sid, 0.0))
        port_var += (w**2) * (vol**2)
        mdd += w * float(sc.get("max_drawdown") or 0.0)
    hhi = sum(float(weights[sid] ** 2) for sid in ids)

    gate = AllocationGateStatus.ALLOCATABLE
    if blockers:
        gate = AllocationGateStatus.BLOCKED
    elif warnings:
        gate = AllocationGateStatus.WARNING

    res = PortfolioAllocationResult(
        generated_at_utc=datetime.now(timezone.utc),
        request=request,
        allocations=sorted(allocations, key=lambda a: a.strategy_id),
        excluded=excluded,
        risk_summary=PortfolioRiskSummary(
            expected_volatility_like=float(port_var**0.5) if port_var > 0 else None,
            max_drawdown_like=mdd if mdd > 0 else None,
            concentration_hhi=hhi,
        ),
        allocation_gate_status=gate,
        warnings=warnings,
        blockers=blockers,
    )
    body = res.model_dump(mode="json", exclude_none=True)
    stable = {k: v for k, v in body.items() if k not in ("evidence_digest", "generated_at_utc")}
    return res.model_copy(update={"evidence_digest": canonical_json_sha256(stable)})


__all__ = ["simulate_portfolio_allocation"]
