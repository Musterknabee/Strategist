"""Toy parameter perturbation fragility (deterministic; research)."""
from __future__ import annotations

import copy
import math
from typing import Any, Callable

import numpy as np

from strategy_validator.contracts.strategy_batch import StrategyTypeId
from strategy_validator.contracts.strategy_parameter_sensitivity import (
    ParameterPerturbationResult,
    ParameterSensitivityGateStatus,
    ParameterSensitivityResult,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from strategy_validator.research.strategy_batch_evaluators import (
    evaluate_mean_reversion,
    evaluate_momentum,
    evaluate_volatility_breakout,
)

def _eval_fn(
    strategy_type: StrategyTypeId,
) -> Callable[[np.ndarray, dict[str, Any]], dict[str, float]]:
    if strategy_type == "momentum":
        return evaluate_momentum
    if strategy_type == "mean_reversion":
        return evaluate_mean_reversion
    return evaluate_volatility_breakout


def _perturbations_for_params(params: dict[str, Any]) -> list[tuple[str, Any, Any]]:
    out: list[tuple[str, Any, Any]] = []
    for key, raw in params.items():
        if isinstance(raw, bool):
            continue
        if isinstance(raw, int):
            base = int(raw)
            if base <= 0:
                continue
            for delta in (-2, -1, 1, 2):
                nv = max(1, base + delta)
                if nv != base:
                    out.append((key, base, nv))
            pct20 = max(1, int(round(base * 0.8)))
            pct12 = max(1, int(round(base * 1.2)))
            if pct20 != base:
                out.append((key, base, pct20))
            if pct12 != base:
                out.append((key, base, pct12))
        elif isinstance(raw, float):
            base = float(raw)
            if not math.isfinite(base) or base == 0.0:
                continue
            for pct in (0.9, 1.1, 0.8, 1.2):
                nv = base * pct
                if abs(nv - base) > 1e-12:
                    out.append((key, base, nv))
    # cap count for determinism
    return out[:48]


def evaluate_parameter_sensitivity(
    *,
    strategy_id: str,
    batch_id: str,
    run_id: str,
    prices: np.ndarray,
    strategy_type: StrategyTypeId,
    params: dict[str, Any],
    synthetic_demo: bool,
) -> ParameterSensitivityResult:
    if synthetic_demo:
        body = ParameterSensitivityResult(
            strategy_id=strategy_id,
            batch_id=batch_id,
            run_id=run_id,
            gate_status=ParameterSensitivityGateStatus.NOT_APPLICABLE,
            blockers=[],
            warnings=["SYNTHETIC_DEMO_NOT_PARAMETER_PROOF"],
        )
        plain = body.model_dump(mode="json")
        return body.model_copy(
            update={"parameter_sensitivity_evidence_sha256": canonical_json_sha256(plain)}
        )

    spec = _perturbations_for_params(params)
    if not spec:
        body = ParameterSensitivityResult(
            strategy_id=strategy_id,
            batch_id=batch_id,
            run_id=run_id,
            gate_status=ParameterSensitivityGateStatus.NOT_APPLICABLE,
            warnings=["NO_PERTURBABLE_PARAMETERS"],
        )
        plain = body.model_dump(mode="json")
        return body.model_copy(
            update={"parameter_sensitivity_evidence_sha256": canonical_json_sha256(plain)}
        )

    fn = _eval_fn(strategy_type)
    base_m = fn(prices, params)
    base_tr = float(base_m.get("total_return", 0.0))
    base_sh = float(base_m.get("sharpe_like", 0.0))

    results: list[ParameterPerturbationResult] = []
    rets: list[float] = []
    for key, old_v, new_v in spec:
        p2 = copy.deepcopy(params)
        if isinstance(old_v, int) and isinstance(new_v, int):
            p2[key] = int(new_v)
        else:
            p2[key] = float(new_v)
        m = fn(prices, p2)
        tr = float(m.get("total_return", 0.0))
        sh = float(m.get("sharpe_like", 0.0))
        results.append(
            ParameterPerturbationResult(
                param_key=key,
                base_value=old_v,
                perturbed_value=new_v,
                total_return=tr,
                sharpe_like=sh,
            )
        )
        rets.append(tr)

    if not rets:
        med = base_tr
        worst = base_tr
        pct_pos = 1.0
    else:
        arr = np.array(rets, dtype=np.float64)
        med = float(np.median(arr))
        worst = float(np.min(arr))
        pct_pos = float(np.mean(arr > 0.0))

    var = float(np.var(np.array(rets, dtype=np.float64))) if rets else 0.0
    one_point = 1.0 if (pct_pos < 0.35 and worst < -0.05) else 0.0

    gate = ParameterSensitivityGateStatus.STABLE
    warnings: list[str] = []
    blockers: list[str] = []

    if worst < -0.25 or pct_pos < 0.25:
        gate = ParameterSensitivityGateStatus.FRAGILE
        blockers.append("PARAMETER_FRAGILITY_SEVERE")
    elif worst < -0.12 or pct_pos < 0.45 or var > 0.08:
        gate = ParameterSensitivityGateStatus.WARNING
        warnings.append("PARAMETER_SENSITIVITY_MARGINAL")
    if one_point > 0.5:
        gate = ParameterSensitivityGateStatus.FRAGILE
        blockers.append("ONE_POINT_OPTIMUM_RISK")

    body = ParameterSensitivityResult(
        strategy_id=strategy_id,
        batch_id=batch_id,
        run_id=run_id,
        base_total_return=base_tr,
        base_sharpe_like=base_sh,
        perturbations=results,
        median_perturbed_return=med,
        worst_perturbed_return=worst,
        pct_positive_perturbations=pct_pos,
        gate_status=gate,
        blockers=blockers,
        warnings=warnings,
    )
    plain = body.model_dump(mode="json")
    return body.model_copy(
        update={"parameter_sensitivity_evidence_sha256": canonical_json_sha256(plain)}
    )


__all__ = ["evaluate_parameter_sensitivity"]
