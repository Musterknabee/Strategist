from __future__ import annotations

import argparse

from strategy_validator.cli.command_registry import CommandSpec, register_commands
from strategy_validator.cli.oracle_queue_command_configs import (
    _configure_oracle_operator_workboard_action_contract,
    _configure_oracle_operator_transition_policy,
)


def register_oracle_queue_read_contract_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    runners: dict[str, object],
) -> None:
    register_commands(
        subparsers,
        [
            CommandSpec(
                'oracle-operator-workboard-action-contract',
                'Inspect the typed action-execution contract for operator workboard items',
                _configure_oracle_operator_workboard_action_contract,
                runners['oracle-operator-workboard-action-contract'],
            ),
            CommandSpec(
                'oracle-operator-transition-policy',
                'Inspect the governed transition policy for operator workboard actions',
                _configure_oracle_operator_transition_policy,
                runners['oracle-operator-transition-policy'],
            ),
        ],
    )


__all__ = ['register_oracle_queue_read_contract_commands']
