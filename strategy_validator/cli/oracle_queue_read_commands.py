from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_queue_read_query_commands import register_oracle_queue_read_query_commands
from strategy_validator.cli.oracle_queue_read_contract_commands import register_oracle_queue_read_contract_commands


def register_oracle_queue_read_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    runners: dict[str, object],
) -> None:
    register_oracle_queue_read_query_commands(subparsers, runners=runners)
    register_oracle_queue_read_contract_commands(subparsers, runners=runners)


__all__ = ['register_oracle_queue_read_commands']
