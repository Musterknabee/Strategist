"""Parameter sensitivity, regime, and promotion diagnostics for one strategy run."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from strategy_validator.contracts.strategy_batch import (
    StrategyBatchSpec,
    StrategyCandidateSpec,
    StrategyGateSummary,
    StrategyRunStatus,
)
from strategy_validator.research.strategy_batch_runner_common import _promotion_state, _write_json
from strategy_validator.research.strategy_batch_runner_single_data import StrategySingleDataContext
from strategy_validator.research.strategy_parameter_sensitivity import evaluate_parameter_sensitivity
from strategy_validator.research.strategy_regime_analysis import evaluate_regime_analysis


@dataclass(frozen=True)
class StrategySingleDiagnosticEvaluation:
    """Sensitivity, regime, and promotion outputs for one strategy run."""

    warnings: list[str]
    blockers: list[str]
    status: StrategyRunStatus
    ps: Any
    ps_path: Path
    reg: Any
    reg_path: Path
    promo_ok: bool
    promo_reasons: list[str]


def evaluate_single_strategy_diagnostics(
    *,
    candidate: StrategyCandidateSpec,
    batch: StrategyBatchSpec,
    run_id: str,
    strat_dir: Path,
    gate: StrategyGateSummary,
    data_context: StrategySingleDataContext,
    warnings: list[str],
    blockers: list[str],
    status: StrategyRunStatus,
) -> StrategySingleDiagnosticEvaluation:
    """Evaluate parameter sensitivity, regime analysis, and promotion eligibility."""

    prices = data_context.prices
    opens = data_context.opens
    highs = data_context.highs
    lows = data_context.lows
    volumes = data_context.volumes
    used_synthetic = data_context.used_synthetic

    ps = evaluate_parameter_sensitivity(
        strategy_id=candidate.strategy_id,
        batch_id=batch.batch_id,
        run_id=run_id,
        prices=prices,
        strategy_type=candidate.strategy_type,
        params=candidate.params,
        synthetic_demo=used_synthetic,
        opens=opens,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
    gate.parameter_sensitivity_gate = ps.gate_status.value
    ps_plain = ps.model_dump(mode="json")
    ps_path = strat_dir / "parameter_sensitivity_result.json"
    _write_json(
        ps_path,
        {
            **ps_plain,
            "parameter_sensitivity_evidence_sha256": ps.parameter_sensitivity_evidence_sha256,
        },
    )
    if ps.gate_status.value == "FRAGILE":
        blockers.extend(ps.blockers)
        if status == StrategyRunStatus.PASSED:
            status = StrategyRunStatus.BLOCKED
    elif ps.gate_status.value == "WARNING":
        warnings.extend(ps.warnings)

    reg = evaluate_regime_analysis(
        strategy_id=candidate.strategy_id,
        batch_id=batch.batch_id,
        run_id=run_id,
        prices=prices,
        strategy_type=candidate.strategy_type,
        params=candidate.params,
        synthetic_demo=used_synthetic,
        opens=opens,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )
    gate.regime_analysis_gate = reg.gate_status
    reg_plain = reg.model_dump(mode="json")
    reg_path = strat_dir / "regime_analysis_result.json"
    _write_json(
        reg_path,
        {**reg_plain, "regime_analysis_evidence_sha256": reg.regime_analysis_evidence_sha256},
    )
    if reg.gate_status == "BLOCKED":
        blockers.extend(reg.blockers)
        if status == StrategyRunStatus.PASSED:
            status = StrategyRunStatus.BLOCKED
    elif reg.gate_status == "WARNING":
        warnings.extend(reg.warnings)

    promo_ok, promo_reasons = _promotion_state(
        gate, synthetic=used_synthetic, sample_count=gate.sample_count
    )
    gate.promotion_eligible = promo_ok
    gate.promotion_blocked_reasons = promo_reasons

    return StrategySingleDiagnosticEvaluation(
        warnings=warnings,
        blockers=blockers,
        status=status,
        ps=ps,
        ps_path=ps_path,
        reg=reg,
        reg_path=reg_path,
        promo_ok=promo_ok,
        promo_reasons=promo_reasons,
    )


__all__ = ["StrategySingleDiagnosticEvaluation", "evaluate_single_strategy_diagnostics"]
