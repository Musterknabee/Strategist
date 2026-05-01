"""Research compute contracts for optional CPU/CUDA acceleration (advisory-only)."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ComputeBackend(str, Enum):
    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"


class ComputeFallbackReason(str, Enum):
    NONE = "NONE"
    TORCH_NOT_INSTALLED = "TORCH_NOT_INSTALLED"
    CUDA_UNAVAILABLE = "CUDA_UNAVAILABLE"
    CUDA_BACKEND_ERROR = "CUDA_BACKEND_ERROR"
    REQUESTED_CPU = "REQUESTED_CPU"


class ComputeDeviceInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    backend: str = "cpu_numpy"
    gpu_available: bool = False
    torch_available: bool = False
    cuda_available: bool = False
    device_count: int = 0
    selected_device: str | None = None
    reason_unavailable: str | None = None
    devices: tuple[dict[str, object], ...] = ()


class ResearchComputeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    strategy_id: str | None = None
    research_task_id: str
    input_manifest_digest: str
    provider_evidence_digest: str
    pit_as_of_utc: str
    backend_requested: ComputeBackend = ComputeBackend.AUTO
    deterministic_seed: int = 7
    paths: int = Field(default=100_000, ge=1)
    steps: int = Field(default=252, ge=1)
    drift: float = 0.05
    volatility: float = 0.20
    horizon_years: float = 1.0


class ComputeEvidenceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest_version: str = "research_compute_evidence/v1"
    run_id: str
    research_task_id: str
    pit_as_of_utc: str
    backend_requested: ComputeBackend
    backend_used: ComputeBackend
    result_digest: str
    artifact_paths: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()


class ResearchComputeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "research_compute_result/v1"
    run_id: str
    strategy_id: str | None = None
    research_task_id: str
    input_manifest_digest: str
    provider_evidence_digest: str
    pit_as_of_utc: str
    backend_requested: ComputeBackend
    backend_used: ComputeBackend
    fallback_reason: ComputeFallbackReason = ComputeFallbackReason.NONE
    device_info: ComputeDeviceInfo
    deterministic_seed: int
    started_at_utc: str
    completed_at_utc: str
    duration_ms: int = Field(ge=0)
    mean_return: float
    std_return: float
    cvar_95: float
    max_drawdown_like: float
    result_digest: str
    artifact_paths: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()


__all__ = [
    "ComputeBackend",
    "ComputeDeviceInfo",
    "ComputeEvidenceManifest",
    "ComputeFallbackReason",
    "ResearchComputeRequest",
    "ResearchComputeResult",
]
