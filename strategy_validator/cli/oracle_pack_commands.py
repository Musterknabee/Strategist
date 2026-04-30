from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_pack_execution_commands import register_oracle_pack_execution_commands
from strategy_validator.cli.oracle_pack_lifecycle_commands import register_oracle_pack_lifecycle_commands
from strategy_validator.cli.oracle_pack_read_commands import register_oracle_pack_read_commands
from strategy_validator.cli.oracle_pack_public_read import *
from strategy_validator.cli.oracle_pack_public_lifecycle import *
from strategy_validator.cli.oracle_pack_public_execution import *
from strategy_validator.cli.oracle_pack_public_read import __all__ as _READ_EXPORTS
from strategy_validator.cli.oracle_pack_public_lifecycle import __all__ as _LIFECYCLE_EXPORTS
from strategy_validator.cli.oracle_pack_public_execution import __all__ as _EXECUTION_EXPORTS


def register_oracle_pack_commands(subparsers: argparse._SubParsersAction, *, runners: dict[str, object]) -> None:
    register_oracle_pack_read_commands(subparsers, runners=runners)
    register_oracle_pack_lifecycle_commands(subparsers, runners=runners)
    register_oracle_pack_execution_commands(subparsers, runners=runners)


__all__ = [
    'register_oracle_pack_commands',
    *_READ_EXPORTS,
    *_LIFECYCLE_EXPORTS,
    *_EXECUTION_EXPORTS,
]
