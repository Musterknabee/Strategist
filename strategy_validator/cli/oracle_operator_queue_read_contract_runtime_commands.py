"""Bounded runtime registration for operator queue contract/policy commands."""
from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_queue_commands import (
    cmd_oracle_operator_transition_policy,
    cmd_oracle_operator_workboard_action_contract,
)
from strategy_validator.cli.oracle_queue_read_contract_commands import register_oracle_queue_read_contract_commands


OPERATOR_QUEUE_READ_CONTRACT_RUNNERS = {
    "oracle-operator-workboard-action-contract": cmd_oracle_operator_workboard_action_contract,
    "oracle-operator-transition-policy": cmd_oracle_operator_transition_policy,
}


def register_oracle_operator_queue_read_contract_runtime_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register bounded operator queue contract/policy runtime commands."""
    register_oracle_queue_read_contract_commands(sub, runners=OPERATOR_QUEUE_READ_CONTRACT_RUNNERS)
