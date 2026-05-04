"""Bounded runtime runner map for operator pack terminal/finality commands."""
from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_pack_execution_runners import (
    cmd_oracle_operator_pack_execution_finality,
    cmd_oracle_operator_pack_terminal_archive,
    cmd_oracle_operator_pack_terminal_closure,
    cmd_oracle_operator_pack_terminal_record,
    cmd_oracle_operator_pack_terminal_record_publish,
    cmd_oracle_operator_pack_terminal_resolution,
)
from strategy_validator.cli.oracle_pack_terminal_commands import register_oracle_pack_terminal_commands

OPERATOR_PACK_TERMINAL_RUNNERS = {
    "oracle-operator-pack-terminal-resolution": cmd_oracle_operator_pack_terminal_resolution,
    "oracle-operator-pack-terminal-closure": cmd_oracle_operator_pack_terminal_closure,
    "oracle-operator-pack-terminal-archive": cmd_oracle_operator_pack_terminal_archive,
    "oracle-operator-pack-terminal-record": cmd_oracle_operator_pack_terminal_record,
    "oracle-operator-pack-terminal-record-publish": cmd_oracle_operator_pack_terminal_record_publish,
    "oracle-operator-pack-execution-finality": cmd_oracle_operator_pack_execution_finality,
}


def register_oracle_operator_pack_terminal_runtime_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register bounded operator pack terminal/finality runtime commands."""
    register_oracle_pack_terminal_commands(sub, runners=OPERATOR_PACK_TERMINAL_RUNNERS)

__all__ = [
    "OPERATOR_PACK_TERMINAL_RUNNERS",
    "register_oracle_operator_pack_terminal_runtime_commands",
]
