"""Advisory research compute demo worker with CPU fallback and optional torch CUDA."""
from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from strategy_validator.contracts.research_compute import (
    ComputeBackend,
    ComputeDeviceInfo,
    ComputeEvidenceManifest,
    ComputeFallbackReason,
    ResearchComputeRequest,
    ResearchComputeResult,
)
from strategy_validator.research_compute.gpu_probe import probe_gpu_capability


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_json(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _artifact_root() -> Path:
    raw = os.environ.get("STRATEGY_VALIDATOR_ARTIFACT_ROOT", "").strip()
    if raw:
        return Path(raw)
    return Path.cwd() / "artifacts"


def _compute_with_numpy(req: ResearchComputeRequest) -> dict[str, float]:
    rng = np.random.default_rng(req.deterministic_seed)
    dt = req.horizon_years / float(req.steps)
    drift_term = (req.drift - 0.5 * req.volatility ** 2) * dt
    shock_scale = req.volatility * np.sqrt(dt)
    shocks = rng.normal(loc=drift_term, scale=shock_scale, size=(req.paths, req.steps))
    log_paths = np.cumsum(shocks, axis=1)
    terminal = np.exp(log_paths[:, -1]) - 1.0
    pnl = terminal.astype(np.float64)
    mean = float(np.mean(pnl))
    std = float(np.std(pnl))
    q05 = float(np.quantile(pnl, 0.05))
    cvar = float(np.mean(pnl[pnl <= q05])) if np.any(pnl <= q05) else q05
    path_prices = np.exp(log_paths)
    rolling_peak = np.maximum.accumulate(path_prices, axis=1)
    drawdowns = (path_prices / rolling_peak) - 1.0
    max_dd_like = float(np.min(drawdowns))
    return {
        "mean_return": mean,
        "std_return": std,
        "cvar_95": cvar,
        "max_drawdown_like": max_dd_like,
    }


def _compute_with_torch(req: ResearchComputeRequest, *, use_cuda: bool) -> dict[str, float]:
    # Lazy import to keep backend boot GPU-optional.
    import torch  # type: ignore

    device = torch.device("cuda:0" if use_cuda else "cpu")
    gen = torch.Generator(device=device if use_cuda else "cpu")
    gen.manual_seed(int(req.deterministic_seed))
    dt = req.horizon_years / float(req.steps)
    drift_term = (req.drift - 0.5 * req.volatility ** 2) * dt
    shock_scale = req.volatility * float(np.sqrt(dt))
    shocks = torch.normal(
        mean=float(drift_term),
        std=float(shock_scale),
        size=(req.paths, req.steps),
        generator=gen,
        device=device,
    )
    log_paths = torch.cumsum(shocks, dim=1)
    terminal = torch.exp(log_paths[:, -1]) - 1.0
    mean = float(torch.mean(terminal).item())
    std = float(torch.std(terminal, unbiased=False).item())
    q05 = float(torch.quantile(terminal, 0.05).item())
    cvar = float(torch.mean(terminal[terminal <= q05]).item()) if bool(torch.any(terminal <= q05)) else q05
    prices = torch.exp(log_paths)
    peak = torch.cummax(prices, dim=1).values
    drawdowns = (prices / peak) - 1.0
    max_dd_like = float(torch.min(drawdowns).item())
    return {
        "mean_return": mean,
        "std_return": std,
        "cvar_95": cvar,
        "max_drawdown_like": max_dd_like,
    }


def _choose_backend(req: ResearchComputeRequest, probe: dict[str, Any]) -> tuple[ComputeBackend, ComputeFallbackReason]:
    if req.backend_requested == ComputeBackend.CPU:
        return ComputeBackend.CPU, ComputeFallbackReason.REQUESTED_CPU
    if req.backend_requested == ComputeBackend.CUDA:
        if probe.get("gpu_available"):
            return ComputeBackend.CUDA, ComputeFallbackReason.NONE
        if not probe.get("torch_available"):
            return ComputeBackend.CPU, ComputeFallbackReason.TORCH_NOT_INSTALLED
        return ComputeBackend.CPU, ComputeFallbackReason.CUDA_UNAVAILABLE
    # AUTO
    if probe.get("gpu_available"):
        return ComputeBackend.CUDA, ComputeFallbackReason.NONE
    if not probe.get("torch_available"):
        return ComputeBackend.CPU, ComputeFallbackReason.TORCH_NOT_INSTALLED
    return ComputeBackend.CPU, ComputeFallbackReason.CUDA_UNAVAILABLE


def run_research_compute_demo(req: ResearchComputeRequest) -> ResearchComputeResult:
    started = _utc_now()
    t0 = time.perf_counter()
    probe = probe_gpu_capability()
    backend_used, fallback = _choose_backend(req, probe)
    warnings: list[str] = []
    blockers: list[str] = []
    stats: dict[str, float]

    if backend_used == ComputeBackend.CUDA:
        try:
            stats = _compute_with_torch(req, use_cuda=True)
        except Exception as exc:
            warnings.append(f"cuda_backend_error:{exc.__class__.__name__}")
            fallback = ComputeFallbackReason.CUDA_BACKEND_ERROR
            backend_used = ComputeBackend.CPU
            stats = _compute_with_numpy(req)
    elif backend_used == ComputeBackend.CPU and probe.get("torch_available"):
        stats = _compute_with_torch(req, use_cuda=False)
    else:
        stats = _compute_with_numpy(req)

    completed = _utc_now()
    duration_ms = int(round((time.perf_counter() - t0) * 1000.0))

    device_info = ComputeDeviceInfo(
        backend="torch_cuda" if backend_used == ComputeBackend.CUDA else ("torch_cpu" if probe.get("torch_available") else "cpu_numpy"),
        gpu_available=bool(probe.get("gpu_available")),
        torch_available=bool(probe.get("torch_available")),
        cuda_available=bool(probe.get("cuda_available")),
        device_count=int(probe.get("device_count", 0) or 0),
        selected_device=str(probe.get("selected_device")) if probe.get("selected_device") is not None else None,
        reason_unavailable=str(probe.get("reason")) if probe.get("reason") is not None else None,
        devices=tuple(probe.get("devices", [])),
    )

    result_payload = {
        "run_id": req.run_id,
        "research_task_id": req.research_task_id,
        "pit_as_of_utc": req.pit_as_of_utc,
        "backend_requested": req.backend_requested.value,
        "backend_used": backend_used.value,
        "deterministic_seed": req.deterministic_seed,
        "stats": stats,
    }
    result_digest = _sha256_json(result_payload)

    artifact_dir = _artifact_root() / "research_compute"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    result_path = artifact_dir / f"{req.run_id}.result.json"
    evidence_path = artifact_dir / f"{req.run_id}.evidence.json"

    result = ResearchComputeResult(
        run_id=req.run_id,
        strategy_id=req.strategy_id,
        research_task_id=req.research_task_id,
        input_manifest_digest=req.input_manifest_digest,
        provider_evidence_digest=req.provider_evidence_digest,
        pit_as_of_utc=req.pit_as_of_utc,
        backend_requested=req.backend_requested,
        backend_used=backend_used,
        fallback_reason=fallback,
        device_info=device_info,
        deterministic_seed=req.deterministic_seed,
        started_at_utc=started,
        completed_at_utc=completed,
        duration_ms=duration_ms,
        mean_return=stats["mean_return"],
        std_return=stats["std_return"],
        cvar_95=stats["cvar_95"],
        max_drawdown_like=stats["max_drawdown_like"],
        result_digest=result_digest,
        artifact_paths=(str(result_path.as_posix()), str(evidence_path.as_posix())),
        warnings=tuple(warnings),
        blockers=tuple(blockers),
    )
    manifest = ComputeEvidenceManifest(
        run_id=req.run_id,
        research_task_id=req.research_task_id,
        pit_as_of_utc=req.pit_as_of_utc,
        backend_requested=req.backend_requested,
        backend_used=backend_used,
        result_digest=result_digest,
        artifact_paths=result.artifact_paths,
        warnings=result.warnings,
        blockers=result.blockers,
    )

    result_path.write_text(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    evidence_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


__all__ = ["run_research_compute_demo"]
