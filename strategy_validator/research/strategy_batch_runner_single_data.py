"""Data loading and PIT gate resolution for a single strategy run."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from strategy_validator.contracts.strategy_batch import (
    PitPolicy,
    StrategyBatchSpec,
    StrategyCandidateSpec,
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
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from strategy_validator.research.strategy_batch_evaluators import deterministic_prices
from strategy_validator.research.strategy_batch_runner_common import (
    _write_filtered_bars_csv,
    _write_json,
)
from strategy_validator.research.strategy_data_loader import (
    StrategyDataLoadError,
    load_local_bars_snapshot,
    load_provider_snapshot_bars,
)


@dataclass(frozen=True)
class StrategySingleDataContext:
    """Resolved bar arrays, manifests, and PIT metadata for one strategy run."""

    local_snap: Any | None
    loaded_bars: list[Any] | None
    load_warnings: list[str]
    prices: np.ndarray
    opens: np.ndarray
    highs: np.ndarray
    lows: np.ndarray
    volumes: np.ndarray
    used_synthetic: bool
    data_snapshot_path: Path | None
    data_snapshot_sha: str | None
    bars_row_count: int | None
    provider_snap: Any | None
    provider_snapshot_source_manifest_path: str | None
    pit_sha: str


@dataclass(frozen=True)
class StrategySingleDataResolution:
    """Outcome of data-plane resolution: either a context or a blocked result."""

    context: StrategySingleDataContext | None
    blocked_result: StrategyRunResult | None = None


def _bar_arrays(bars: list[Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    return (
        np.array([b.close for b in bars], dtype=np.float64),
        np.array([b.open for b in bars], dtype=np.float64),
        np.array([b.high for b in bars], dtype=np.float64),
        np.array([b.low for b in bars], dtype=np.float64),
        np.array([b.volume for b in bars], dtype=np.float64),
    )


def _blocked_result(
    *,
    candidate: StrategyCandidateSpec,
    started: datetime,
    gate: StrategyGateSummary,
    pit_status: str,
    data_status: str,
    data_plane: str | None = None,
    blockers: list[str] | None = None,
    warnings: list[str] | None = None,
    pit_snapshot_status: str | None = None,
    data_snapshot_path: Path | None = None,
    data_snapshot_sha: str | None = None,
    data_snapshot_digest: str | None = None,
    bars_row_count: int | None = None,
) -> StrategyRunResult:
    completed = datetime.now(timezone.utc)
    dur = int((completed - started).total_seconds() * 1000)
    return StrategyRunResult(
        strategy_id=candidate.strategy_id,
        status=StrategyRunStatus.BLOCKED,
        started_at_utc=started,
        completed_at_utc=completed,
        duration_ms=dur,
        pit_status=pit_status,
        pit_snapshot_status=pit_snapshot_status,
        data_status=data_status,
        data_plane=data_plane,
        blockers=list(blockers or []),
        warnings=list(warnings or []),
        gate_summary=gate,
        data_snapshot_manifest_path=str(data_snapshot_path.resolve()) if data_snapshot_path else None,
        data_snapshot_manifest_sha256=data_snapshot_sha,
        data_snapshot_digest=data_snapshot_digest,
        bars_row_count=bars_row_count,
        compute_backend="cpu",
        compute_worker_model="thread_pool",
        cuda_available=False,
    )


def _write_data_snapshot_manifest(
    *,
    strat_dir: Path,
    candidate: StrategyCandidateSpec,
    batch: StrategyBatchSpec,
    run_id: str,
    local_snap: Any,
    extra: dict[str, Any],
) -> tuple[Path, str]:
    dsm = StrategyDataSnapshotManifest(
        strategy_id=candidate.strategy_id,
        batch_id=batch.batch_id,
        run_id=run_id,
        snapshot=local_snap,
        compute_backend="cpu",
        extra=extra,
    )
    dsm_body = dsm.model_dump(mode="json")
    data_snapshot_sha = canonical_json_sha256(dsm_body)
    data_snapshot_path = strat_dir / "data_snapshot_manifest.json"
    _write_json(
        data_snapshot_path,
        {**dsm_body, "data_snapshot_manifest_sha256": data_snapshot_sha},
    )
    return data_snapshot_path, data_snapshot_sha


def resolve_single_strategy_data(
    *,
    candidate: StrategyCandidateSpec,
    batch: StrategyBatchSpec,
    run_id: str,
    strat_dir: Path,
    repo_root: Path,
    started: datetime,
    gate: StrategyGateSummary,
    allow_synthetic: bool,
    deterministic_prices_fn: Any | None = None,
) -> StrategySingleDataResolution:
    """Resolve data inputs and enforce the early PIT/data gates for one strategy."""

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
            prices, opens, highs, lows, volumes = _bar_arrays(loaded_bars)
            bars_row_count = len(loaded_bars)
            _write_filtered_bars_csv(strat_dir / "filtered_bars.csv", loaded_bars)
            data_snapshot_path, data_snapshot_sha = _write_data_snapshot_manifest(
                strat_dir=strat_dir,
                candidate=candidate,
                batch=batch,
                run_id=run_id,
                local_snap=local_snap,
                extra={"max_workers_declared": batch.max_workers, "worker_model": batch.worker_model},
            )
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
            prices, opens, highs, lows, volumes = _bar_arrays(loaded_bars)
            bars_row_count = len(loaded_bars)
            _write_filtered_bars_csv(strat_dir / "filtered_bars.csv", loaded_bars)
            if isinstance(candidate.data_source, ProviderSnapshotDataSourceConfig):
                provider_snapshot_source_manifest_path = candidate.data_source.manifest_path
            data_snapshot_path, data_snapshot_sha = _write_data_snapshot_manifest(
                strat_dir=strat_dir,
                candidate=candidate,
                batch=batch,
                run_id=run_id,
                local_snap=local_snap,
                extra={
                    "max_workers_declared": batch.max_workers,
                    "worker_model": batch.worker_model,
                    "provider_snapshot_manifest_sha256": provider_snap.manifest_sha256,
                    "provider_snapshot_manifest_spec_path": candidate.data_source.manifest_path,
                },
            )
        except StrategyDataLoadError as exc:
            load_warnings = [f"PROVIDER_SNAPSHOT_LOAD:{b}" for b in exc.blockers]

    if prices is None:
        if candidate.data_source is not None and candidate.data_source.kind == "provider_snapshot":
            gate.data_gate = "PROVIDER_SNAPSHOT_LOAD_FAILED"
            gate.pit_gate = "BLOCKED"
            blk = load_warnings or ["PROVIDER_SNAPSHOT_LOAD_FAILED"]
            return StrategySingleDataResolution(
                context=None,
                blocked_result=_blocked_result(
                    candidate=candidate,
                    started=started,
                    gate=gate,
                    pit_status="BLOCKED",
                    pit_snapshot_status=None,
                    data_status="PROVIDER_SNAPSHOT",
                    data_plane="NO_BARS",
                    blockers=list(dict.fromkeys(blk)),
                ),
            )
        if batch.pit_policy == PitPolicy.STRICT:
            gate.pit_gate = "BLOCKED_STRICT_NO_VERIFIED_DATA"
            gate.data_gate = "MISSING_LOCAL_BARS"
            return StrategySingleDataResolution(
                context=None,
                blocked_result=_blocked_result(
                    candidate=candidate,
                    started=started,
                    gate=gate,
                    pit_status="BLOCKED",
                    pit_snapshot_status=None,
                    data_status="MISSING_PIT",
                    data_plane="NO_BARS",
                    blockers=["STRICT_REQUIRES_LOCAL_PIT_VERIFIED_BARS", *load_warnings],
                    warnings=["PIT_STRICT_BLOCKED"],
                ),
            )
        if not allow_synthetic:
            gate.data_gate = "BLOCKED_NO_SYNTHETIC"
            gate.pit_gate = "BLOCKED"
            return StrategySingleDataResolution(
                context=None,
                blocked_result=_blocked_result(
                    candidate=candidate,
                    started=started,
                    gate=gate,
                    pit_status="BLOCKED",
                    data_status="NO_DATA",
                    data_plane="EMPTY",
                    blockers=["NO_SYNTHETIC_DATA_PATH", *load_warnings],
                ),
            )
        seed = f"{batch.batch_id}|{run_id}|{candidate.strategy_id}|{candidate.as_of_utc.isoformat()}"
        n = max(32, min(512, candidate.lookback_days))
        prices = (deterministic_prices_fn or deterministic_prices)(seed=seed, n=n)
        opens = prices.copy()
        highs = prices * 1.002
        lows = prices * 0.998
        volumes = np.ones_like(prices, dtype=np.float64) * 1000.0
        used_synthetic = True

    if batch.pit_policy == PitPolicy.STRICT and used_synthetic:
        gate.pit_gate = "BLOCKED_STRICT_SYNTHETIC"
        gate.data_gate = "SYNTHETIC_NOT_ALLOWED_UNDER_STRICT"
        return StrategySingleDataResolution(
            context=None,
            blocked_result=_blocked_result(
                candidate=candidate,
                started=started,
                gate=gate,
                pit_status="BLOCKED",
                data_status="SYNTHETIC_DEMO",
                data_plane="SYNTHETIC",
                blockers=["STRICT_SYNTHETIC_FORBIDDEN"],
                warnings=["PIT_STRICT_BLOCKED"],
            ),
        )

    if (
        batch.pit_policy == PitPolicy.STRICT
        and local_snap is not None
        and local_snap.pit_status != StrategyPitSnapshotStatus.PIT_VERIFIED
    ):
        gate.pit_gate = f"BLOCKED_{local_snap.pit_status.value}"
        gate.data_gate = "LOCAL_BARS_NOT_VERIFIED"
        return StrategySingleDataResolution(
            context=None,
            blocked_result=_blocked_result(
                candidate=candidate,
                started=started,
                gate=gate,
                pit_status="BLOCKED",
                pit_snapshot_status=local_snap.pit_status.value,
                data_status="PIT_NOT_VERIFIED",
                data_plane="REAL_LOCAL",
                blockers=["STRICT_REQUIRES_PIT_VERIFIED_SNAPSHOT"],
                warnings=load_warnings,
                data_snapshot_path=data_snapshot_path,
                data_snapshot_sha=data_snapshot_sha,
                data_snapshot_digest=local_snap.bars_sha256,
                bars_row_count=bars_row_count,
            ),
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

    assert prices is not None
    assert opens is not None
    assert highs is not None
    assert lows is not None
    assert volumes is not None
    return StrategySingleDataResolution(
        context=StrategySingleDataContext(
            local_snap=local_snap,
            loaded_bars=loaded_bars,
            load_warnings=load_warnings,
            prices=prices,
            opens=opens,
            highs=highs,
            lows=lows,
            volumes=volumes,
            used_synthetic=used_synthetic,
            data_snapshot_path=data_snapshot_path,
            data_snapshot_sha=data_snapshot_sha,
            bars_row_count=bars_row_count,
            provider_snap=provider_snap,
            provider_snapshot_source_manifest_path=provider_snapshot_source_manifest_path,
            pit_sha=pit_sha,
        )
    )


__all__ = [
    "StrategySingleDataContext",
    "StrategySingleDataResolution",
    "resolve_single_strategy_data",
]
