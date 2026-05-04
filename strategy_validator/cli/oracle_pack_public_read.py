from __future__ import annotations

from strategy_validator.cli.oracle_pack_command_configs import (
    _configure_oracle_operator_pack_comparison,
    _configure_oracle_operator_pack_dashboard,
    _configure_oracle_operator_pack_drift,
    _configure_oracle_operator_pack_navigation,
    _configure_oracle_operator_pack_query,
    _configure_oracle_operator_pack_timeline,
    _configure_oracle_operator_pack_workbench,
)
from strategy_validator.cli.oracle_pack_runners import (
    cmd_oracle_operator_pack_comparison,
    cmd_oracle_operator_pack_dashboard,
    cmd_oracle_operator_pack_drift,
    cmd_oracle_operator_pack_navigation,
    cmd_oracle_operator_pack_query,
    cmd_oracle_operator_pack_timeline,
    cmd_oracle_operator_pack_workbench,
)

__all__ = [name for name in globals() if name.startswith('_configure_') or name.startswith('cmd_oracle_operator_pack_')]
