from __future__ import annotations

import argparse

from strategy_validator.cli.command_registry import CommandSpec, register_commands
from strategy_validator.cli.oracle_pack_command_configs import (
    _configure_oracle_operator_pack_comparison,
    _configure_oracle_operator_pack_dashboard,
    _configure_oracle_operator_pack_drift,
    _configure_oracle_operator_pack_timeline,
)


def register_oracle_pack_read_dashboard_commands(subparsers: argparse._SubParsersAction, *, runners: dict[str, object]) -> None:
    register_commands(
        subparsers,
        [
            CommandSpec('oracle-operator-pack-dashboard', 'Render a structured operator pack dashboard over workbench plus navigation', _configure_oracle_operator_pack_dashboard, runners['oracle-operator-pack-dashboard']),
            CommandSpec('oracle-operator-pack-timeline', 'Render a structured operator pack timeline over indexed pack activity', _configure_oracle_operator_pack_timeline, runners['oracle-operator-pack-timeline']),
            CommandSpec('oracle-operator-pack-comparison', 'Render a structured operator pack comparison over recent indexed pack generations', _configure_oracle_operator_pack_comparison, runners['oracle-operator-pack-comparison']),
            CommandSpec('oracle-operator-pack-drift', 'Render a structured operator pack drift alert surface over worsening or sustained degraded indexed packs', _configure_oracle_operator_pack_drift, runners['oracle-operator-pack-drift']),
        ],
    )


__all__ = ['register_oracle_pack_read_dashboard_commands']
