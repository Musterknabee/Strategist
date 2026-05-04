from __future__ import annotations
from strategy_validator.validator.readiness import perform_readiness_check
def get_current_readiness():
    return perform_readiness_check()
__all__=["get_current_readiness"]
