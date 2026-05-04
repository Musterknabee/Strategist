"""Concurrent strategy batch runner: artifacts only; no ledger authority."""
from __future__ import annotations

import csv
import os
import traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from strategy_validator.contracts.strategy_batch import (
    PitPolicy,
    StrategyBatchRunManifest,
    StrategyBatchRunSummary,
    StrategyBatchSpec,
    StrategyCandidateSpec,
    StrategyEvidenceManifest,
    StrategyGateSummary,
    StrategyRunResult,
    StrategyRunStatus,
)
from strategy_validator.contracts.strategy_data_snapshot import (
    ProviderSnapshotDataSourceConfig,
    StrategyDataSnapshotManifest,
    StrategyDataSourceClassification,
    StrategyPitSnapshotStatus,
)
from strategy_validator.contracts.strategy_execution_realism import ExecutionRealismGateStatus
from strategy_validator.contracts.strategy_robustness import RobustnessGateStatus
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from strategy_validator.research.strategy_execution_realism import evaluate_execution_realism
from strategy_validator.contracts.strategy_cpcv import CPCVConfig
from strategy_validator.research.strategy_cpcv import cpcv_to_robustness_result, evaluate_strategy_cpcv
from strategy_validator.research.strategy_robustness import evaluate_strategy_robustness
from strategy_validator.research.strategy_batch_analytics import apply_batch_ranking, build_chart_artifacts
from strategy_validator.research.strategy_data_quality import evaluate_local_bars_data_quality
from strategy_validator.research.market_data_integrity import evaluate_market_data_integrity
from strategy_validator.research.strategy_parameter_sensitivity import evaluate_parameter_sensitivity
from strategy_validator.research.strategy_portfolio_summary import build_batch_portfolio_summary
from strategy_validator.research.strategy_regime_analysis import evaluate_regime_analysis
from strategy_validator.research.strategy_batch_evaluators import (
    deterministic_prices,
    evaluate_strategy_metrics,
)
from strategy_validator.research.strategy_data_loader import (
    StrategyDataLoadError,
    load_local_bars_snapshot,
    load_provider_snapshot_bars,
)


def _resolve_output_base(spec: StrategyBatchSpec) -> Path:
    raw = Path(spec.output_root)
    if raw.is_absolute():
        return raw
    return (Path.cwd() / raw).resolve()


def _run_id_for_batch(spec: StrategyBatchSpec) -> str:
    override = os.environ.get("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "").strip()
    if override:
        return override
    basis = "|".join(sorted(s.strategy_id for s in spec.strategies))
    return canonical_json_sha256({"batch_id": spec.batch_id, "as_of": spec.as_of_utc.isoformat(), "ids": basis})[:24]


def _resolve_batch_run_directory(output_base: Path, batch_id: str, run_id: str) -> Path:
    bid = batch_id.strip()
    rid = run_id.strip()
    if not bid or bid != batch_id or ".." in bid or bid.startswith(("/", "\\")):
        raise ValueError("INVALID_BATCH_ID")
    if not rid or Path(rid).name != rid or ".." in rid or rid.startswith(("/", "\\")):
        raise ValueError("INVALID_RUN_ID")
    return (output_base / bid / rid).resolve()


def _assert_path_under(parent: Path, child: Path) -> None:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise ValueError(f"RUN_DIRECTORY_TRAVERSAL:{child}") from exc


def _prepare_run_directory(*, output_base: Path, batch_id: str, run_id: str, overwrite: bool) -> Path:
    base_r = output_base.resolve()
    run_dir = _resolve_batch_run_directory(base_r, batch_id, run_id)
    _assert_path_under(base_r, run_dir)
    if run_dir.exists():
        if not overwrite:
            raise FileExistsError(f"RUN_DIRECTORY_EXISTS:{run_dir}")
        import shutil

        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _write_json(path: Path, obj: Any) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=_json_dt) + "\n", encoding="utf-8")


def _json_dt(o: Any) -> str:
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(type(o))


def _write_filtered_bars_csv(path: Path, bars: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle)
        w.writerow(["symbol", "timestamp_utc", "open", "high", "low", "close", "volume"])
        for b in bars:
            w.writerow(
                [
                    b.symbol,
                    b.timestamp_utc.isoformat(),
                    b.open,
                    b.high,
                    b.low,
                    b.close,
                    b.volume,
                ]
            )


def _enrich_metrics(
    metrics: dict[str, float],
    prices: np.ndarray,
    candidate: StrategyCandidateSpec,
    *,
    synthetic: bool,
) -> dict[str, float]:
    out = {k: float(v) for k, v in metrics.items()}
    n = int(prices.shape[0])
    out["sample_count"] = float(n)
    out["data_coverage_ratio"] = float(n) / float(max(candidate.lookback_days, 1))
    out["synthetic_demo_flag"] = 1.0 if synthetic else 0.0
    return out


