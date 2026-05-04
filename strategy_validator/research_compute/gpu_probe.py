"""Optional GPU capability probe (torch/CUDA). Safe on CPU-only hosts."""
from __future__ import annotations

import importlib
import os
import shutil
import subprocess
from typing import Any


def _probe_nvidia_smi() -> dict[str, Any]:
    if shutil.which("nvidia-smi") is None:
        return {
            "gpu_hardware_detected": False,
            "nvidia_smi_available": False,
        }
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except Exception as exc:  # pragma: no cover - defensive host probe
        return {
            "gpu_hardware_detected": False,
            "nvidia_smi_available": True,
            "nvidia_smi_error": exc.__class__.__name__,
        }
    if completed.returncode != 0:
        return {
            "gpu_hardware_detected": False,
            "nvidia_smi_available": True,
            "nvidia_smi_error": (completed.stderr or completed.stdout or "").strip()[:240],
        }
    devices: list[dict[str, Any]] = []
    for index, line in enumerate(completed.stdout.splitlines()):
        parts = [part.strip() for part in line.split(",")]
        if not parts or not parts[0]:
            continue
        row: dict[str, Any] = {"index": index, "name": parts[0]}
        if len(parts) > 1:
            try:
                row["memory_total_mib"] = int(parts[1])
            except ValueError:
                row["memory_total_mib"] = parts[1]
        if len(parts) > 2:
            row["driver_version"] = parts[2]
        devices.append(row)
    return {
        "gpu_hardware_detected": bool(devices),
        "nvidia_smi_available": True,
        "nvidia_smi_devices": devices,
    }


def probe_gpu_capability() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": True,
        "backend": "cpu",
        "gpu_available": False,
        "torch_available": False,
        "cuda_available": False,
        "device_count": 0,
        "selected_device": "cpu",
        "devices": [],
        "fallback_status": "GPU_UNAVAILABLE_CPU_FALLBACK",
    }
    payload.update(_probe_nvidia_smi())
    deep_probe = (os.environ.get("STRATEGY_VALIDATOR_RESEARCH_COMPUTE_DEEP_PROBE_ENABLE", "").strip().lower() in {"1", "true", "yes"})
    if not deep_probe:
        payload["reason"] = "TORCH_DEEP_PROBE_DISABLED"
        payload["fallback_status"] = "GPU_UNAVAILABLE_CPU_FALLBACK"
        return payload
    try:
        torch = importlib.import_module("torch")
    except Exception:
        payload["reason"] = "GPU_UNAVAILABLE_CPU_FALLBACK"
        payload["fallback_status"] = "GPU_UNAVAILABLE_CPU_FALLBACK"
        return payload

    payload["torch_available"] = True
    payload["backend"] = "torch_cpu"
    cuda_mod = getattr(torch, "cuda", None)
    if cuda_mod is None:
        payload["reason"] = "CUDA_MODULE_MISSING"
        return payload

    try:
        cuda_available = bool(cuda_mod.is_available())
    except Exception as exc:  # pragma: no cover - defensive
        payload["reason"] = f"CUDA_PROBE_ERROR:{exc.__class__.__name__}"
        return payload

    payload["cuda_available"] = cuda_available
    if not cuda_available:
        payload["reason"] = "CUDA_UNAVAILABLE"
        return payload

    payload["backend"] = "torch_cuda"
    payload["gpu_available"] = True
    payload["selected_device"] = "cuda:0"

    try:
        payload["cuda_version"] = getattr(torch.version, "cuda", None)
    except Exception:
        payload["cuda_version"] = None

    try:
        device_count = int(cuda_mod.device_count())
    except Exception:
        device_count = 0
    payload["device_count"] = device_count

    devices: list[dict[str, Any]] = []
    for i in range(device_count):
        row: dict[str, Any] = {"index": i}
        try:
            row["name"] = str(cuda_mod.get_device_name(i))
        except Exception:
            row["name"] = "unknown"
        try:
            free_b, total_b = cuda_mod.mem_get_info(i)
            row["memory_free_bytes"] = int(free_b)
            row["memory_total_bytes"] = int(total_b)
        except Exception:
            # mem_get_info may be unsupported on some drivers; keep probe non-fatal.
            pass
        devices.append(row)
    payload["devices"] = devices
    return payload


__all__ = ["probe_gpu_capability"]
