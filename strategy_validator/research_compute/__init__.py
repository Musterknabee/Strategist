"""Optional advisory research compute helpers (CPU fallback, optional CUDA).

Keep package import side effects minimal.  Importing this package should not pull
in torch/Monte-Carlo dependencies just to render a read-plane status route.
"""
from __future__ import annotations

from typing import Any


def probe_gpu_capability() -> dict[str, Any]:
    from strategy_validator.research_compute.gpu_probe import probe_gpu_capability as _probe_gpu_capability

    return _probe_gpu_capability()


def run_research_compute_demo(*args: Any, **kwargs: Any) -> Any:
    from strategy_validator.research_compute.monte_carlo import run_research_compute_demo as _run_research_compute_demo

    return _run_research_compute_demo(*args, **kwargs)


__all__ = ["probe_gpu_capability", "run_research_compute_demo"]