def _promotion_state(
    gate: StrategyGateSummary, *, synthetic: bool, sample_count: int | None
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if synthetic:
        reasons.append("SYNTHETIC_DEMO")
    if not synthetic and gate.pit_gate != "PIT_VERIFIED":
        reasons.append(f"PIT:{gate.pit_gate}")
    if gate.data_coverage_gate.startswith("BLOCKED"):
        reasons.append(f"DATA_COVERAGE:{gate.data_coverage_gate}")
    if not synthetic and gate.data_quality_gate == "BLOCKED":
        reasons.append(f"DATA_QUALITY:{gate.data_quality_gate}")
    if not synthetic and gate.market_data_integrity_gate == "BLOCKED":
        reasons.append("MARKET_DATA_INTEGRITY:BLOCKED")
    if not synthetic and sample_count is not None and sample_count < 30:
        reasons.append("STRATEGY_METRICS_LOW_SAMPLE")
    if not synthetic and gate.robustness_gate != "PROVEN":
        reasons.append(f"ROBUSTNESS:{gate.robustness_gate}")
    if not synthetic and gate.cpcv_robustness_gate not in ("NOT_RUN", "NOT_APPLICABLE", "PROVEN"):
        reasons.append(f"CPCV:{gate.cpcv_robustness_gate}")
    if not synthetic and gate.execution_realism_gate != "PROVEN":
        reasons.append("EXECUTION_REALISM_NOT_PROVEN")
    if not synthetic and gate.parameter_sensitivity_gate == "FRAGILE":
        reasons.append("PARAMETER_SENSITIVITY:FRAGILE")
    if not synthetic and gate.regime_analysis_gate == "BLOCKED":
        reasons.append("REGIME_ANALYSIS:BLOCKED")
    if not synthetic and gate.oos_holdout_gate == "BLOCKED":
        reasons.append("OOS_HOLDOUT:BLOCKED")
    eligible = len(reasons) == 0
    return eligible, reasons


def run_single_strategy(
    *,
    candidate: StrategyCandidateSpec,
    batch: StrategyBatchSpec,
    run_id: str,
    run_dir: Path,
    allow_synthetic: bool,
    adjudication_hook: Any | None = None,
) -> StrategyRunResult:
    """Execute one strategy in an isolated subdirectory under *run_dir*."""

    strat_dir = run_dir / "strategies" / candidate.strategy_id
    strat_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)
    result = StrategyRunResult(strategy_id=candidate.strategy_id, started_at_utc=started, status=StrategyRunStatus.RUNNING)
    gate = StrategyGateSummary(
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

    try:
        repo_root = Path.cwd()
        input_payload = candidate.model_dump(mode="json")
        input_sha = canonical_json_sha256(input_payload)
        _write_json(strat_dir / "input_manifest.json", {"spec": input_payload, "input_spec_sha256": input_sha})

        local_snap = None
        loaded_bars: list[Any] | None = None
        load_warnings: list[str] = []
        prices: np.ndarray | None = None
        opens: np.ndarray | None = None
        highs: np.ndarray | None = None
        lows: np.ndarray | None = None
        volumes: np.ndarray | None = None
        used_synthetic = False
        data_snapshot_path: Path | None = None
        data_snapshot_sha: str | None = None
        bars_row_count: int | None = None
        provider_snap = None
        provider_snapshot_source_manifest_path: str | None = None

        if candidate.data_source is not None and candidate.data_source.kind == "local_bars":
            try:
                loaded = load_local_bars_snapshot(
                    repo_root=repo_root,
                    candidate=candidate,
                    batch=batch,
                    data_source=candidate.data_source,
                    retrieved_at_utc=started,
                )
                local_snap = loaded.snapshot
                loaded_bars = list(loaded.bars)
                load_warnings = list(loaded.warnings)
                prices = np.array([b.close for b in loaded.bars], dtype=np.float64)
                opens = np.array([b.open for b in loaded.bars], dtype=np.float64)
                highs = np.array([b.high for b in loaded.bars], dtype=np.float64)
                lows = np.array([b.low for b in loaded.bars], dtype=np.float64)
                volumes = np.array([b.volume for b in loaded.bars], dtype=np.float64)
                bars_row_count = len(loaded.bars)
                filt_path = strat_dir / "filtered_bars.csv"
                _write_filtered_bars_csv(filt_path, loaded.bars)
                dsm = StrategyDataSnapshotManifest(
                    strategy_id=candidate.strategy_id,
                    batch_id=batch.batch_id,
                    run_id=run_id,
                    snapshot=local_snap,
                    compute_backend="cpu",
                    extra={"max_workers_declared": batch.max_workers, "worker_model": batch.worker_model},
                )
                dsm_body = dsm.model_dump(mode="json")
                data_snapshot_sha = canonical_json_sha256(dsm_body)
                data_snapshot_path = strat_dir / "data_snapshot_manifest.json"
                _write_json(data_snapshot_path, {**dsm_body, "data_snapshot_manifest_sha256": data_snapshot_sha})
            except StrategyDataLoadError as exc:
                load_warnings = [f"LOCAL_BARS_LOAD:{b}" for b in exc.blockers]

        if candidate.data_source is not None and candidate.data_source.kind == "provider_snapshot":
            try:
                loaded, provider_snap = load_provider_snapshot_bars(
                    repo_root=repo_root,
                    candidate=candidate,
                    batch=batch,
                    data_source=candidate.data_source,
                    retrieved_at_utc=started,
                )
                local_snap = loaded.snapshot
                loaded_bars = list(loaded.bars)
                load_warnings = list(loaded.warnings)
                prices = np.array([b.close for b in loaded.bars], dtype=np.float64)
                opens = np.array([b.open for b in loaded.bars], dtype=np.float64)
                highs = np.array([b.high for b in loaded.bars], dtype=np.float64)
                lows = np.array([b.low for b in loaded.bars], dtype=np.float64)
                volumes = np.array([b.volume for b in loaded.bars], dtype=np.float64)
                bars_row_count = len(loaded.bars)
                filt_path = strat_dir / "filtered_bars.csv"
                _write_filtered_bars_csv(filt_path, loaded.bars)
                if isinstance(candidate.data_source, ProviderSnapshotDataSourceConfig):
                    provider_snapshot_source_manifest_path = candidate.data_source.manifest_path
                dsm_extra = {
                    "max_workers_declared": batch.max_workers,
                    "worker_model": batch.worker_model,
                    "provider_snapshot_manifest_sha256": provider_snap.manifest_sha256,
                    "provider_snapshot_manifest_spec_path": candidate.data_source.manifest_path,
                }
                dsm = StrategyDataSnapshotManifest(
                    strategy_id=candidate.strategy_id,
                    batch_id=batch.batch_id,
                    run_id=run_id,
                    snapshot=local_snap,
                    compute_backend="cpu",
                    extra=dsm_extra,
                )
                dsm_body = dsm.model_dump(mode="json")
                data_snapshot_sha = canonical_json_sha256(dsm_body)
                data_snapshot_path = strat_dir / "data_snapshot_manifest.json"
                _write_json(data_snapshot_path, {**dsm_body, "data_snapshot_manifest_sha256": data_snapshot_sha})
            except StrategyDataLoadError as exc:
                load_warnings = [f"PROVIDER_SNAPSHOT_LOAD:{b}" for b in exc.blockers]

        if prices is None:
            if (
                candidate.data_source is not None
                and candidate.data_source.kind == "provider_snapshot"
            ):
                completed = datetime.now(timezone.utc)
                dur = int((completed - started).total_seconds() * 1000)
                gate.data_gate = "PROVIDER_SNAPSHOT_LOAD_FAILED"
                gate.pit_gate = "BLOCKED"
                blk = load_warnings or ["PROVIDER_SNAPSHOT_LOAD_FAILED"]
                return StrategyRunResult(
                    strategy_id=candidate.strategy_id,
                    status=StrategyRunStatus.BLOCKED,
                    started_at_utc=started,
                    completed_at_utc=completed,
                    duration_ms=dur,
                    pit_status="BLOCKED",
                    pit_snapshot_status=None,
                    data_status="PROVIDER_SNAPSHOT",
                    data_plane="NO_BARS",
                    blockers=list(dict.fromkeys(blk)),
                    warnings=[],
                    gate_summary=gate,
                    compute_backend="cpu",
                    compute_worker_model="thread_pool",
                    cuda_available=False,
                )
            if batch.pit_policy == PitPolicy.STRICT:
                completed = datetime.now(timezone.utc)
                dur = int((completed - started).total_seconds() * 1000)
                gate.pit_gate = "BLOCKED_STRICT_NO_VERIFIED_DATA"
                gate.data_gate = "MISSING_LOCAL_BARS"
                return StrategyRunResult(
                    strategy_id=candidate.strategy_id,
                    status=StrategyRunStatus.BLOCKED,
                    started_at_utc=started,
                    completed_at_utc=completed,
                    duration_ms=dur,
                    pit_status="BLOCKED",
                    pit_snapshot_status=None,
                    data_status="MISSING_PIT",
                    data_plane="NO_BARS",
                    blockers=["STRICT_REQUIRES_LOCAL_PIT_VERIFIED_BARS", *load_warnings],
                    warnings=["PIT_STRICT_BLOCKED"],
                    gate_summary=gate,
                    compute_backend="cpu",
                    compute_worker_model="thread_pool",
                    cuda_available=False,
                )
            if not allow_synthetic:
                completed = datetime.now(timezone.utc)
                dur = int((completed - started).total_seconds() * 1000)
                gate.data_gate = "BLOCKED_NO_SYNTHETIC"
                gate.pit_gate = "BLOCKED"
                return StrategyRunResult(
                    strategy_id=candidate.strategy_id,
                    status=StrategyRunStatus.BLOCKED,
                    started_at_utc=started,
                    completed_at_utc=completed,
                    duration_ms=dur,
                    pit_status="BLOCKED",
                    data_status="NO_DATA",
                    data_plane="EMPTY",
                    blockers=["NO_SYNTHETIC_DATA_PATH", *load_warnings],
                    gate_summary=gate,
                    compute_backend="cpu",
                    compute_worker_model="thread_pool",
                    cuda_available=False,
                )
            seed = f"{batch.batch_id}|{run_id}|{candidate.strategy_id}|{candidate.as_of_utc.isoformat()}"
            n = max(32, min(512, candidate.lookback_days))
            prices = deterministic_prices(seed=seed, n=n)
            opens = prices.copy()
            highs = prices * 1.002
            lows = prices * 0.998
            volumes = np.ones_like(prices, dtype=np.float64) * 1000.0
            used_synthetic = True

        if batch.pit_policy == PitPolicy.STRICT and used_synthetic:
            completed = datetime.now(timezone.utc)
            dur = int((completed - started).total_seconds() * 1000)
            gate.pit_gate = "BLOCKED_STRICT_SYNTHETIC"
            gate.data_gate = "SYNTHETIC_NOT_ALLOWED_UNDER_STRICT"
            return StrategyRunResult(
                strategy_id=candidate.strategy_id,
                status=StrategyRunStatus.BLOCKED,
                started_at_utc=started,
                completed_at_utc=completed,
                duration_ms=dur,
                pit_status="BLOCKED",
                data_status="SYNTHETIC_DEMO",
                data_plane="SYNTHETIC",
                blockers=["STRICT_SYNTHETIC_FORBIDDEN"],
                warnings=["PIT_STRICT_BLOCKED"],
                gate_summary=gate,
                compute_backend="cpu",
                compute_worker_model="thread_pool",
                cuda_available=False,
            )

        if (
            batch.pit_policy == PitPolicy.STRICT
            and local_snap is not None
            and local_snap.pit_status != StrategyPitSnapshotStatus.PIT_VERIFIED
        ):
            completed = datetime.now(timezone.utc)
            dur = int((completed - started).total_seconds() * 1000)
            gate.pit_gate = f"BLOCKED_{local_snap.pit_status.value}"
            gate.data_gate = "LOCAL_BARS_NOT_VERIFIED"
            return StrategyRunResult(
                strategy_id=candidate.strategy_id,
                status=StrategyRunStatus.BLOCKED,
                started_at_utc=started,
                completed_at_utc=completed,
                duration_ms=dur,
                pit_status="BLOCKED",
                pit_snapshot_status=local_snap.pit_status.value,
                data_status="PIT_NOT_VERIFIED",
                data_plane="REAL_LOCAL",
                blockers=["STRICT_REQUIRES_PIT_VERIFIED_SNAPSHOT"],
                warnings=load_warnings,
                gate_summary=gate,
                data_snapshot_manifest_path=str(data_snapshot_path.resolve()) if data_snapshot_path else None,
                data_snapshot_manifest_sha256=data_snapshot_sha,
                data_snapshot_digest=local_snap.bars_sha256,
                bars_row_count=bars_row_count,
                compute_backend="cpu",
                compute_worker_model="thread_pool",
                cuda_available=False,
            )

        pit_ok = not used_synthetic and (
            local_snap is None or local_snap.pit_status == StrategyPitSnapshotStatus.PIT_VERIFIED
        )
        pit_classification = "LOCAL_GOVERNED_BARS"
        if used_synthetic:
            pit_classification = "SYNTHETIC_DEMO"
        elif (
            local_snap is not None
            and local_snap.source_classification == StrategyDataSourceClassification.PROVIDER_GOVERNED_SNAPSHOT
        ):
            pit_classification = "PROVIDER_GOVERNED_SNAPSHOT"
        pit_context = {
            "as_of_utc": candidate.as_of_utc.isoformat(),
            "pit_available": pit_ok,
            "pit_policy": batch.pit_policy.value,
            "classification": pit_classification,
            "pit_snapshot_status": None if local_snap is None else local_snap.pit_status.value,
        }
        pit_sha = canonical_json_sha256(pit_context)
        _write_json(strat_dir / "pit_context.json", {**pit_context, "pit_context_sha256": pit_sha})

        warnings: list[str] = list(load_warnings)
        blockers: list[str] = []
        status = StrategyRunStatus.PASSED
        may_promo_ev = False

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

        ts_list: list[str] = (
            [b.timestamp_utc.isoformat() for b in loaded_bars]
            if loaded_bars
            else [str(i) for i in range(int(prices.shape[0]))]
        )
        art = build_chart_artifacts(
            strategy_id=candidate.strategy_id,
            batch_id=batch.batch_id,
            run_id=run_id,
            timestamps=ts_list,
            prices=prices,
            strategy_type=candidate.strategy_type,
            params=candidate.params,
            metrics_payload=metrics_payload,
            rob=rob_charts,
            execution_slippage_bps=er.estimated_slippage_bps,
            execution_fee_bps=er.estimated_fees_bps,
            gate_robustness=gate.robustness_gate,
            gate_execution=gate.execution_realism_gate,
            pit_status=pit_status,
            promotion_eligible=promo_ok,
            status=status,
            synthetic_demo=used_synthetic,
            gate_data_quality=gate.data_quality_gate,
            gate_parameter_sensitivity=gate.parameter_sensitivity_gate,
            gate_regime_analysis=gate.regime_analysis_gate,
            opens=opens,
            highs=highs,
            lows=lows,
            volumes=volumes,
        )
        eq_body = art["equity_curve"]
        dd_body = art["drawdown_curve"]
        rm_body = art["rolling_metrics"]
        fp_body = art["fold_performance"]
        sc_body = art["strategy_scorecard"]
        sc_body = {
            **sc_body,
            "warnings": list(warnings)[:64],
            "blockers": list(blockers)[:64],
            "market_data_integrity_gate": gate.market_data_integrity_gate,
            "market_data_integrity_evidence_sha256": mdi.evidence_sha256,
        }
        if cpcv is not None:
            sc_body = {
                **sc_body,
                "cpcv_gate": cpcv.gate_status.value,
                "cpcv_pbo_like": cpcv.pbo_like_score,
                "cpcv_dsr_like": cpcv.dsr_like_score,
                "cpcv_path_count": cpcv.path_count,
            }
        tm_body = art["trade_markers"]
        eq_path = strat_dir / "equity_curve.json"
        dd_path = strat_dir / "drawdown_curve.json"
        rm_path = strat_dir / "rolling_metrics.json"
        fp_path = strat_dir / "fold_performance.json"
        sc_path = strat_dir / "strategy_scorecard.json"
        tm_path = strat_dir / "trade_markers.json"
        eq_h = canonical_json_sha256(eq_body)
        dd_h = canonical_json_sha256(dd_body)
        rm_h = canonical_json_sha256(rm_body)
        fp_h = canonical_json_sha256(fp_body)
        sc_h = canonical_json_sha256(sc_body)
        tm_h = canonical_json_sha256(tm_body)
        _write_json(eq_path, {**eq_body, "equity_curve_sha256": eq_h})
        _write_json(dd_path, {**dd_body, "drawdown_curve_sha256": dd_h})
        _write_json(rm_path, {**rm_body, "rolling_metrics_sha256": rm_h})
        _write_json(fp_path, {**fp_body, "fold_performance_sha256": fp_h})
        _write_json(sc_path, {**sc_body, "strategy_scorecard_sha256": sc_h})
        _write_json(tm_path, {**tm_body, "trade_markers_sha256": tm_h})

        gate_sha = canonical_json_sha256(gate.model_dump(mode="json"))
        _write_json(strat_dir / "gate_summary.json", {**gate.model_dump(mode="json"), "gate_summary_sha256": gate_sha})

        if used_synthetic:
            may_promo_ev = False
        else:
            may_promo_ev = bool(local_snap and local_snap.may_gate_live_promotion)

        ev = StrategyEvidenceManifest(
            strategy_id=candidate.strategy_id,
            strategy_type=candidate.strategy_type,
            batch_id=batch.batch_id,
            run_id=run_id,
            as_of_utc=candidate.as_of_utc,
            input_spec_sha256=input_sha,
            pit_context_sha256=pit_sha,
            metrics_sha256=metrics_sha,
            gate_summary_sha256=gate_sha,
            data_source=ds_label,
            data_source_classification=ds_class,
            synthetic_demo=used_synthetic,
            may_gate_live_promotion=may_promo_ev,
            promotion_eligible=gate.promotion_eligible,
            data_snapshot_digest=ds_digest,
            data_snapshot_manifest_sha256=data_snapshot_sha,
            provider_snapshot_manifest_sha256=provider_snap.manifest_sha256 if provider_snap else None,
            provider_snapshot_source_manifest_path=provider_snapshot_source_manifest_path,
            pit_snapshot_status=pit_snap_s,
            bars_row_count=bars_row_count,
            execution_realism_evidence_sha256=er_sha,
            execution_realism_gate_status=er.gate_status.value,
            robustness_evidence_sha256=rob.robustness_evidence_sha256,
            robustness_gate_status=rob.gate_status.value,
            robustness_model_label=rob.model_label,
            cpcv_evidence_sha256=cpcv.cpcv_evidence_sha256 if cpcv else None,
            cpcv_gate_status=cpcv.gate_status.value if cpcv else None,
            data_quality_evidence_sha256=dq.data_quality_evidence_sha256,
            data_quality_gate_status=dq.gate_status.value,
            market_data_integrity_evidence_sha256=mdi.evidence_sha256,
            market_data_integrity_gate_status=mdi.gate_status.value,
            parameter_sensitivity_evidence_sha256=ps.parameter_sensitivity_evidence_sha256,
            parameter_sensitivity_gate_status=ps.gate_status.value,
            regime_analysis_evidence_sha256=reg.regime_analysis_evidence_sha256,
            regime_analysis_gate_status=reg.gate_status,
            strategy_scorecard_sha256=sc_h,
            equity_curve_sha256=eq_h,
            drawdown_curve_sha256=dd_h,
            rolling_metrics_sha256=rm_h,
            fold_performance_sha256=fp_h,
            trade_markers_sha256=tm_h,
            warnings=warnings,
            blockers=blockers,
        )
        ev_body = ev.model_dump(mode="json")
        ev_sha = canonical_json_sha256(ev_body)
        ev_path = strat_dir / "evidence_manifest.json"
        _write_json(ev_path, {**ev_body, "evidence_manifest_sha256": ev_sha})

        completed = datetime.now(timezone.utc)
        dur = int((completed - started).total_seconds() * 1000)

        adj_status = "NOT_INVOKED"
        if adjudication_hook is not None:
            adj_status, adj_warnings = adjudication_hook(
                candidate=candidate,
                batch=batch,
                run_dir=str(strat_dir),
                metrics=metrics_payload,
                evidence_manifest_sha256=ev_sha,
            )
            warnings = list(dict.fromkeys([*warnings, *adj_warnings]))

        gate.adjudication_gate = adj_status
        gate_sha2 = canonical_json_sha256(gate.model_dump(mode="json"))
        _write_json(strat_dir / "gate_summary.json", {**gate.model_dump(mode="json"), "gate_summary_sha256": gate_sha2})

        decision = status.value
        if status == StrategyRunStatus.PAPER_ONLY:
            decision = "PAPER_ONLY"

        result = StrategyRunResult(
            strategy_id=candidate.strategy_id,
            strategy_type=candidate.strategy_type,
            status=status,
            started_at_utc=started,
            completed_at_utc=completed,
            duration_ms=dur,
            pit_status=pit_status,
            pit_snapshot_status=pit_snap_s,
            data_status=data_status,
            data_plane=data_plane,
            robustness_status=rob_status,
            execution_realism_status=exec_realism_status,
            execution_realism_digest=er_digest,
            execution_realism_gate=er.gate_status.value,
            execution_realism_model_label=er.model_label,
            execution_realism_est_slippage_bps=er.estimated_slippage_bps,
            execution_realism_est_fee_bps=er.estimated_fees_bps,
            execution_realism_capacity_notional=er.capacity.capacity_notional if er.capacity else None,
            execution_realism_est_participation=er.estimated_participation_rate,
            robustness_gate_status=rob.gate_status.value,
            robustness_model_label=rob.model_label,
            robustness_evidence_sha256=rob.robustness_evidence_sha256,
            robustness_artifact_path=str(rob_path.resolve()),
            positive_fold_ratio=rob.positive_fold_ratio,
            worst_fold_return=rob.worst_fold_return,
            pbo_like_score=rob.pbo_like_score,
            dsr_like_score=rob.dsr_like_score,
            robustness_fold_count=rob.fold_count,
            cpcv_robustness_gate_status=gate.cpcv_robustness_gate,
            cpcv_evidence_sha256=cpcv.cpcv_evidence_sha256 if cpcv else None,
            cpcv_artifact_path=str(cpcv_path.resolve()) if cpcv_path.is_file() else None,
            data_quality_gate_status=dq.gate_status.value,
            market_data_integrity_gate_status=mdi.gate_status.value,
            market_data_integrity_artifact_path=str(mdi_path.resolve()),
            market_data_integrity_evidence_sha256=mdi.evidence_sha256,
            parameter_sensitivity_gate_status=ps.gate_status.value,
            regime_analysis_gate_status=reg.gate_status,
            data_quality_artifact_path=str(dq_path.resolve()),
            parameter_sensitivity_artifact_path=str(ps_path.resolve()),
            regime_analysis_artifact_path=str(reg_path.resolve()),
            trade_markers_path=str(tm_path.resolve()),
            total_return=float(metrics_payload.get("total_return", 0.0)),
            max_drawdown=float(metrics_payload.get("max_drawdown", 0.0)),
            sharpe_like=float(metrics_payload.get("sharpe_like", 0.0)),
            analytics_score=art["analytics_score"],
            analytics_rank=None,
            strategy_scorecard_path=str(sc_path.resolve()),
            equity_curve_path=str(eq_path.resolve()),
            drawdown_curve_path=str(dd_path.resolve()),
            rolling_metrics_path=str(rm_path.resolve()),
            fold_performance_path=str(fp_path.resolve()),
            charts_compact=art["charts_compact"],
            analytics_rank_explanation=(str(s) if (s := sc_body.get("rank_explanation")) else None),
            adjudication_status=adj_status,
            decision=decision,
            blockers=blockers,
            warnings=warnings,
            evidence_manifest_path=str(ev_path.resolve()),
            evidence_manifest_sha256=ev_sha,
            data_snapshot_manifest_path=str(data_snapshot_path.resolve()) if data_snapshot_path else None,
            data_snapshot_manifest_sha256=data_snapshot_sha,
            data_snapshot_digest=ds_digest,
            provider_snapshot_manifest_sha256=provider_snap.manifest_sha256 if provider_snap else None,
            provider_snapshot_source_manifest_path=provider_snapshot_source_manifest_path,
            provider_license_scope=provider_snap.license_scope if provider_snap else None,
            provider_trust_level=provider_snap.trust_level if provider_snap else None,
            bars_row_count=bars_row_count,
            metrics=metrics_payload,
            gate_summary=gate,
            compute_backend="cpu",
            compute_worker_model=batch.worker_model,
            cuda_available=False,
        )
        return result
    except Exception as exc:  # pragma: no cover - exercised via tests that force failure
        completed = datetime.now(timezone.utc)
        dur = int((completed - started).total_seconds() * 1000)
        return StrategyRunResult(
            strategy_id=candidate.strategy_id,
            status=StrategyRunStatus.FAILED,
            started_at_utc=started,
            completed_at_utc=completed,
            duration_ms=dur,
            pit_status="UNKNOWN",
            data_status="ERROR",
            blockers=[f"RUNNER_EXCEPTION:{type(exc).__name__}"],
            warnings=[traceback.format_exc()],
            gate_summary=gate,
        )


def _process_pool_run_single(
    payload: tuple[dict[str, Any], dict[str, Any], str, str, bool],
) -> StrategyRunResult:
    cand_dict, spec_dict, run_id, run_dir_str, allow_synthetic = payload
    cand = StrategyCandidateSpec.model_validate(cand_dict)
    spec = StrategyBatchSpec.model_validate(spec_dict)
    return run_single_strategy(
        candidate=cand,
        batch=spec,
        run_id=run_id,
        run_dir=Path(run_dir_str),
        allow_synthetic=allow_synthetic,
        adjudication_hook=None,
    )


def run_strategy_batch(
    spec: StrategyBatchSpec,
    *,
    allow_synthetic: bool = True,
    fail_fast: bool = False,
    adjudication_hook: Any | None = None,
    run_id: str | None = None,
    overwrite: bool = False,
) -> StrategyBatchRunSummary:
    """Run all strategies in *spec* concurrently; write manifests under output_root."""

    base = _resolve_output_base(spec)
    run_id_final = run_id.strip() if run_id and run_id.strip() else _run_id_for_batch(spec)
    run_dir = _prepare_run_directory(
        output_base=base, batch_id=spec.batch_id, run_id=run_id_final, overwrite=overwrite
    )

    spec_sha = canonical_json_sha256(spec.model_dump(mode="json"))
    manifest = StrategyBatchRunManifest(
        batch_id=spec.batch_id,
        run_id=run_id_final,
        spec_sha256=spec_sha,
        mode=spec.mode,
        as_of_utc=spec.as_of_utc,
        created_at_utc=datetime.now(timezone.utc),
        output_dir=str(run_dir),
        strategy_count=len(spec.strategies),
        max_workers=spec.max_workers,
        fail_fast=fail_fast,
        allow_synthetic=allow_synthetic,
        adjudication_enabled=adjudication_hook is not None,
        compute_backend="cpu",
        compute_worker_model=spec.worker_model,
        cuda_available=False,
    )
    _write_json(run_dir / "batch_manifest.json", manifest.model_dump(mode="json"))

    results: list[StrategyRunResult] = []
    if fail_fast:
        for cand in sorted(spec.strategies, key=lambda s: s.strategy_id):
            r = run_single_strategy(
                candidate=cand,
                batch=spec,
                run_id=run_id_final,
                run_dir=run_dir,
                allow_synthetic=allow_synthetic,
                adjudication_hook=adjudication_hook,
            )
            results.append(r)
            if r.status in (StrategyRunStatus.FAILED, StrategyRunStatus.BLOCKED):
                break
    else:
        max_workers = min(spec.max_workers, len(spec.strategies))
        if spec.worker_model == "process_pool":
            if adjudication_hook is not None:
                raise ValueError("WORKER_MODEL_PROCESS_POOL_REQUIRES_ADJUDICATION_DISABLED")
            from concurrent.futures import ProcessPoolExecutor

            spec_dump = spec.model_dump(mode="json")
            tasks = [
                (
                    c.model_dump(mode="json"),
                    spec_dump,
                    run_id_final,
                    str(run_dir),
                    allow_synthetic,
                )
                for c in sorted(spec.strategies, key=lambda s: s.strategy_id)
            ]
            with ProcessPoolExecutor(max_workers=max_workers) as ex:
                futs = [ex.submit(_process_pool_run_single, t) for t in tasks]
                results = [fu.result() for fu in futs]
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futs = {
                    ex.submit(
                        run_single_strategy,
                        candidate=c,
                        batch=spec,
                        run_id=run_id_final,
                        run_dir=run_dir,
                        allow_synthetic=allow_synthetic,
                        adjudication_hook=adjudication_hook,
                    ): c.strategy_id
                    for c in spec.strategies
                }
                for fut in as_completed(futs):
                    results.append(fut.result())

    results.sort(key=lambda r: r.strategy_id)

    results, batch_ranking = apply_batch_ranking(results)

    portfolio = build_batch_portfolio_summary(
        batch_id=spec.batch_id, run_id=run_id_final, strategies=results
    )
    port_plain = portfolio.model_dump(mode="json")
    _write_json(
        run_dir / "portfolio_correlation_summary.json",
        {
            **port_plain,
            "portfolio_summary_evidence_sha256": portfolio.portfolio_summary_evidence_sha256,
        },
    )

    top_candidate: dict[str, Any] | None = None
    for row in batch_ranking:
        if row.get("blocked_tier"):
            continue
        sid = str(row["strategy_id"])
        match = next((s for s in results if s.strategy_id == sid), None)
        if match is not None and match.gate_summary.promotion_eligible:
            top_candidate = {
                "strategy_id": sid,
                "rank": row["rank"],
                "score": row.get("score"),
            }
            break

    promo_counts: dict[str, int] = {}
    ctr: Counter[str] = Counter()
    for r in results:
        for reason in r.gate_summary.promotion_blocked_reasons:
            key = reason.split(":", 1)[0] if ":" in reason else reason
            ctr[key] += 1
    promo_counts = dict(ctr)

    provider_rows: list[dict[str, str | None]] = []
    for r in results:
        if r.provider_snapshot_source_manifest_path:
            provider_rows.append(
                {
                    "strategy_id": r.strategy_id,
                    "provider_snapshot_source_manifest_path": r.provider_snapshot_source_manifest_path,
                    "provider_snapshot_manifest_sha256": r.provider_snapshot_manifest_sha256,
                }
            )
    if provider_rows:
        _write_json(
            run_dir / "batch_provider_historical_evidence.json",
            {
                "schema_version": "batch_provider_historical_evidence/v1",
                "batch_id": spec.batch_id,
                "run_id": run_id_final,
                "strategies": provider_rows,
            },
        )

    passed = sum(1 for r in results if r.status == StrategyRunStatus.PASSED)
    blocked = sum(1 for r in results if r.status == StrategyRunStatus.BLOCKED)
    paper = sum(1 for r in results if r.status == StrategyRunStatus.PAPER_ONLY)
    failed = sum(1 for r in results if r.status == StrategyRunStatus.FAILED)
    pending = len(spec.strategies) - len(results)

    summary = StrategyBatchRunSummary(
        ok=failed == 0 and pending == 0,
        batch_id=spec.batch_id,
        run_id=run_id_final,
        output_dir=str(run_dir),
        strategy_count=len(spec.strategies),
        passed_count=passed,
        blocked_count=blocked,
        paper_only_count=paper,
        failed_count=failed,
        pending_count=pending,
        strategies=results,
        batch_ranking=batch_ranking,
        portfolio_correlation_summary=port_plain,
        top_candidate=top_candidate,
        promotion_blocked_counts=promo_counts,
        manifest=manifest,
    )
    if any(r.status == StrategyRunStatus.FAILED for r in results):
        summary.ok = False
        summary.blockers.append("ONE_OR_MORE_STRATEGIES_FAILED")
    _write_json(run_dir / "batch_summary.json", summary.model_dump(mode="json"))
    return summary


__all__ = ["run_single_strategy", "run_strategy_batch"]
