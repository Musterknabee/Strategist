from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_pack_read_dashboard_commands import register_oracle_pack_read_dashboard_commands
from strategy_validator.cli.oracle_pack_read_query_commands import register_oracle_pack_read_query_commands


def register_oracle_pack_read_commands(subparsers: argparse._SubParsersAction, *, runners: dict[str, object]) -> None:
    register_oracle_pack_read_query_commands(subparsers, runners=runners)
    register_oracle_pack_read_dashboard_commands(subparsers, runners=runners)


__all__ = ['register_oracle_pack_read_commands']
