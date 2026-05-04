"""Bootstrap helpers for the controlled rollout CLI."""
from __future__ import annotations

import argparse

from strategy_validator.cli.rollout_runtime_registry import register_rollout_runtime_commands


def build_rollout_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Controlled rollout operations tooling")
    sub = parser.add_subparsers(dest="cmd", required=True)
    register_rollout_runtime_commands(sub)
    return parser
