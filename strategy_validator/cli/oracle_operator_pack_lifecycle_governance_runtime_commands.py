"""Bounded runtime runner map for operator pack governance/handoff lifecycle commands."""
from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_pack_execution_runners import (
    cmd_oracle_operator_pack_dispatch_outcome,
)
from strategy_validator.cli.oracle_pack_lifecycle_runners import (
    cmd_oracle_operator_pack_dispatch_permission,
    cmd_oracle_operator_pack_handoff,
    cmd_oracle_operator_pack_lease_governance,
)
from strategy_validator.cli.oracle_pack_lifecycle_governance_commands import register_oracle_pack_lifecycle_governance_commands

OPERATOR_PACK_LIFECYCLE_GOVERNANCE_RUNNERS = {
    "oracle-operator-pack-handoff": cmd_oracle_operator_pack_handoff,
    "oracle-operator-pack-lease-governance": cmd_oracle_operator_pack_lease_governance,
    "oracle-operator-pack-dispatch-permission": cmd_oracle_operator_pack_dispatch_permission,
    "oracle-operator-pack-dispatch-outcome": cmd_oracle_operator_pack_dispatch_outcome,
}


def register_oracle_operator_pack_lifecycle_governance_runtime_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register bounded operator pack governance/handoff lifecycle runtime commands."""
    register_oracle_pack_lifecycle_governance_commands(sub, runners=OPERATOR_PACK_LIFECYCLE_GOVERNANCE_RUNNERS)

__all__ = [
    "OPERATOR_PACK_LIFECYCLE_GOVERNANCE_RUNNERS",
    "register_oracle_operator_pack_lifecycle_governance_runtime_commands",
]
