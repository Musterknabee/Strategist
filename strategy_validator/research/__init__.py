"""Research-plane execution helpers (paper/research; not live trading).

Keep package import side effects minimal.  Several read-plane modules import small
helpers from ``strategy_validator.research`` submodules; importing the full batch
runner at package import time pulls in the entire quant stack and can make simple
status routes slow or fragile.  Expose ``run_strategy_batch`` lazily instead.
"""
from __future__ import annotations

from typing import Any


def run_strategy_batch(*args: Any, **kwargs: Any) -> Any:
    from strategy_validator.research.strategy_batch_runner import run_strategy_batch as _run_strategy_batch

    return _run_strategy_batch(*args, **kwargs)


__all__ = ["run_strategy_batch"]
