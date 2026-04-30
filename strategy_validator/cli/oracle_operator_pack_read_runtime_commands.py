"""Bounded runtime registration for operator pack read/query commands."""
from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_operator_pack_read_dashboard_runtime_commands import (
    OPERATOR_PACK_READ_DASHBOARD_RUNNERS,
    register_oracle_operator_pack_read_dashboard_runtime_commands,
)
from strategy_validator.cli.oracle_operator_pack_read_query_runtime_commands import (
    OPERATOR_PACK_READ_QUERY_RUNNERS,
    register_oracle_operator_pack_read_query_runtime_commands,
)

OPERATOR_PACK_READ_RUNNERS = {
    **OPERATOR_PACK_READ_QUERY_RUNNERS,
    **OPERATOR_PACK_READ_DASHBOARD_RUNNERS,
}


def register_oracle_operator_pack_read_runtime_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register bounded operator pack read runtime commands."""
    register_oracle_operator_pack_read_query_runtime_commands(sub)
    register_oracle_operator_pack_read_dashboard_runtime_commands(sub)
__all__ = [
    "OPERATOR_PACK_READ_RUNNERS",
    "register_oracle_operator_pack_read_runtime_commands",
]
