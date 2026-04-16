from __future__ import annotations

from typing import Any

from strategy_validator.validator.orchestrator import adjudicate


def adjudicate_experiment(*args: Any, **kwargs: Any):
    """Service seam over the canonical adjudication bottleneck."""
    return adjudicate(*args, **kwargs)
