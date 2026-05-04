"""Bounded runtime registration for operator pack execution / approval / terminal commands."""
from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_operator_pack_execution_flow_runtime_commands import (
    OPERATOR_PACK_EXECUTION_FLOW_RUNNERS,
    register_oracle_operator_pack_execution_flow_runtime_commands,
)
from strategy_validator.cli.oracle_operator_pack_terminal_runtime_commands import (
    OPERATOR_PACK_TERMINAL_RUNNERS,
    register_oracle_operator_pack_terminal_runtime_commands,
)

OPERATOR_PACK_EXECUTION_RUNNERS = {
    **OPERATOR_PACK_EXECUTION_FLOW_RUNNERS,
    **OPERATOR_PACK_TERMINAL_RUNNERS,
}


def register_oracle_operator_pack_execution_runtime_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register bounded operator pack execution runtime commands."""
    register_oracle_operator_pack_execution_flow_runtime_commands(sub)
    register_oracle_operator_pack_terminal_runtime_commands(sub)
__all__ = [
    "OPERATOR_PACK_EXECUTION_RUNNERS",
    "register_oracle_operator_pack_execution_runtime_commands",
]
