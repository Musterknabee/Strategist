from __future__ import annotations

import types

from strategy_validator.research_compute.gpu_probe import probe_gpu_capability


def test_gpu_probe_torch_missing(monkeypatch) -> None:
    import importlib

    def _boom(_name: str):
        raise ModuleNotFoundError("torch")

    monkeypatch.setattr(importlib, "import_module", _boom)
    payload = probe_gpu_capability()
    assert payload["ok"] is True
    assert payload["gpu_available"] is False
    assert payload["reason"] == "TORCH_NOT_INSTALLED"


def test_gpu_probe_torch_cpu_only(monkeypatch) -> None:
    import importlib

    fake_torch = types.SimpleNamespace(
        cuda=types.SimpleNamespace(is_available=lambda: False),
        version=types.SimpleNamespace(cuda=None),
    )
    monkeypatch.setattr(importlib, "import_module", lambda _name: fake_torch)
    payload = probe_gpu_capability()
    assert payload["torch_available"] is True
    assert payload["cuda_available"] is False
    assert payload["gpu_available"] is False
    assert payload["reason"] == "CUDA_UNAVAILABLE"


def test_gpu_probe_cuda_available(monkeypatch) -> None:
    import importlib

    class FakeCuda:
        @staticmethod
        def is_available() -> bool:
            return True

        @staticmethod
        def device_count() -> int:
            return 1

        @staticmethod
        def get_device_name(_index: int) -> str:
            return "Mock GPU"

        @staticmethod
        def mem_get_info(_index: int) -> tuple[int, int]:
            return 1_000_000, 2_000_000

    fake_torch = types.SimpleNamespace(
        cuda=FakeCuda(),
        version=types.SimpleNamespace(cuda="12.1"),
    )
    monkeypatch.setattr(importlib, "import_module", lambda _name: fake_torch)
    payload = probe_gpu_capability()
    assert payload["gpu_available"] is True
    assert payload["backend"] == "torch_cuda"
    assert payload["device_count"] == 1
    assert payload["devices"][0]["name"] == "Mock GPU"
