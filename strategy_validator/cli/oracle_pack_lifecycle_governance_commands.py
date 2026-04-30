from __future__ import annotations

import argparse

from strategy_validator.cli.command_registry import CommandSpec, register_commands
from strategy_validator.cli.oracle_pack_command_configs import (
    _configure_oracle_operator_pack_dispatch_outcome,
    _configure_oracle_operator_pack_dispatch_permission,
    _configure_oracle_operator_pack_handoff,
    _configure_oracle_operator_pack_lease_governance,
)


def register_oracle_pack_lifecycle_governance_commands(subparsers: argparse._SubParsersAction, *, runners: dict[str, object]) -> None:
    register_commands(
        subparsers,
        [
            CommandSpec('oracle-operator-pack-handoff', 'Render a structured operator pack handoff surface over assignment plus acknowledgement context', _configure_oracle_operator_pack_handoff, runners['oracle-operator-pack-handoff']),
            CommandSpec('oracle-operator-pack-lease-governance', 'Render a structured operator pack lease governance surface over claim lifecycle plus escalation context', _configure_oracle_operator_pack_lease_governance, runners['oracle-operator-pack-lease-governance']),
            CommandSpec('oracle-operator-pack-dispatch-permission', 'Render a structured operator pack dispatch-permission surface over execution readiness plus claim/lease context', _configure_oracle_operator_pack_dispatch_permission, runners['oracle-operator-pack-dispatch-permission']),
            CommandSpec('oracle-operator-pack-dispatch-outcome', 'Render a structured operator pack dispatch-outcome surface over dispatch permission plus lease-governance context', _configure_oracle_operator_pack_dispatch_outcome, runners['oracle-operator-pack-dispatch-outcome']),
        ],
    )


__all__ = ['register_oracle_pack_lifecycle_governance_commands']
