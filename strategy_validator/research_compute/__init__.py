"""Optional advisory research compute helpers (CPU fallback, optional CUDA)."""

from strategy_validator.research_compute.gpu_probe import probe_gpu_capability
from strategy_validator.research_compute.monte_carlo import run_research_compute_demo

__all__ = ["probe_gpu_capability", "run_research_compute_demo"]
