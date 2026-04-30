"""Bounded runtime runner map for operator pack claim/escalation lifecycle commands."""
from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_pack_lifecycle_runners import (
    cmd_oracle_operator_pack_assignment,
    cmd_oracle_operator_pack_claim_lease,
    cmd_oracle_operator_pack_claim_lifecycle,
    cmd_oracle_operator_pack_claim_operability,
    cmd_oracle_operator_pack_escalation,
)
from strategy_validator.cli.oracle_pack_lifecycle_claim_commands import register_oracle_pack_lifecycle_claim_commands

OPERATOR_PACK_LIFECYCLE_CLAIM_RUNNERS = {
    "oracle-operator-pack-escalation": cmd_oracle_operator_pack_escalation,
    "oracle-operator-pack-assignment": cmd_oracle_operator_pack_assignment,
    "oracle-operator-pack-claim-lease": cmd_oracle_operator_pack_claim_lease,
    "oracle-operator-pack-claim-lifecycle": cmd_oracle_operator_pack_claim_lifecycle,
    "oracle-operator-pack-claim-operability": cmd_oracle_operator_pack_claim_operability,
}


def register_oracle_operator_pack_lifecycle_claim_runtime_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register bounded operator pack claim/escalation lifecycle runtime commands."""
    register_oracle_pack_lifecycle_claim_commands(sub, runners=OPERATOR_PACK_LIFECYCLE_CLAIM_RUNNERS)

__all__ = [
    "OPERATOR_PACK_LIFECYCLE_CLAIM_RUNNERS",
    "register_oracle_operator_pack_lifecycle_claim_runtime_commands",
]
