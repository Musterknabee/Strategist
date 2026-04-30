from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_queue_transition_escalation_commands import register_oracle_queue_transition_escalation_commands
from strategy_validator.cli.oracle_queue_transition_reentry_commands import register_oracle_queue_transition_reentry_commands


def register_oracle_queue_transition_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    runners: dict[str, object],
) -> None:
    register_oracle_queue_transition_escalation_commands(subparsers, runners=runners)
    register_oracle_queue_transition_reentry_commands(subparsers, runners=runners)


__all__ = ['register_oracle_queue_transition_commands']
