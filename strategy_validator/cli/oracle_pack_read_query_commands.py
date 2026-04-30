from __future__ import annotations

import argparse

from strategy_validator.cli.command_registry import CommandSpec, register_commands
from strategy_validator.cli.oracle_pack_command_configs import (
    _configure_oracle_operator_pack_navigation,
    _configure_oracle_operator_pack_query,
    _configure_oracle_operator_pack_workbench,
)


def register_oracle_pack_read_query_commands(subparsers: argparse._SubParsersAction, *, runners: dict[str, object]) -> None:
    register_commands(
        subparsers,
        [
            CommandSpec('oracle-operator-pack-query', 'Query the shared operator pack index for discoverable operator packs', _configure_oracle_operator_pack_query, runners['oracle-operator-pack-query']),
            CommandSpec('oracle-operator-pack-workbench', 'Render a structured operator workbench over the shared operator pack index', _configure_oracle_operator_pack_workbench, runners['oracle-operator-pack-workbench']),
            CommandSpec('oracle-operator-pack-navigation', 'Select latest relevant operator packs from the shared workbench/index', _configure_oracle_operator_pack_navigation, runners['oracle-operator-pack-navigation']),
        ],
    )


__all__ = ['register_oracle_pack_read_query_commands']
