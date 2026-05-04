"""Bounded runtime registration for operator pack lifecycle / ownership commands."""
from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_operator_pack_lifecycle_claim_runtime_commands import (
    OPERATOR_PACK_LIFECYCLE_CLAIM_RUNNERS,
    register_oracle_operator_pack_lifecycle_claim_runtime_commands,
)
from strategy_validator.cli.oracle_operator_pack_lifecycle_governance_runtime_commands import (
    OPERATOR_PACK_LIFECYCLE_GOVERNANCE_RUNNERS,
    register_oracle_operator_pack_lifecycle_governance_runtime_commands,
)

OPERATOR_PACK_LIFECYCLE_RUNNERS = {
    **OPERATOR_PACK_LIFECYCLE_CLAIM_RUNNERS,
    **OPERATOR_PACK_LIFECYCLE_GOVERNANCE_RUNNERS,
}


def register_oracle_operator_pack_lifecycle_runtime_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register bounded operator pack lifecycle runtime commands."""
    register_oracle_operator_pack_lifecycle_claim_runtime_commands(sub)
    register_oracle_operator_pack_lifecycle_governance_runtime_commands(sub)
__all__ = [
    "OPERATOR_PACK_LIFECYCLE_RUNNERS",
    "register_oracle_operator_pack_lifecycle_runtime_commands",
]
