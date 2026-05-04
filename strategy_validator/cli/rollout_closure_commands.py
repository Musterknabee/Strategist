"""Controlled-rollout and closure command helpers for the rollout CLI."""
from __future__ import annotations

import argparse

from strategy_validator.cli.rollout_closure_runtime_commands import (
    cmd_bundle,
    cmd_checklist,
    cmd_fingerprint,
    cmd_review,
    register_rollout_closure_runtime_commands,
)
from strategy_validator.cli.rollout_closure_snapshot_commands import (
    cmd_closure_attestation,
    cmd_closure_snapshot,
    cmd_governed_exception,
    cmd_snapshot_keypair,
    cmd_verify_closure_snapshot_payload,
    cmd_verify_governed_exception,
    register_rollout_closure_snapshot_commands,
)


def register_rollout_closure_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    register_rollout_closure_runtime_commands(sub)
    register_rollout_closure_snapshot_commands(sub)
