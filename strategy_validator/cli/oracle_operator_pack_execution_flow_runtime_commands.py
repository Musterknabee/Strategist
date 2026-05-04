"""Bounded runtime runner map for operator pack execution-flow commands."""
from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_pack_execution_runners import (
    cmd_oracle_operator_pack_approval_disposition,
    cmd_oracle_operator_pack_approval_needed,
    cmd_oracle_operator_pack_dispatch_outcome,
    cmd_oracle_operator_pack_execution_authorization,
    cmd_oracle_operator_pack_execution_exception,
    cmd_oracle_operator_pack_execution_finality,
    cmd_oracle_operator_pack_execution_force,
    cmd_oracle_operator_pack_execution_readiness,
)
from strategy_validator.cli.oracle_pack_execution_flow_commands import register_oracle_pack_execution_flow_commands

OPERATOR_PACK_EXECUTION_FLOW_RUNNERS = {
    "oracle-operator-pack-execution-readiness": cmd_oracle_operator_pack_execution_readiness,
    "oracle-operator-pack-dispatch-outcome": cmd_oracle_operator_pack_dispatch_outcome,
    "oracle-operator-pack-execution-exception": cmd_oracle_operator_pack_execution_exception,
    "oracle-operator-pack-approval-needed": cmd_oracle_operator_pack_approval_needed,
    "oracle-operator-pack-approval-disposition": cmd_oracle_operator_pack_approval_disposition,
    "oracle-operator-pack-execution-authorization": cmd_oracle_operator_pack_execution_authorization,
    "oracle-operator-pack-execution-force": cmd_oracle_operator_pack_execution_force,
    "oracle-operator-pack-execution-finality": cmd_oracle_operator_pack_execution_finality,
}


def register_oracle_operator_pack_execution_flow_runtime_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register bounded operator pack execution-flow runtime commands."""
    register_oracle_pack_execution_flow_commands(sub, runners=OPERATOR_PACK_EXECUTION_FLOW_RUNNERS)

__all__ = [
    "OPERATOR_PACK_EXECUTION_FLOW_RUNNERS",
    "register_oracle_operator_pack_execution_flow_runtime_commands",
]
