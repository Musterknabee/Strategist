"""Bounded runtime registration for operator pack commands."""
from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_operator_pack_runtime_compat_execution import register_oracle_operator_pack_execution_runtime_commands
from strategy_validator.cli.oracle_operator_pack_runtime_compat_lifecycle import register_oracle_operator_pack_lifecycle_runtime_commands
from strategy_validator.cli.oracle_operator_pack_runtime_compat_read import register_oracle_operator_pack_read_runtime_commands


def register_oracle_operator_pack_runtime_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register bounded operator pack runtime commands."""
    register_oracle_operator_pack_read_runtime_commands(sub)
    register_oracle_operator_pack_lifecycle_runtime_commands(sub)
    register_oracle_operator_pack_execution_runtime_commands(sub)
__all__ = ["register_oracle_operator_pack_runtime_commands"]
