from __future__ import annotations

import argparse

from strategy_validator.cli.command_registry import CommandSpec, register_commands
from strategy_validator.cli.oracle_pack_command_configs import (
    _configure_oracle_operator_pack_terminal_archive,
    _configure_oracle_operator_pack_terminal_closure,
    _configure_oracle_operator_pack_terminal_record,
    _configure_oracle_operator_pack_terminal_record_publish,
    _configure_oracle_operator_pack_terminal_resolution,
)


def register_oracle_pack_terminal_commands(subparsers: argparse._SubParsersAction, *, runners: dict[str, object]) -> None:
    register_commands(
        subparsers,
        [
            CommandSpec('oracle-operator-pack-terminal-resolution', 'Render a structured operator pack terminal-resolution surface over execution finality plus approval disposition', _configure_oracle_operator_pack_terminal_resolution, runners['oracle-operator-pack-terminal-resolution']),
            CommandSpec('oracle-operator-pack-terminal-closure', 'Render a structured operator pack terminal-closure surface over terminal resolution plus claim lifecycle', _configure_oracle_operator_pack_terminal_closure, runners['oracle-operator-pack-terminal-closure']),
            CommandSpec('oracle-operator-pack-terminal-archive', 'Render a structured operator pack terminal-archive surface over terminal closure plus pack registry', _configure_oracle_operator_pack_terminal_archive, runners['oracle-operator-pack-terminal-archive']),
            CommandSpec('oracle-operator-pack-terminal-record', 'Render a structured operator pack terminal-record surface over terminal archive plus pack registry index', _configure_oracle_operator_pack_terminal_record, runners['oracle-operator-pack-terminal-record']),
            CommandSpec('oracle-operator-pack-terminal-record-publish', 'Publish a durable operator terminal-record bundle plus manifest/index', _configure_oracle_operator_pack_terminal_record_publish, runners['oracle-operator-pack-terminal-record-publish']),
        ],
    )


__all__ = ['register_oracle_pack_terminal_commands']
