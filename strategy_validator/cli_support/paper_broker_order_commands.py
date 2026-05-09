"""Order command-family dispatcher for the paper broker CLI.

The public handler remains stable for the top-level dispatcher while the
phase-specific command bodies live in smaller support modules.
"""
from __future__ import annotations

from typing import Any

from strategy_validator.cli_support import (
    paper_broker_order_read_commands,
    paper_broker_order_lifecycle_commands,
)

_PHASE_HANDLERS = (
    paper_broker_order_read_commands,
    paper_broker_order_lifecycle_commands,
)


def handle(ns: Any, env: dict[str, str]) -> int | None:
    from strategy_validator.cli import paper_broker as _paper_broker

    for command_family in _PHASE_HANDLERS:
        result = command_family.handle(ns, env)
        if result is not None:
            return result
    return None
