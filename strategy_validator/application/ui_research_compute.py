"""Read-plane summary payload for optional research compute acceleration."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.research_compute.gpu_probe import probe_gpu_capability


def _artifact_root() -> Path:
    raw = os.environ.get("STRATEGY_VALIDATOR_ARTIFACT_ROOT", "").strip()
    if raw:
        return Path(raw)
    return Path.cwd() / "artifacts"


def _read_last_benchmark() -> dict[str, Any] | None:
    p = _artifact_root() / "research_compute" / "benchmark.json"
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    data["_artifact_path"] = str(p.as_posix())
    return data


def build_ui_research_compute_payload() -> dict[str, Any]:
    probe = probe_gpu_capability()
    benchmark = _read_last_benchmark()
    gpu_available = bool(probe.get("gpu_available"))
    readiness = "GPU_ACCELERATION_READY" if gpu_available else "CPU_FALLBACK_READY"
    fallback_reason = probe.get("reason")
    if not gpu_available and fallback_reason is None:
        fallback_reason = "CUDA_UNAVAILABLE"
    return {
        "schema_version": "ui_research_compute/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_plane_only": True,
        "advisory_only": True,
        "gpu_probe": probe,
        "last_benchmark": benchmark,
        "gpu_available": gpu_available,
        "cpu_fallback_status": "READY" if not gpu_available else "NOT_APPLICABLE",
        "fallback_reason": fallback_reason,
        "research_compute_readiness": readiness,
    }


__all__ = ["build_ui_research_compute_payload"]
