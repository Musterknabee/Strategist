"""Custody command-family dispatcher for the paper broker CLI.

The custody lifecycle spans multiple evidence-chain phases. This module keeps
that family as one public handler while delegating the large phase-specific
command bodies to smaller import-light support modules.
"""
from __future__ import annotations

from typing import Any

from strategy_validator.cli_support import (
    paper_broker_custody_archive_commands,
    paper_broker_custody_chain_commands,
    paper_broker_custody_renewal_commands,
)

_CUSTODY_PHASE_HANDLERS = (
    paper_broker_custody_chain_commands,
    paper_broker_custody_renewal_commands,
    paper_broker_custody_archive_commands,
)


def handle(ns: Any, env: dict[str, str]) -> int | None:
    from strategy_validator.cli import paper_broker as _paper_broker

    for command_family in _CUSTODY_PHASE_HANDLERS:
        result = command_family.handle(ns, env)
        if result is not None:
            return result
    return None
