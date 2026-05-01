"""Optional GPU capability probe (torch/CUDA). Safe on CPU-only hosts."""
from __future__ import annotations

import importlib
from typing import Any


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
    }
    try:
        torch = importlib.import_module("torch")
    except Exception:
        payload["reason"] = "TORCH_NOT_INSTALLED"
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
