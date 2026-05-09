"""Single-strategy execution implementation for strategy batch runs."""
from __future__ import annotations

import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.contracts.strategy_batch import (
    StrategyBatchSpec,
    StrategyCandidateSpec,
    StrategyGateSummary,
    StrategyRunResult,
    StrategyRunStatus,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from strategy_validator.research.strategy_batch_runner_common import _write_json
from strategy_validator.research.strategy_batch_runner_single_artifacts import emit_single_strategy_artifacts
from strategy_validator.research.strategy_batch_runner_single_data import resolve_single_strategy_data
from strategy_validator.research.strategy_batch_runner_single_gates import evaluate_single_strategy_gates


def _initial_gate() -> StrategyGateSummary:
    return StrategyGateSummary(
        pit_gate="PENDING",
        data_gate="PENDING",
        data_quality_gate="NOT_RUN",
        market_data_integrity_gate="NOT_RUN",
        robustness_gate="NOT_RUN",
        cpcv_robustness_gate="NOT_RUN",
        execution_realism_gate="PAPER_ASSUMED",
        parameter_sensitivity_gate="NOT_RUN",
        regime_analysis_gate="NOT_RUN",
        data_coverage_gate="NOT_RUN",
        oos_holdout_gate="NOT_RUN",
    )


def run_single_strategy_impl(
    *,
    candidate: StrategyCandidateSpec,
    batch: StrategyBatchSpec,
    run_id: str,
    run_dir: Path,
    allow_synthetic: bool,
    adjudication_hook: Any | None = None,
    deterministic_prices_fn: Any | None = None,
) -> StrategyRunResult:
    """Execute one strategy in an isolated subdirectory under *run_dir*."""

    strat_dir = run_dir / "strategies" / candidate.strategy_id
    strat_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)
    gate = _initial_gate()

    try:
        input_payload = candidate.model_dump(mode="json")
        input_sha = canonical_json_sha256(input_payload)
        _write_json(strat_dir / "input_manifest.json", {"spec": input_payload, "input_spec_sha256": input_sha})

        data_resolution = resolve_single_strategy_data(
            candidate=candidate,
            batch=batch,
            run_id=run_id,
            strat_dir=strat_dir,
            repo_root=Path.cwd(),
            started=started,
            gate=gate,
            allow_synthetic=allow_synthetic,
            deterministic_prices_fn=deterministic_prices_fn,
        )
        if data_resolution.blocked_result is not None:
            return data_resolution.blocked_result
        assert data_resolution.context is not None
        data_context = data_resolution.context

        gate_eval = evaluate_single_strategy_gates(
            candidate=candidate,
            batch=batch,
            run_id=run_id,
            strat_dir=strat_dir,
            gate=gate,
            data_context=data_context,
        )
        artifacts = emit_single_strategy_artifacts(
            candidate=candidate,
            batch=batch,
            run_id=run_id,
            strat_dir=strat_dir,
            gate=gate,
            data_context=data_context,
            gate_eval=gate_eval,
            input_sha=input_sha,
        )

        warnings = list(gate_eval.warnings)
        blockers = list(gate_eval.blockers)
        adjudication_status = "NOT_INVOKED"
        if adjudication_hook is not None:
            adjudication_status, adjudication_warnings = adjudication_hook(
                candidate=candidate,
                batch=batch,
                run_dir=str(strat_dir),
                metrics=gate_eval.metrics_payload,
                evidence_manifest_sha256=artifacts.evidence_manifest_sha256,
            )
            warnings = list(dict.fromkeys([*warnings, *adjudication_warnings]))

        gate.adjudication_gate = adjudication_status
        gate_sha = canonical_json_sha256(gate.model_dump(mode="json"))
        _write_json(strat_dir / "gate_summary.json", {**gate.model_dump(mode="json"), "gate_summary_sha256": gate_sha})

        completed = datetime.now(timezone.utc)
        duration_ms = int((completed - started).total_seconds() * 1000)
        decision = "PAPER_ONLY" if gate_eval.status == StrategyRunStatus.PAPER_ONLY else gate_eval.status.value
        provider_snap = data_context.provider_snap
        cpcv_path = gate_eval.cpcv_path

        return StrategyRunResult(
            strategy_id=candidate.strategy_id,
            strategy_type=candidate.strategy_type,
            status=gate_eval.status,
            started_at_utc=started,
            completed_at_utc=completed,
            duration_ms=duration_ms,
            pit_status=gate_eval.pit_status,
            pit_snapshot_status=gate_eval.pit_snap_s,
            data_status=gate_eval.data_status,
            data_plane=gate_eval.data_plane,
            robustness_status=gate_eval.rob_status,
            execution_realism_status=gate_eval.exec_realism_status,
            execution_realism_digest=gate_eval.er_digest,
            execution_realism_gate=gate_eval.er.gate_status.value,
            execution_realism_model_label=gate_eval.er.model_label,
            execution_realism_est_slippage_bps=gate_eval.er.estimated_slippage_bps,
            execution_realism_est_fee_bps=gate_eval.er.estimated_fees_bps,
            execution_realism_capacity_notional=(gate_eval.er.capacity.capacity_notional if gate_eval.er.capacity else None),
            execution_realism_est_participation=gate_eval.er.estimated_participation_rate,
            robustness_gate_status=gate_eval.rob.gate_status.value,
            robustness_model_label=gate_eval.rob.model_label,
            robustness_evidence_sha256=gate_eval.rob.robustness_evidence_sha256,
            robustness_artifact_path=str(gate_eval.rob_path.resolve()),
            positive_fold_ratio=gate_eval.rob.positive_fold_ratio,
            worst_fold_return=gate_eval.rob.worst_fold_return,
            pbo_like_score=gate_eval.rob.pbo_like_score,
            dsr_like_score=gate_eval.rob.dsr_like_score,
            robustness_fold_count=gate_eval.rob.fold_count,
            cpcv_robustness_gate_status=gate.cpcv_robustness_gate,
            cpcv_evidence_sha256=gate_eval.cpcv.cpcv_evidence_sha256 if gate_eval.cpcv else None,
            cpcv_artifact_path=str(cpcv_path.resolve()) if cpcv_path.is_file() else None,
            data_quality_gate_status=gate_eval.dq.gate_status.value,
            market_data_integrity_gate_status=gate_eval.mdi.gate_status.value,
            market_data_integrity_artifact_path=str(gate_eval.mdi_path.resolve()),
            market_data_integrity_evidence_sha256=gate_eval.mdi.evidence_sha256,
            parameter_sensitivity_gate_status=gate_eval.ps.gate_status.value,
            regime_analysis_gate_status=gate_eval.reg.gate_status,
            data_quality_artifact_path=str(gate_eval.dq_path.resolve()),
            parameter_sensitivity_artifact_path=str(gate_eval.ps_path.resolve()),
            regime_analysis_artifact_path=str(gate_eval.reg_path.resolve()),
            trade_markers_path=str(artifacts.trade_markers_path.resolve()),
            total_return=float(gate_eval.metrics_payload.get("total_return", 0.0)),
            max_drawdown=float(gate_eval.metrics_payload.get("max_drawdown", 0.0)),
            sharpe_like=float(gate_eval.metrics_payload.get("sharpe_like", 0.0)),
            analytics_score=artifacts.analytics_score,
            analytics_rank=None,
            strategy_scorecard_path=str(artifacts.strategy_scorecard_path.resolve()),
            equity_curve_path=str(artifacts.equity_curve_path.resolve()),
            drawdown_curve_path=str(artifacts.drawdown_curve_path.resolve()),
            rolling_metrics_path=str(artifacts.rolling_metrics_path.resolve()),
            fold_performance_path=str(artifacts.fold_performance_path.resolve()),
            charts_compact=artifacts.charts_compact,
            analytics_rank_explanation=artifacts.rank_explanation,
            adjudication_status=adjudication_status,
            decision=decision,
            blockers=blockers,
            warnings=warnings,
            evidence_manifest_path=str(artifacts.evidence_manifest_path.resolve()),
            evidence_manifest_sha256=artifacts.evidence_manifest_sha256,
            data_snapshot_manifest_path=(str(data_context.data_snapshot_path.resolve()) if data_context.data_snapshot_path else None),
            data_snapshot_manifest_sha256=data_context.data_snapshot_sha,
            data_snapshot_digest=gate_eval.ds_digest,
            provider_snapshot_manifest_sha256=provider_snap.manifest_sha256 if provider_snap else None,
            provider_snapshot_source_manifest_path=data_context.provider_snapshot_source_manifest_path,
            provider_license_scope=provider_snap.license_scope if provider_snap else None,
            provider_trust_level=provider_snap.trust_level if provider_snap else None,
            bars_row_count=data_context.bars_row_count,
            metrics=gate_eval.metrics_payload,
            gate_summary=gate,
            compute_backend="cpu",
            compute_worker_model=batch.worker_model,
            cuda_available=False,
        )
    except Exception as exc:  # pragma: no cover - exercised via tests that force failure
        completed = datetime.now(timezone.utc)
        duration_ms = int((completed - started).total_seconds() * 1000)
        return StrategyRunResult(
            strategy_id=candidate.strategy_id,
            status=StrategyRunStatus.FAILED,
            started_at_utc=started,
            completed_at_utc=completed,
            duration_ms=duration_ms,
            pit_status="UNKNOWN",
            data_status="ERROR",
            blockers=[f"RUNNER_EXCEPTION:{type(exc).__name__}"],
            warnings=[traceback.format_exc()],
            gate_summary=gate,
        )


__all__ = ["run_single_strategy_impl"]
