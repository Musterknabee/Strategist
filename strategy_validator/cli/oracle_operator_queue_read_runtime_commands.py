"""Operator queue read runtime command registration façade."""
from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_operator_queue_read_contract_runtime_commands import (
    register_oracle_operator_queue_read_contract_runtime_commands,
)
from strategy_validator.cli.oracle_operator_queue_read_query_runtime_commands import (
    register_oracle_operator_queue_read_query_runtime_commands,
)


def register_oracle_operator_queue_read_runtime_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register bounded operator queue read runtime command clusters."""
    register_oracle_operator_queue_read_query_runtime_commands(sub)
    register_oracle_operator_queue_read_contract_runtime_commands(sub)
__all__ = ["register_oracle_operator_queue_read_runtime_commands"]
