"""Bounded runtime registration registry for rollout CLI families."""
from __future__ import annotations

import argparse
from collections.abc import Callable
from typing import Any

from strategy_validator.cli.oracle_briefing_replay_runtime_commands import register_oracle_briefing_replay_runtime_commands
from strategy_validator.cli.oracle_event_runtime_commands import register_oracle_event_runtime_commands
from strategy_validator.cli.oracle_operator_runtime_commands import register_oracle_operator_runtime_commands
from strategy_validator.cli.oracle_projection_runtime_commands import register_oracle_projection_runtime_commands
from strategy_validator.cli.oracle_strategy_runtime_commands import register_oracle_strategy_runtime_commands
from strategy_validator.cli.oracle_temporal_runtime_commands import register_oracle_temporal_runtime_commands
from strategy_validator.cli.rollout_closure_commands import register_rollout_closure_commands

RolloutRuntimeRegistrar = Callable[[Any], None]

ROLLOUT_RUNTIME_REGISTRARS: tuple[RolloutRuntimeRegistrar, ...] = (
    register_rollout_closure_commands,
    register_oracle_strategy_runtime_commands,
    register_oracle_event_runtime_commands,
    register_oracle_projection_runtime_commands,
    register_oracle_operator_runtime_commands,
    register_oracle_temporal_runtime_commands,
    register_oracle_briefing_replay_runtime_commands,
)


def register_rollout_runtime_commands(sub: Any) -> None:
    """Register all rollout runtime command families in stable order."""
    for registrar in ROLLOUT_RUNTIME_REGISTRARS:
        registrar(sub)
