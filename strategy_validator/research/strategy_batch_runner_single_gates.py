"""Facade for single-strategy gate, robustness, and diagnostic evaluation."""
from __future__ import annotations

from pathlib import Path

from strategy_validator.contracts.strategy_batch import (
    StrategyBatchSpec,
    StrategyCandidateSpec,
    StrategyGateSummary,
)
from strategy_validator.research.strategy_batch_runner_single_data import StrategySingleDataContext
from strategy_validator.research.strategy_batch_runner_single_data_metrics import (
    evaluate_single_strategy_data_metrics,
)
from strategy_validator.research.strategy_batch_runner_single_diagnostics import (
    evaluate_single_strategy_diagnostics,
)
from strategy_validator.research.strategy_batch_runner_single_gate_types import StrategySingleGateEvaluation
from strategy_validator.research.strategy_batch_runner_single_robustness import (
    evaluate_single_strategy_robustness,
)


def evaluate_single_strategy_gates(
    *,
    candidate: StrategyCandidateSpec,
    batch: StrategyBatchSpec,
    run_id: str,
    strat_dir: Path,
    gate: StrategyGateSummary,
    data_context: StrategySingleDataContext,
) -> StrategySingleGateEvaluation:
    """Evaluate all single-strategy gates and write their evidence artifacts."""

    data_metrics = evaluate_single_strategy_data_metrics(
        candidate=candidate,
        batch=batch,
        run_id=run_id,
        strat_dir=strat_dir,
        gate=gate,
        data_context=data_context,
    )
    robustness = evaluate_single_strategy_robustness(
        candidate=candidate,
        batch=batch,
        run_id=run_id,
        strat_dir=strat_dir,
        gate=gate,
        data_context=data_context,
        metrics_payload=data_metrics.metrics_payload,
        warnings=data_metrics.warnings,
        blockers=data_metrics.blockers,
        status=data_metrics.status,
    )
    diagnostics = evaluate_single_strategy_diagnostics(
        candidate=candidate,
        batch=batch,
        run_id=run_id,
        strat_dir=strat_dir,
        gate=gate,
        data_context=data_context,
        warnings=robustness.warnings,
        blockers=robustness.blockers,
        status=robustness.status,
    )

    return StrategySingleGateEvaluation(
        warnings=diagnostics.warnings,
        blockers=diagnostics.blockers,
        status=diagnostics.status,
        metrics_payload=data_metrics.metrics_payload,
        metrics_sha=data_metrics.metrics_sha,
        ds_digest=data_metrics.ds_digest,
        pit_snap_s=data_metrics.pit_snap_s,
        data_status=data_metrics.data_status,
        data_plane=data_metrics.data_plane,
        pit_status=data_metrics.pit_status,
        rob_status=robustness.rob_status,
        ds_class=data_metrics.ds_class,
        ds_label=data_metrics.ds_label,
        dq=data_metrics.dq,
        dq_path=data_metrics.dq_path,
        mdi=data_metrics.mdi,
        mdi_path=data_metrics.mdi_path,
        er=robustness.er,
        er_sha=robustness.er_sha,
        er_digest=robustness.er_digest,
        exec_realism_status=robustness.exec_realism_status,
        rob=robustness.rob,
        rob_charts=robustness.rob_charts,
        rob_path=robustness.rob_path,
        cpcv=robustness.cpcv,
        cpcv_path=robustness.cpcv_path,
        ps=diagnostics.ps,
        ps_path=diagnostics.ps_path,
        reg=diagnostics.reg,
        reg_path=diagnostics.reg_path,
        promo_ok=diagnostics.promo_ok,
        promo_reasons=diagnostics.promo_reasons,
    )


__all__ = ["StrategySingleGateEvaluation", "evaluate_single_strategy_gates"]
