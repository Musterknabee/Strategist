"""Operator queue and pack CLI command registration helpers."""
from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_operator_runtime_compat_pack import *
from strategy_validator.cli.oracle_operator_runtime_compat_queue import *
from strategy_validator.cli.oracle_operator_runtime_compat_pack import __all__ as _PACK_RUNTIME_EXPORTS
from strategy_validator.cli.oracle_operator_runtime_compat_queue import __all__ as _QUEUE_RUNTIME_EXPORTS


def register_oracle_operator_runtime_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register operator queue and pack command clusters."""
    register_oracle_operator_queue_runtime_commands(sub)
    register_oracle_operator_pack_runtime_commands(sub)


__all__ = [
    'register_oracle_operator_runtime_commands',
    *_QUEUE_RUNTIME_EXPORTS,
    *_PACK_RUNTIME_EXPORTS,
]
