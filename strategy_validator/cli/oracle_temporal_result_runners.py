from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable, Any

from strategy_validator.cli.oracle_temporal_runner_inputs import (
    load_append_report,
    load_canonicalization,
    load_generated_for_map,
    load_macro_map,
    load_manifest,
    load_micro_map,
    load_strategies_map,
    load_verification_report,
)
from strategy_validator.contracts.oracle_temporal_results import TemporalLaneStatus


def cmd_canonicalize_temporal_semantic_batch(
    ns: argparse.Namespace,
    *,
    canonicalize_payload: Callable[..., Any],
    print_or_write_payload: Callable[..., Any],
) -> int:
    manifest = load_manifest(ns.input)
    macro_by_date = load_macro_map(ns.macro_by_date)
    micro_by_date = load_micro_map(ns.microstructure_by_date)
    generated_for_by_date = load_generated_for_map(ns.generated_for_by_date) if getattr(ns, "generated_for_by_date", "") else None
    strategies_by_date = load_strategies_map(ns.strategies_by_date) if getattr(ns, "strategies_by_date", "") else None
    payload = canonicalize_payload(
        manifest,
        universe_label=ns.universe_label,
        output_root=Path(ns.output_root),
        repo_root=Path(ns.repo_root) if getattr(ns, "repo_root", "") else None,
        macro_by_date=macro_by_date,
        microstructure_by_date=micro_by_date,
        generated_for_by_date=generated_for_by_date,
        strategies_by_date=strategies_by_date,
    )
    print_or_write_payload(payload, getattr(ns, "output", ""))
    return 0


def cmd_append_temporal_canonicalization_event_log(
    ns: argparse.Namespace,
    *,
    append_payload: Callable[..., Any],
    print_or_write_payload: Callable[..., Any],
) -> int:
    canonicalization = load_canonicalization(ns.input)
    payload = append_payload(
        canonicalization,
        lane_path=Path(ns.log_path),
        repo_root=Path(ns.repo_root) if getattr(ns, "repo_root", "") else None,
        require_complete_success=bool(getattr(ns, "require_complete_success", False)),
    )
    print_or_write_payload(payload, getattr(ns, "output", ""))
    return 0


def cmd_summarize_temporal_lane(
    ns: argparse.Namespace,
    *,
    summarize_payload: Callable[..., Any],
    write_temporal_lane_status: Callable[..., Any],
    print_or_write_payload: Callable[..., Any],
) -> int:
    manifest = load_manifest(ns.manifest)
    verification = load_verification_report(ns.verification) if getattr(ns, 'verification', '') else None
    canonicalization = load_canonicalization(ns.canonicalization) if getattr(ns, 'canonicalization', '') else None
    append_report = load_append_report(ns.append_report) if getattr(ns, 'append_report', '') else None
    payload = summarize_payload(
        manifest,
        universe_label=ns.universe_label,
        verification=verification,
        canonicalization=canonicalization,
        append_report=append_report,
    )
    artifact_root = getattr(ns, 'artifact_root', '')
    if artifact_root:
        write_temporal_lane_status(
            Path(artifact_root) / 'ORACLE_TEMPORAL_LANE_STATUS.json',
            TemporalLaneStatus.model_validate(payload['temporal_lane_status']),
        )
    print_or_write_payload(payload, getattr(ns, 'output', ''))
    return 0


def cmd_canonicalize_temporal_semantic_batch_openbb(
    ns: argparse.Namespace,
    *,
    load_config: Callable[..., Any],
    build_provider: Callable[..., Any],
    canonicalize_payload: Callable[..., Any],
    print_or_write_payload: Callable[..., Any],
) -> int:
    cfg = load_config(getattr(ns, "config", "") or None)
    provider = build_provider(cfg)
    if provider is None:
        raise SystemExit("OPENBB_PROVIDER_NOT_ENABLED")
    manifest = load_manifest(ns.input)
    generated_for_by_date = load_generated_for_map(ns.generated_for_by_date) if getattr(ns, "generated_for_by_date", "") else None
    strategies_by_date = load_strategies_map(ns.strategies_by_date) if getattr(ns, "strategies_by_date", "") else None
    payload = canonicalize_payload(
        manifest,
        provider=provider,
        universe_label=ns.universe_label,
        output_root=Path(ns.output_root),
        repo_root=Path(ns.repo_root) if getattr(ns, "repo_root", "") else None,
        generated_for_by_date=generated_for_by_date,
        strategies_by_date=strategies_by_date,
    )
    print_or_write_payload(payload, getattr(ns, "output", ""))
    return 0
