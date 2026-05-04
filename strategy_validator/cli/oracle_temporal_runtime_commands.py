from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_temporal_commands import register_oracle_temporal_commands
from strategy_validator.cli.oracle_temporal_runners import (
    cmd_append_temporal_canonicalization_event_log,
    cmd_canonicalize_temporal_semantic_batch,
    cmd_canonicalize_temporal_semantic_batch_openbb,
    cmd_extract_temporal_semantic_batch,
    cmd_fetch_openbb_temporal_sensor_inputs,
    cmd_summarize_temporal_lane,
    cmd_verify_temporal_semantic_batch,
)

TEMPORAL_RUNNERS = {
    "append-temporal-canonicalization-event-log": cmd_append_temporal_canonicalization_event_log,
    "extract-temporal-semantic-batch": cmd_extract_temporal_semantic_batch,
    "verify-temporal-semantic-batch": cmd_verify_temporal_semantic_batch,
    "canonicalize-temporal-semantic-batch": cmd_canonicalize_temporal_semantic_batch,
    "summarize-temporal-lane": cmd_summarize_temporal_lane,
    "fetch-openbb-temporal-sensor-inputs": cmd_fetch_openbb_temporal_sensor_inputs,
    "canonicalize-temporal-semantic-batch-openbb": cmd_canonicalize_temporal_semantic_batch_openbb,
}


def register_oracle_temporal_runtime_commands(
    sub: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register bounded temporal runtime commands."""
    register_oracle_temporal_commands(sub, runners=TEMPORAL_RUNNERS)
