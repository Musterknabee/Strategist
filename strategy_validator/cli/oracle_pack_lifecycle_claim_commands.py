from __future__ import annotations

import argparse

from strategy_validator.cli.command_registry import CommandSpec, register_commands
from strategy_validator.cli.oracle_pack_command_configs import (
    _configure_oracle_operator_pack_assignment,
    _configure_oracle_operator_pack_claim_lease,
    _configure_oracle_operator_pack_claim_lifecycle,
    _configure_oracle_operator_pack_claim_operability,
    _configure_oracle_operator_pack_escalation,
)


def register_oracle_pack_lifecycle_claim_commands(subparsers: argparse._SubParsersAction, *, runners: dict[str, object]) -> None:
    register_commands(
        subparsers,
        [
            CommandSpec('oracle-operator-pack-escalation', 'Render a structured operator pack escalation surface over drift plus operator routing context', _configure_oracle_operator_pack_escalation, runners['oracle-operator-pack-escalation']),
            CommandSpec('oracle-operator-pack-assignment', 'Render a structured operator pack assignment surface over escalation plus ownership context', _configure_oracle_operator_pack_assignment, runners['oracle-operator-pack-assignment']),
            CommandSpec('oracle-operator-pack-claim-lease', 'Render a structured operator pack claim/lease surface over handoff plus workboard context', _configure_oracle_operator_pack_claim_lease, runners['oracle-operator-pack-claim-lease']),
            CommandSpec('oracle-operator-pack-claim-lifecycle', 'Render a structured operator pack claim lifecycle surface over claim/lease plus workboard context', _configure_oracle_operator_pack_claim_lifecycle, runners['oracle-operator-pack-claim-lifecycle']),
            CommandSpec('oracle-operator-pack-claim-operability', 'Render a structured operator pack claim-operability surface over execution readiness plus claim lifecycle', _configure_oracle_operator_pack_claim_operability, runners['oracle-operator-pack-claim-operability']),
        ],
    )


__all__ = ['register_oracle_pack_lifecycle_claim_commands']
