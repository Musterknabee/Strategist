"""Execution-realism and robustness gates for one strategy run."""
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
from strategy_validator.contracts.strategy_cpcv import CPCVConfig
from strategy_validator.contracts.strategy_execution_realism import ExecutionRealismGateStatus
from strategy_validator.contracts.strategy_robustness import RobustnessGateStatus
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from strategy_validator.research.strategy_batch_runner_common import _write_json
from strategy_validator.research.strategy_batch_runner_single_data import StrategySingleDataContext
from strategy_validator.research.strategy_cpcv import cpcv_to_robustness_result, evaluate_strategy_cpcv
from strategy_validator.research.strategy_execution_realism import evaluate_execution_realism
from strategy_validator.research.strategy_robustness import evaluate_strategy_robustness


@dataclass(frozen=True)
class StrategySingleRobustnessEvaluation:
    """Execution-realism, walk-forward, and CPCV robustness outputs."""

    warnings: list[str]
    blockers: list[str]
    status: StrategyRunStatus
    er: Any
    er_sha: str
    er_digest: str | None
    exec_realism_status: str
    rob: Any
    rob_charts: Any
    rob_path: Path
    cpcv: Any | None
    cpcv_path: Path
    rob_status: str


def evaluate_single_strategy_robustness(
    *,
    candidate: StrategyCandidateSpec,
    batch: StrategyBatchSpec,
    run_id: str,
    strat_dir: Path,
    gate: StrategyGateSummary,
    data_context: StrategySingleDataContext,
    metrics_payload: dict[str, Any],
    warnings: list[str],
    blockers: list[str],
    status: StrategyRunStatus,
) -> StrategySingleRobustnessEvaluation:
    """Evaluate execution realism plus walk-forward/CPCV robustness gates."""

    loaded_bars = data_context.loaded_bars
    used_synthetic = data_context.used_synthetic

    er = evaluate_execution_realism(
        candidate=candidate,
        batch=batch,
        run_id=run_id,
        metrics=metrics_payload,
        bars=loaded_bars,
        synthetic=used_synthetic,
    )
    gate.execution_realism_gate = er.gate_status.value
    er_plain = er.model_dump(mode="json")
    er_sha = canonical_json_sha256(er_plain)
    er_path = strat_dir / "execution_realism_result.json"
    _write_json(er_path, {**er_plain, "execution_realism_evidence_sha256": er_sha})
    er_digest = er.evidence_digest

    if er.gate_status == ExecutionRealismGateStatus.BLOCKED:
        blockers.extend(er.blockers)
        blockers.extend(er.blockers)
        if status == StrategyRunStatus.PASSED:
            status = StrategyRunStatus.BLOCKED
    elif er.gate_status == ExecutionRealismGateStatus.WARNING:
        warnings.extend(er.warnings)
    exec_realism_status = er.gate_status.value

    bars_csv = strat_dir / "filtered_bars.csv"
    mode = candidate.robustness_mode
    rob_wf = None
    cpcv = None
    cpcv_path = strat_dir / "cpcv_result.json"

    if mode in ("walk_forward", "both"):
        rob_wf = evaluate_strategy_robustness(
            strategy_id=candidate.strategy_id,
            batch_id=batch.batch_id,
            run_id=run_id,
            filtered_bars_path=bars_csv if bars_csv.is_file() else None,
            synthetic_demo=used_synthetic,
            assumptions=candidate.robustness_config,
        )

    if mode in ("cpcv", "both"):
        cpcv = evaluate_strategy_cpcv(
            strategy_id=candidate.strategy_id,
            batch_id=batch.batch_id,
            run_id=run_id,
            filtered_bars_path=bars_csv if bars_csv.is_file() else None,
            synthetic_demo=used_synthetic,
            config=CPCVConfig(),
        )
        gate.cpcv_robustness_gate = cpcv.gate_status.value
        cpcv_plain = cpcv.model_dump(mode="json")
        _write_json(
            cpcv_path,
            {**cpcv_plain, "cpcv_evidence_sha256": cpcv.cpcv_evidence_sha256},
        )
        if mode == "both":
            if cpcv.gate_status == RobustnessGateStatus.BLOCKED:
                blockers.extend([f"CPCV:{b}" for b in cpcv.blockers])
                if status == StrategyRunStatus.PASSED:
                    status = StrategyRunStatus.BLOCKED
            elif cpcv.gate_status == RobustnessGateStatus.WARNING:
                warnings.extend(cpcv.warnings)
    else:
        gate.cpcv_robustness_gate = "NOT_RUN"

    if mode == "cpcv":
        assert cpcv is not None
        rob = cpcv_to_robustness_result(cpcv)
        gate.robustness_gate = rob.gate_status.value
    elif mode == "walk_forward":
        assert rob_wf is not None
        rob = rob_wf
        gate.robustness_gate = rob.gate_status.value
    else:
        assert rob_wf is not None
        rob = rob_wf
        gate.robustness_gate = rob_wf.gate_status.value

    rob_charts = rob_wf if mode == "both" else rob

    rob_plain = rob.model_dump(mode="json")
    rob_path = strat_dir / "robustness_result.json"
    _write_json(rob_path, {**rob_plain, "robustness_evidence_sha256": rob.robustness_evidence_sha256})
    rob_status = rob.gate_status.value

    if rob.gate_status == RobustnessGateStatus.BLOCKED:
        blockers.extend(rob.blockers)
        if status == StrategyRunStatus.PASSED:
            status = StrategyRunStatus.BLOCKED
    elif rob.gate_status == RobustnessGateStatus.WARNING:
        warnings.extend(rob.warnings)

    return StrategySingleRobustnessEvaluation(
        warnings=warnings,
        blockers=blockers,
        status=status,
        er=er,
        er_sha=er_sha,
        er_digest=er_digest,
        exec_realism_status=exec_realism_status,
        rob=rob,
        rob_charts=rob_charts,
        rob_path=rob_path,
        cpcv=cpcv,
        cpcv_path=cpcv_path,
        rob_status=rob_status,
    )


__all__ = ["StrategySingleRobustnessEvaluation", "evaluate_single_strategy_robustness"]
