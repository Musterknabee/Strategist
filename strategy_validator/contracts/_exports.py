"""Grouped lazy export map for the contracts package."""
from __future__ import annotations

from strategy_validator.contracts._exports_foundation import EXPORTS_FOUNDATION
from strategy_validator.contracts._exports_operational_runtime import EXPORTS_OPERATIONAL_RUNTIME
from strategy_validator.contracts._exports_operator_ui import EXPORTS_OPERATOR_UI
from strategy_validator.contracts._exports_research_strategy import EXPORTS_RESEARCH_STRATEGY

_EXPORT_MAP = {
    **EXPORTS_FOUNDATION,
    **EXPORTS_OPERATOR_UI,
    **EXPORTS_OPERATIONAL_RUNTIME,
    **EXPORTS_RESEARCH_STRATEGY,
}
