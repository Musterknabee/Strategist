from __future__ import annotations
from typing import Any
def adjudicate_experiment(*args: Any, **kwargs: Any):
    from strategy_validator.validator.orchestrator import adjudicate
    return adjudicate(*args, **kwargs)
__all__=["adjudicate_experiment"]
