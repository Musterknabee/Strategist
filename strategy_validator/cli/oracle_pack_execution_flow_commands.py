from __future__ import annotations

import argparse

from strategy_validator.cli.command_registry import CommandSpec, register_commands
from strategy_validator.cli.oracle_pack_command_configs import (
    _configure_oracle_operator_pack_approval_disposition,
    _configure_oracle_operator_pack_approval_needed,
    _configure_oracle_operator_pack_execution_authorization,
    _configure_oracle_operator_pack_execution_exception,
    _configure_oracle_operator_pack_execution_finality,
    _configure_oracle_operator_pack_execution_force,
    _configure_oracle_operator_pack_execution_readiness,
)


def register_oracle_pack_execution_flow_commands(subparsers: argparse._SubParsersAction, *, runners: dict[str, object]) -> None:
    register_commands(
        subparsers,
        [
            CommandSpec('oracle-operator-pack-execution-readiness', 'Render a structured operator pack execution readiness surface over lease governance plus handoff context', _configure_oracle_operator_pack_execution_readiness, runners['oracle-operator-pack-execution-readiness']),
            CommandSpec('oracle-operator-pack-execution-exception', 'Render a structured operator pack execution-exception surface over dispatch outcome plus lease-governance context', _configure_oracle_operator_pack_execution_exception, runners['oracle-operator-pack-execution-exception']),
            CommandSpec('oracle-operator-pack-approval-needed', 'Render a structured operator pack approval-needed surface over execution exception plus handoff context', _configure_oracle_operator_pack_approval_needed, runners['oracle-operator-pack-approval-needed']),
            CommandSpec('oracle-operator-pack-approval-disposition', 'Render a structured operator pack approval-disposition surface over approval-needed plus claim/lease context', _configure_oracle_operator_pack_approval_disposition, runners['oracle-operator-pack-approval-disposition']),
            CommandSpec('oracle-operator-pack-execution-authorization', 'Render a structured operator pack execution-authorization surface over approval disposition plus dispatch permission', _configure_oracle_operator_pack_execution_authorization, runners['oracle-operator-pack-execution-authorization']),
            CommandSpec('oracle-operator-pack-execution-force', 'Render a structured operator pack forced-execution surface over execution authorization plus execution exception', _configure_oracle_operator_pack_execution_force, runners['oracle-operator-pack-execution-force']),
            CommandSpec('oracle-operator-pack-execution-finality', 'Render a structured operator pack execution-finality surface over forced execution plus dispatch outcome', _configure_oracle_operator_pack_execution_finality, runners['oracle-operator-pack-execution-finality']),
        ],
    )


__all__ = ['register_oracle_pack_execution_flow_commands']
