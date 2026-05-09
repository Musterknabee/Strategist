"""Artifact, scorecard, gate, and evidence manifest emission for one strategy run."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from strategy_validator.contracts.strategy_batch import (
    StrategyBatchSpec,
    StrategyCandidateSpec,
    StrategyEvidenceManifest,
    StrategyGateSummary,
)
from strategy_validator.research.strategy_batch_analytics import build_chart_artifacts
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from strategy_validator.research.strategy_batch_runner_common import _write_json
from strategy_validator.research.strategy_batch_runner_single_data import StrategySingleDataContext
from strategy_validator.research.strategy_batch_runner_single_gates import StrategySingleGateEvaluation


@dataclass(frozen=True)
class StrategySingleArtifacts:
    """File paths and digests emitted after single-strategy gate evaluation."""

    analytics_score: float
    charts_compact: dict[str, Any]
    rank_explanation: str | None
    strategy_scorecard_path: Path
    equity_curve_path: Path
    drawdown_curve_path: Path
    rolling_metrics_path: Path
    fold_performance_path: Path
    trade_markers_path: Path
    evidence_manifest_path: Path
    strategy_scorecard_sha256: str
    equity_curve_sha256: str
    drawdown_curve_sha256: str
    rolling_metrics_sha256: str
    fold_performance_sha256: str
    trade_markers_sha256: str
    evidence_manifest_sha256: str


def emit_single_strategy_artifacts(
    *,
    candidate: StrategyCandidateSpec,
    batch: StrategyBatchSpec,
    run_id: str,
    strat_dir: Path,
    gate: StrategyGateSummary,
    data_context: StrategySingleDataContext,
    gate_eval: StrategySingleGateEvaluation,
    input_sha: str,
) -> StrategySingleArtifacts:
    """Emit chart, scorecard, gate-summary, and evidence-manifest artifacts."""

    loaded_bars = data_context.loaded_bars
    timestamps: list[str] = (
        [bar.timestamp_utc.isoformat() for bar in loaded_bars]
        if loaded_bars
        else [str(i) for i in range(int(data_context.prices.shape[0]))]
    )
    art = build_chart_artifacts(
        strategy_id=candidate.strategy_id,
        batch_id=batch.batch_id,
        run_id=run_id,
        timestamps=timestamps,
        prices=data_context.prices,
        strategy_type=candidate.strategy_type,
        params=candidate.params,
        metrics_payload=gate_eval.metrics_payload,
        rob=gate_eval.rob_charts,
        execution_slippage_bps=gate_eval.er.estimated_slippage_bps,
        execution_fee_bps=gate_eval.er.estimated_fees_bps,
        gate_robustness=gate.robustness_gate,
        gate_execution=gate.execution_realism_gate,
        pit_status=gate_eval.pit_status,
        promotion_eligible=gate_eval.promo_ok,
        status=gate_eval.status,
        synthetic_demo=data_context.used_synthetic,
        gate_data_quality=gate.data_quality_gate,
        gate_parameter_sensitivity=gate.parameter_sensitivity_gate,
        gate_regime_analysis=gate.regime_analysis_gate,
        opens=data_context.opens,
        highs=data_context.highs,
        lows=data_context.lows,
        volumes=data_context.volumes,
    )

    scorecard_body = {
        **art["strategy_scorecard"],
        "warnings": list(gate_eval.warnings)[:64],
        "blockers": list(gate_eval.blockers)[:64],
        "market_data_integrity_gate": gate.market_data_integrity_gate,
        "market_data_integrity_evidence_sha256": gate_eval.mdi.evidence_sha256,
    }
    if gate_eval.cpcv is not None:
        scorecard_body = {
            **scorecard_body,
            "cpcv_gate": gate_eval.cpcv.gate_status.value,
            "cpcv_pbo_like": gate_eval.cpcv.pbo_like_score,
            "cpcv_dsr_like": gate_eval.cpcv.dsr_like_score,
            "cpcv_path_count": gate_eval.cpcv.path_count,
        }

    artifact_bodies = {
        "equity_curve": art["equity_curve"],
        "drawdown_curve": art["drawdown_curve"],
        "rolling_metrics": art["rolling_metrics"],
        "fold_performance": art["fold_performance"],
        "strategy_scorecard": scorecard_body,
        "trade_markers": art["trade_markers"],
    }
    artifact_paths = {
        "equity_curve": strat_dir / "equity_curve.json",
        "drawdown_curve": strat_dir / "drawdown_curve.json",
        "rolling_metrics": strat_dir / "rolling_metrics.json",
        "fold_performance": strat_dir / "fold_performance.json",
        "strategy_scorecard": strat_dir / "strategy_scorecard.json",
        "trade_markers": strat_dir / "trade_markers.json",
    }
    artifact_hashes = {name: canonical_json_sha256(body) for name, body in artifact_bodies.items()}
    for name, body in artifact_bodies.items():
        _write_json(artifact_paths[name], {**body, f"{name}_sha256": artifact_hashes[name]})

    gate_sha = canonical_json_sha256(gate.model_dump(mode="json"))
    _write_json(strat_dir / "gate_summary.json", {**gate.model_dump(mode="json"), "gate_summary_sha256": gate_sha})

    local_snap = data_context.local_snap
    provider_snap = data_context.provider_snap
    may_gate_live_promotion = bool(local_snap and local_snap.may_gate_live_promotion) if not data_context.used_synthetic else False
    evidence_manifest = StrategyEvidenceManifest(
        strategy_id=candidate.strategy_id,
        strategy_type=candidate.strategy_type,
        batch_id=batch.batch_id,
        run_id=run_id,
        as_of_utc=candidate.as_of_utc,
        input_spec_sha256=input_sha,
        pit_context_sha256=data_context.pit_sha,
        metrics_sha256=gate_eval.metrics_sha,
        gate_summary_sha256=gate_sha,
        data_source=gate_eval.ds_label,
        data_source_classification=gate_eval.ds_class,
        synthetic_demo=data_context.used_synthetic,
        may_gate_live_promotion=may_gate_live_promotion,
        promotion_eligible=gate.promotion_eligible,
        data_snapshot_digest=gate_eval.ds_digest,
        data_snapshot_manifest_sha256=data_context.data_snapshot_sha,
        provider_snapshot_manifest_sha256=provider_snap.manifest_sha256 if provider_snap else None,
        provider_snapshot_source_manifest_path=data_context.provider_snapshot_source_manifest_path,
        pit_snapshot_status=gate_eval.pit_snap_s,
        bars_row_count=data_context.bars_row_count,
        execution_realism_evidence_sha256=gate_eval.er_sha,
        execution_realism_gate_status=gate_eval.er.gate_status.value,
        robustness_evidence_sha256=gate_eval.rob.robustness_evidence_sha256,
        robustness_gate_status=gate_eval.rob.gate_status.value,
        robustness_model_label=gate_eval.rob.model_label,
        cpcv_evidence_sha256=gate_eval.cpcv.cpcv_evidence_sha256 if gate_eval.cpcv else None,
        cpcv_gate_status=gate_eval.cpcv.gate_status.value if gate_eval.cpcv else None,
        data_quality_evidence_sha256=gate_eval.dq.data_quality_evidence_sha256,
        data_quality_gate_status=gate_eval.dq.gate_status.value,
        market_data_integrity_evidence_sha256=gate_eval.mdi.evidence_sha256,
        market_data_integrity_gate_status=gate_eval.mdi.gate_status.value,
        parameter_sensitivity_evidence_sha256=gate_eval.ps.parameter_sensitivity_evidence_sha256,
        parameter_sensitivity_gate_status=gate_eval.ps.gate_status.value,
        regime_analysis_evidence_sha256=gate_eval.reg.regime_analysis_evidence_sha256,
        regime_analysis_gate_status=gate_eval.reg.gate_status,
        strategy_scorecard_sha256=artifact_hashes["strategy_scorecard"],
        equity_curve_sha256=artifact_hashes["equity_curve"],
        drawdown_curve_sha256=artifact_hashes["drawdown_curve"],
        rolling_metrics_sha256=artifact_hashes["rolling_metrics"],
        fold_performance_sha256=artifact_hashes["fold_performance"],
        trade_markers_sha256=artifact_hashes["trade_markers"],
        warnings=gate_eval.warnings,
        blockers=gate_eval.blockers,
    )
    evidence_body = evidence_manifest.model_dump(mode="json")
    evidence_sha = canonical_json_sha256(evidence_body)
    evidence_path = strat_dir / "evidence_manifest.json"
    _write_json(evidence_path, {**evidence_body, "evidence_manifest_sha256": evidence_sha})

    return StrategySingleArtifacts(
        analytics_score=art["analytics_score"],
        charts_compact=art["charts_compact"],
        rank_explanation=(str(rank) if (rank := scorecard_body.get("rank_explanation")) else None),
        strategy_scorecard_path=artifact_paths["strategy_scorecard"],
        equity_curve_path=artifact_paths["equity_curve"],
        drawdown_curve_path=artifact_paths["drawdown_curve"],
        rolling_metrics_path=artifact_paths["rolling_metrics"],
        fold_performance_path=artifact_paths["fold_performance"],
        trade_markers_path=artifact_paths["trade_markers"],
        evidence_manifest_path=evidence_path,
        strategy_scorecard_sha256=artifact_hashes["strategy_scorecard"],
        equity_curve_sha256=artifact_hashes["equity_curve"],
        drawdown_curve_sha256=artifact_hashes["drawdown_curve"],
        rolling_metrics_sha256=artifact_hashes["rolling_metrics"],
        fold_performance_sha256=artifact_hashes["fold_performance"],
        trade_markers_sha256=artifact_hashes["trade_markers"],
        evidence_manifest_sha256=evidence_sha,
    )


__all__ = ["StrategySingleArtifacts", "emit_single_strategy_artifacts"]
