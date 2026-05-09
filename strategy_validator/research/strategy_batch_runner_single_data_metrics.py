"""Data quality, market integrity, and metric gates for one strategy run."""
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
from strategy_validator.contracts.strategy_data_snapshot import (
    StrategyDataSourceClassification,
    StrategyPitSnapshotStatus,
)
from strategy_validator.research.market_data_integrity import evaluate_market_data_integrity
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from strategy_validator.research.strategy_batch_evaluators import evaluate_strategy_metrics
from strategy_validator.research.strategy_batch_runner_common import _enrich_metrics, _write_json
from strategy_validator.research.strategy_batch_runner_single_data import StrategySingleDataContext
from strategy_validator.research.strategy_data_quality import evaluate_local_bars_data_quality


@dataclass(frozen=True)
class StrategySingleDataMetricEvaluation:
    """Data-plane, PIT, and metric gate outputs for one strategy run."""

    warnings: list[str]
    blockers: list[str]
    status: StrategyRunStatus
    metrics_payload: dict[str, Any]
    metrics_sha: str
    ds_digest: str | None
    pit_snap_s: str | None
    data_status: str
    data_plane: str
    pit_status: str
    rob_status: str
    ds_class: str
    ds_label: str
    dq: Any
    dq_path: Path
    mdi: Any
    mdi_path: Path


