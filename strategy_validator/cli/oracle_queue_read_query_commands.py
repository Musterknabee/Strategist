from __future__ import annotations

import argparse

from strategy_validator.cli.command_registry import CommandSpec, register_commands
from strategy_validator.cli.oracle_queue_command_configs import (
    _configure_oracle_operator_queue_query,
    _configure_oracle_operator_workboard_query,
)


def register_oracle_queue_read_query_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    runners: dict[str, object],
) -> None:
    register_commands(
        subparsers,
        [
            CommandSpec(
                'oracle-operator-queue-query',
                'Inspect the typed operator queue/work-item surface from governance policy inputs',
                _configure_oracle_operator_queue_query,
                runners['oracle-operator-queue-query'],
            ),
            CommandSpec(
                'oracle-operator-workboard-query',
                'Inspect the typed operator workboard surface from governance policy inputs',
                _configure_oracle_operator_workboard_query,
                runners['oracle-operator-workboard-query'],
            ),
        ],
    )


__all__ = ['register_oracle_queue_read_query_commands']
