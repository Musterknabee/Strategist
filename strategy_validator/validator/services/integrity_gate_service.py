from __future__ import annotations

from strategy_validator.validator.readiness import perform_readiness_check


def get_current_readiness():
    """Service seam over runtime integrity/readiness gates."""
    return perform_readiness_check()