def evaluate_single_strategy_data_metrics(
    *,
    candidate: StrategyCandidateSpec,
    batch: StrategyBatchSpec,
    run_id: str,
    strat_dir: Path,
    gate: StrategyGateSummary,
    data_context: StrategySingleDataContext,
) -> StrategySingleDataMetricEvaluation:
    """Evaluate data quality, market integrity, strategy metrics, and PIT/data gates."""

    local_snap = data_context.local_snap
    loaded_bars = data_context.loaded_bars
    load_warnings = data_context.load_warnings
    prices = data_context.prices
    opens = data_context.opens
    highs = data_context.highs
    lows = data_context.lows
    volumes = data_context.volumes
    used_synthetic = data_context.used_synthetic
    provider_snap = data_context.provider_snap

    warnings: list[str] = list(load_warnings)
    blockers: list[str] = []
    status = StrategyRunStatus.PASSED

    bars_for_dq: list[Any] = list(loaded_bars) if loaded_bars else []
    dq = evaluate_local_bars_data_quality(
        strategy_id=candidate.strategy_id,
        batch_id=batch.batch_id,
        run_id=run_id,
        bars=bars_for_dq,
        as_of_utc=candidate.as_of_utc,
        synthetic_demo=used_synthetic,
        snapshot=local_snap,
        load_warnings=list(load_warnings),
    )
    gate.data_quality_gate = dq.gate_status.value
    dq_plain = dq.model_dump(mode="json")
    dq_path = strat_dir / "data_quality_result.json"
    _write_json(
        dq_path,
        {**dq_plain, "data_quality_evidence_sha256": dq.data_quality_evidence_sha256},
    )

    mdi = evaluate_market_data_integrity(
        strategy_id=candidate.strategy_id,
        batch_id=batch.batch_id,
        run_id=run_id,
        bars=bars_for_dq,
        as_of_utc=candidate.as_of_utc,
        snapshot=local_snap,
        provider_id=(provider_snap.provider_id if provider_snap else (local_snap.provider_id if local_snap else "synthetic")),
        license_scope=(provider_snap.license_scope if provider_snap else "local_or_synthetic_unverified"),
        trust_level=(provider_snap.trust_level if provider_snap else "local_or_synthetic_unverified"),
        adjusted_status="UNKNOWN",
    )
    gate.market_data_integrity_gate = mdi.gate_status.value
    mdi_plain = mdi.model_dump(mode="json")
    mdi_path = strat_dir / "market_data_integrity_result.json"
    _write_json(mdi_path, {**mdi_plain, "evidence_sha256": mdi.evidence_sha256})
    if mdi.gate_status.value == "BLOCKED":
        blockers.extend(mdi.blockers)
        if status == StrategyRunStatus.PASSED:
            status = StrategyRunStatus.BLOCKED
    elif mdi.gate_status.value == "WARNING":
        warnings.extend(mdi.warnings)

    metrics = evaluate_strategy_metrics(
        strategy_type=candidate.strategy_type,
        prices=prices,
        params=candidate.params,
        opens=opens,
        highs=highs,
        lows=lows,
        volumes=volumes,
    )

    metrics_payload = _enrich_metrics(metrics, prices, candidate, synthetic=used_synthetic)
    hb = int(candidate.params.get("oos_holdout_bars", 0) or 0)
    if hb > 0:
        from strategy_validator.research.strategy_holdout_gate import evaluate_oos_holdout

        ho = evaluate_oos_holdout(
            strategy_type=candidate.strategy_type,
            prices=prices,
            params=candidate.params,
            holdout_bars=hb,
            opens=opens,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )
        gate.oos_holdout_gate = str(ho.get("oos_holdout_gate", "NOT_RUN"))
        for key in ("oos_sharpe_like", "is_sharpe_like", "oos_holdout_bars", "oos_min_sharpe"):
            if key in ho and isinstance(ho[key], (int, float)):
                metrics_payload[key] = float(ho[key])
        if gate.oos_holdout_gate == "BLOCKED":
            blockers.append("OOS_HOLDOUT_SHARPE_BELOW_THRESHOLD")
            status = StrategyRunStatus.BLOCKED
    metrics_sha = canonical_json_sha256(metrics_payload)
    _write_json(strat_dir / "strategy_metrics.json", {"metrics": metrics_payload, "metrics_sha256": metrics_sha})

    ds_digest = local_snap.bars_sha256 if local_snap is not None else None
    pit_snap_s = local_snap.pit_status.value if local_snap is not None else None

    if not used_synthetic and dq.gate_status.value == "BLOCKED":
        blockers.extend(dq.blockers)
        status = StrategyRunStatus.BLOCKED
    elif dq.gate_status.value == "WARNING":
        warnings.extend(dq.warnings)

    if used_synthetic:
        gate.data_gate = "SYNTHETIC_DEMO"
        gate.pit_gate = "DEGRADED_SYNTHETIC"
        gate.execution_realism_gate = "PAPER_FRICTION_ASSUMED"
        gate.data_coverage_gate = "NOT_APPLICABLE_SYNTHETIC"
        gate.sample_count = int(prices.shape[0])
        gate.data_coverage_ratio = float(metrics_payload.get("data_coverage_ratio", 0.0))
        warnings.extend(
            [
                "SYNTHETIC_DEMO_DATA",
                "NOT_LIVE_READY",
                "PAPER_ONLY_POSTURE",
            ]
        )
        status = StrategyRunStatus.PAPER_ONLY
        data_status = "SYNTHETIC_DEMO"
        data_plane = "SYNTHETIC"
        pit_status = "SYNTHETIC"
        rob_status = "NOT_RUN"
        ds_class = "DETERMINISTIC_TOY"
        ds_label = "SYNTHETIC_DEMO"
    else:
        assert local_snap is not None
        if local_snap.source_classification == StrategyDataSourceClassification.PROVIDER_GOVERNED_SNAPSHOT:
            gate.data_gate = "PROVIDER_SNAPSHOT_BARS"
            data_status = "PROVIDER_SNAPSHOT"
            data_plane = "PROVIDER_SNAPSHOT"
            ds_class = StrategyDataSourceClassification.PROVIDER_GOVERNED_SNAPSHOT.value
            ds_label = "PROVIDER_SNAPSHOT"
        else:
            gate.data_gate = "LOCAL_HISTORICAL_BARS"
            data_status = "LOCAL_BARS"
            data_plane = "REAL_LOCAL"
            ds_class = "LOCAL_GOVERNED_BARS"
            ds_label = "LOCAL_FILE_BARS"
        gate.pit_gate = "PIT_VERIFIED" if local_snap.pit_status == StrategyPitSnapshotStatus.PIT_VERIFIED else local_snap.pit_status.value
        gate.execution_realism_gate = "PAPER_FRICTION_ASSUMED"
        gate.sample_count = int(prices.shape[0])
        cov = float(metrics_payload.get("data_coverage_ratio", 0.0))
        gate.data_coverage_ratio = cov
        if cov < 0.5:
            gate.data_coverage_gate = "BLOCKED_LOW_COVERAGE"
            blockers.append("DATA_COVERAGE_BELOW_THRESHOLD")
            status = StrategyRunStatus.BLOCKED
        elif cov < 0.7:
            gate.data_coverage_gate = "WARN_PARTIAL_COVERAGE"
            warnings.append("PARTIAL_DATA_COVERAGE")
        else:
            gate.data_coverage_gate = "PASS"

        if gate.sample_count < 30:
            warnings.append("INSUFFICIENT_SAMPLE_FOR_ROBUSTNESS")

        pit_status = local_snap.pit_status.value
        rob_status = "NOT_RUN"

    return StrategySingleDataMetricEvaluation(
        warnings=warnings,
        blockers=blockers,
        status=status,
        metrics_payload=metrics_payload,
        metrics_sha=metrics_sha,
        ds_digest=ds_digest,
        pit_snap_s=pit_snap_s,
        data_status=data_status,
        data_plane=data_plane,
        pit_status=pit_status,
        rob_status=rob_status,
        ds_class=ds_class,
        ds_label=ds_label,
        dq=dq,
        dq_path=dq_path,
        mdi=mdi,
        mdi_path=mdi_path,
    )


__all__ = ["StrategySingleDataMetricEvaluation", "evaluate_single_strategy_data_metrics"]
