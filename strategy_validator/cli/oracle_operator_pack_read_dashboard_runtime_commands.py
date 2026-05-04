"""Bounded runtime runner map for operator pack dashboard/timeline commands."""
from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_pack_read_runners import (
    cmd_oracle_operator_pack_comparison,
    cmd_oracle_operator_pack_dashboard,
    cmd_oracle_operator_pack_drift,
    cmd_oracle_operator_pack_timeline,
)
from strategy_validator.cli.oracle_pack_read_dashboard_commands import register_oracle_pack_read_dashboard_commands

OPERATOR_PACK_READ_DASHBOARD_RUNNERS = {
    "oracle-operator-pack-dashboard": cmd_oracle_operator_pack_dashboard,
    "oracle-operator-pack-timeline": cmd_oracle_operator_pack_timeline,
    "oracle-operator-pack-comparison": cmd_oracle_operator_pack_comparison,
    "oracle-operator-pack-drift": cmd_oracle_operator_pack_drift,
}


def register_oracle_operator_pack_read_dashboard_runtime_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register bounded operator pack dashboard/timeline runtime commands."""
    register_oracle_pack_read_dashboard_commands(sub, runners=OPERATOR_PACK_READ_DASHBOARD_RUNNERS)

__all__ = [
    "OPERATOR_PACK_READ_DASHBOARD_RUNNERS",
    "register_oracle_operator_pack_read_dashboard_runtime_commands",
]
