from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_pack_lifecycle_claim_commands import register_oracle_pack_lifecycle_claim_commands
from strategy_validator.cli.oracle_pack_lifecycle_governance_commands import register_oracle_pack_lifecycle_governance_commands


def register_oracle_pack_lifecycle_commands(subparsers: argparse._SubParsersAction, *, runners: dict[str, object]) -> None:
    register_oracle_pack_lifecycle_claim_commands(subparsers, runners=runners)
    register_oracle_pack_lifecycle_governance_commands(subparsers, runners=runners)


__all__ = ['register_oracle_pack_lifecycle_commands']
