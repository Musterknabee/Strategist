"""Bounded runtime registration for operator queue read/query commands."""
from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_queue_commands import (
    cmd_oracle_operator_queue_query,
    cmd_oracle_operator_workboard_query,
)
from strategy_validator.cli.oracle_queue_read_query_commands import register_oracle_queue_read_query_commands


OPERATOR_QUEUE_READ_QUERY_RUNNERS = {
    "oracle-operator-queue-query": cmd_oracle_operator_queue_query,
    "oracle-operator-workboard-query": cmd_oracle_operator_workboard_query,
}


def register_oracle_operator_queue_read_query_runtime_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register bounded operator queue read/query runtime commands."""
    register_oracle_queue_read_query_commands(sub, runners=OPERATOR_QUEUE_READ_QUERY_RUNNERS)
