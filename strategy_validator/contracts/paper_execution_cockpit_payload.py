"""Legacy facade for paper execution cockpit payload contracts."""
from __future__ import annotations

from strategy_validator.contracts import paper_execution_cockpit_payload_view, paper_execution_cockpit_summary
from strategy_validator.contracts.paper_execution_cockpit_payload_view import *
from strategy_validator.contracts.paper_execution_cockpit_summary import *

__all__ = (
    *paper_execution_cockpit_summary.__all__,
    *paper_execution_cockpit_payload_view.__all__,
)
