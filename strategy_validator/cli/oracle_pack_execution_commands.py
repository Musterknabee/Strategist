from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_pack_execution_flow_commands import register_oracle_pack_execution_flow_commands
from strategy_validator.cli.oracle_pack_terminal_commands import register_oracle_pack_terminal_commands


def register_oracle_pack_execution_commands(subparsers: argparse._SubParsersAction, *, runners: dict[str, object]) -> None:
    register_oracle_pack_execution_flow_commands(subparsers, runners=runners)
    register_oracle_pack_terminal_commands(subparsers, runners=runners)


__all__ = ['register_oracle_pack_execution_commands']
