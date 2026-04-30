from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable, Any

from strategy_validator.cli.oracle_temporal_runner_inputs import (
    load_extraction_request,
    load_manifest,
)


def cmd_extract_temporal_semantic_batch(
    ns: argparse.Namespace,
    *,
    load_config: Callable[..., Any],
    build_provider: Callable[..., Any],
    extract_payload: Callable[..., Any],
    print_or_write_payload: Callable[..., Any],
) -> int:
    cfg = load_config(getattr(ns, "config", "") or None)
    provider = build_provider(cfg)
    if provider is None:
        raise SystemExit("NVIDIA_NIM_PROVIDER_NOT_ENABLED")
    request = load_extraction_request(ns.input)
    payload = extract_payload(
        request,
        provider=provider,
        artifact_root=Path(ns.artifact_root) if getattr(ns, "artifact_root", "") else None,
        temperature=float(getattr(ns, "temperature", 0.0) or 0.0),
    )
    print_or_write_payload(payload, getattr(ns, "output", ""))
    return 0


def cmd_verify_temporal_semantic_batch(
    ns: argparse.Namespace,
    *,
    verify_payload: Callable[..., Any],
    print_or_write_payload: Callable[..., Any],
) -> int:
    manifest = load_manifest(ns.input)
    payload = verify_payload(manifest)
    print_or_write_payload(payload, getattr(ns, "output", ""))
    return 0


def cmd_fetch_openbb_temporal_sensor_inputs(
    ns: argparse.Namespace,
    *,
    load_config: Callable[..., Any],
    build_provider: Callable[..., Any],
    fetch_payload: Callable[..., Any],
    print_or_write_payload: Callable[..., Any],
) -> int:
    cfg = load_config(getattr(ns, "config", "") or None)
    provider = build_provider(cfg)
    if provider is None:
        raise SystemExit("OPENBB_PROVIDER_NOT_ENABLED")
    dates = json.loads(Path(ns.dates).read_text(encoding="utf-8"))
    payload = fetch_payload(
        dates,
        provider=provider,
        universe_label=ns.universe_label,
    )
    print_or_write_payload(payload, getattr(ns, "output", ""))
    return 0
