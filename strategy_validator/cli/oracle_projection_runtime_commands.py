"""Projection runtime command registration helpers."""
from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_projection_commands import (
    cmd_oracle_projection_artifact_query,
    register_oracle_projection_commands,
)

PROJECTION_RUNNERS = {
    "oracle-projection-artifact-query": cmd_oracle_projection_artifact_query,
}


def register_oracle_projection_runtime_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register projection runtime command cluster."""
    register_oracle_projection_commands(sub, runners=PROJECTION_RUNNERS)
