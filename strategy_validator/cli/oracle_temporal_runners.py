from __future__ import annotations

import argparse

from strategy_validator.cli.application_temporal_surfaces import (
    append_temporal_canonicalization_to_event_log_payload,
    canonicalize_temporal_semantic_batch_payload,
    canonicalize_temporal_semantic_batch_with_openbb_payload,
    extract_temporal_semantic_batch_payload,
    fetch_openbb_temporal_sensor_inputs_payload,
    summarize_temporal_lane_payload,
    verify_temporal_semantic_batch_payload,
)
from strategy_validator.cli.oracle_cli_common import print_or_write_payload
from strategy_validator.cli.oracle_temporal_result_runners import (
    cmd_append_temporal_canonicalization_event_log as _cmd_append_temporal_canonicalization_event_log,
)
from strategy_validator.cli.oracle_temporal_result_runners import (
    cmd_canonicalize_temporal_semantic_batch as _cmd_canonicalize_temporal_semantic_batch,
)
from strategy_validator.cli.oracle_temporal_result_runners import (
    cmd_canonicalize_temporal_semantic_batch_openbb as _cmd_canonicalize_temporal_semantic_batch_openbb,
)
from strategy_validator.cli.oracle_temporal_result_runners import (
    cmd_summarize_temporal_lane as _cmd_summarize_temporal_lane,
)
from strategy_validator.cli.oracle_temporal_semantic_runners import (
    cmd_extract_temporal_semantic_batch as _cmd_extract_temporal_semantic_batch,
)
from strategy_validator.cli.oracle_temporal_semantic_runners import (
    cmd_fetch_openbb_temporal_sensor_inputs as _cmd_fetch_openbb_temporal_sensor_inputs,
)
from strategy_validator.cli.oracle_temporal_semantic_runners import (
    cmd_verify_temporal_semantic_batch as _cmd_verify_temporal_semantic_batch,
)
from strategy_validator.core.config import load_config
from strategy_validator.validator.oracle_temporal_artifacts import write_temporal_lane_status
from strategy_validator.validator.providers.factory import (
    build_nvidia_nim_semantic_provider,
    build_openbb_market_data_provider,
)


def cmd_extract_temporal_semantic_batch(ns: argparse.Namespace) -> int:
    return _cmd_extract_temporal_semantic_batch(
        ns,
        load_config=load_config,
        build_provider=build_nvidia_nim_semantic_provider,
        extract_payload=extract_temporal_semantic_batch_payload,
        print_or_write_payload=print_or_write_payload,
    )


def cmd_verify_temporal_semantic_batch(ns: argparse.Namespace) -> int:
    return _cmd_verify_temporal_semantic_batch(
        ns,
        verify_payload=verify_temporal_semantic_batch_payload,
        print_or_write_payload=print_or_write_payload,
    )


def cmd_canonicalize_temporal_semantic_batch(ns: argparse.Namespace) -> int:
    return _cmd_canonicalize_temporal_semantic_batch(
        ns,
        canonicalize_payload=canonicalize_temporal_semantic_batch_payload,
        print_or_write_payload=print_or_write_payload,
    )


def cmd_append_temporal_canonicalization_event_log(ns: argparse.Namespace) -> int:
    return _cmd_append_temporal_canonicalization_event_log(
        ns,
        append_payload=append_temporal_canonicalization_to_event_log_payload,
        print_or_write_payload=print_or_write_payload,
    )


def cmd_summarize_temporal_lane(ns: argparse.Namespace) -> int:
    return _cmd_summarize_temporal_lane(
        ns,
        summarize_payload=summarize_temporal_lane_payload,
        write_temporal_lane_status=write_temporal_lane_status,
        print_or_write_payload=print_or_write_payload,
    )


def cmd_fetch_openbb_temporal_sensor_inputs(ns: argparse.Namespace) -> int:
    return _cmd_fetch_openbb_temporal_sensor_inputs(
        ns,
        load_config=load_config,
        build_provider=build_openbb_market_data_provider,
        fetch_payload=fetch_openbb_temporal_sensor_inputs_payload,
        print_or_write_payload=print_or_write_payload,
    )


def cmd_canonicalize_temporal_semantic_batch_openbb(ns: argparse.Namespace) -> int:
    return _cmd_canonicalize_temporal_semantic_batch_openbb(
        ns,
        load_config=load_config,
        build_provider=build_openbb_market_data_provider,
        canonicalize_payload=canonicalize_temporal_semantic_batch_with_openbb_payload,
        print_or_write_payload=print_or_write_payload,
    )
