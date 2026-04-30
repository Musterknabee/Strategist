"""Bounded runtime runner map for operator pack query/navigation/workbench commands."""
from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_pack_read_runners import (
    cmd_oracle_operator_pack_navigation,
    cmd_oracle_operator_pack_query,
    cmd_oracle_operator_pack_workbench,
)
from strategy_validator.cli.oracle_pack_read_query_commands import register_oracle_pack_read_query_commands

OPERATOR_PACK_READ_QUERY_RUNNERS = {
    "oracle-operator-pack-query": cmd_oracle_operator_pack_query,
    "oracle-operator-pack-navigation": cmd_oracle_operator_pack_navigation,
    "oracle-operator-pack-workbench": cmd_oracle_operator_pack_workbench,
}


def register_oracle_operator_pack_read_query_runtime_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register bounded operator pack read-query runtime commands."""
    register_oracle_pack_read_query_commands(sub, runners=OPERATOR_PACK_READ_QUERY_RUNNERS)

__all__ = [
    "OPERATOR_PACK_READ_QUERY_RUNNERS",
    "register_oracle_operator_pack_read_query_runtime_commands",
]
