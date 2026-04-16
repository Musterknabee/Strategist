from __future__ import annotations

import argparse
import json
from pathlib import Path

from strategy_validator.application import append_temporal_canonicalization_to_event_log_payload, canonicalize_temporal_semantic_batch_payload, extract_temporal_semantic_batch_payload, summarize_temporal_lane_payload, verify_temporal_semantic_batch_payload, fetch_openbb_temporal_sensor_inputs_payload, canonicalize_temporal_semantic_batch_with_openbb_payload
from strategy_validator.cli.oracle_cli_common import print_or_write_payload
from strategy_validator.contracts.oracle import OracleSensorRawMacroInput, OracleSensorRawMicrostructureInput, StrategyHealthSnapshot
from strategy_validator.contracts.oracle_temporal import TemporalCanonicalizationBatchResult, TemporalEventLogAppendBatchResult, TemporalSemanticBatchManifest, TemporalSemanticBatchVerification, TemporalSemanticExtractionBatchRequest
from strategy_validator.core.config import load_config
from strategy_validator.validator.providers.factory import build_nvidia_nim_semantic_provider, build_openbb_market_data_provider
from strategy_validator.validator.oracle_temporal_artifacts import write_temporal_lane_status


def _read_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_extraction_request(path: str) -> TemporalSemanticExtractionBatchRequest:
    return TemporalSemanticExtractionBatchRequest.model_validate(_read_json(path))


def _load_manifest(path: str) -> TemporalSemanticBatchManifest:
    return TemporalSemanticBatchManifest.model_validate(_read_json(path))


def _load_canonicalization(path: str) -> TemporalCanonicalizationBatchResult:
    return TemporalCanonicalizationBatchResult.model_validate(_read_json(path))


def _load_verification_report(path: str) -> TemporalSemanticBatchVerification:
    return TemporalSemanticBatchVerification.model_validate(_read_json(path))


def _load_append_report(path: str) -> TemporalEventLogAppendBatchResult:
    return TemporalEventLogAppendBatchResult.model_validate(_read_json(path))


def _load_macro_map(path: str) -> dict:
    raw = _read_json(path)
    return {k: OracleSensorRawMacroInput.model_validate(v) for k, v in raw.items()}


def _load_micro_map(path: str) -> dict:
    raw = _read_json(path)
    return {k: OracleSensorRawMicrostructureInput.model_validate(v) for k, v in raw.items()}


def _load_generated_for_map(path: str) -> dict:
    raw = _read_json(path)
    return raw


def _load_strategies_map(path: str) -> dict:
    raw = _read_json(path)
    return {k: [StrategyHealthSnapshot.model_validate(item) for item in v] for k, v in raw.items()}


def cmd_extract_temporal_semantic_batch(ns: argparse.Namespace) -> int:
    cfg = load_config(getattr(ns, "config", "") or None)
    provider = build_nvidia_nim_semantic_provider(cfg)
    if provider is None:
        raise SystemExit("NVIDIA_NIM_PROVIDER_NOT_ENABLED")
    request = _load_extraction_request(ns.input)
    payload = extract_temporal_semantic_batch_payload(
        request,
        provider=provider,
        artifact_root=Path(ns.artifact_root) if getattr(ns, "artifact_root", "") else None,
        temperature=float(getattr(ns, "temperature", 0.0) or 0.0),
    )
    print_or_write_payload(payload, getattr(ns, "output", ""))
    return 0


def cmd_verify_temporal_semantic_batch(ns: argparse.Namespace) -> int:
    manifest = _load_manifest(ns.input)
    payload = verify_temporal_semantic_batch_payload(manifest)
    print_or_write_payload(payload, getattr(ns, "output", ""))
    return 0


def cmd_canonicalize_temporal_semantic_batch(ns: argparse.Namespace) -> int:
    manifest = _load_manifest(ns.input)
    macro_by_date = _load_macro_map(ns.macro_by_date)
    micro_by_date = _load_micro_map(ns.microstructure_by_date)
    generated_for_by_date = _load_generated_for_map(ns.generated_for_by_date) if getattr(ns, "generated_for_by_date", "") else None
    strategies_by_date = _load_strategies_map(ns.strategies_by_date) if getattr(ns, "strategies_by_date", "") else None
    payload = canonicalize_temporal_semantic_batch_payload(
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


def cmd_append_temporal_canonicalization_event_log(ns: argparse.Namespace) -> int:
    canonicalization = _load_canonicalization(ns.input)
    payload = append_temporal_canonicalization_to_event_log_payload(
        canonicalization,
        lane_path=Path(ns.log_path),
        repo_root=Path(ns.repo_root) if getattr(ns, "repo_root", "") else None,
        require_complete_success=bool(getattr(ns, "require_complete_success", False)),
    )
    print_or_write_payload(payload, getattr(ns, "output", ""))
    return 0


def cmd_summarize_temporal_lane(ns: argparse.Namespace) -> int:
    manifest = _load_manifest(ns.manifest)
    verification = _load_verification_report(ns.verification) if getattr(ns, 'verification', '') else None
    canonicalization = _load_canonicalization(ns.canonicalization) if getattr(ns, 'canonicalization', '') else None
    append_report = _load_append_report(ns.append_report) if getattr(ns, 'append_report', '') else None
    payload = summarize_temporal_lane_payload(
        manifest,
        universe_label=ns.universe_label,
        verification=verification,
        canonicalization=canonicalization,
        append_report=append_report,
    )
    artifact_root = getattr(ns, 'artifact_root', '')
    if artifact_root:
        from strategy_validator.contracts.oracle_temporal import TemporalLaneStatus
        write_temporal_lane_status(
            Path(artifact_root) / 'ORACLE_TEMPORAL_LANE_STATUS.json',
            TemporalLaneStatus.model_validate(payload['temporal_lane_status']),
        )
    print_or_write_payload(payload, getattr(ns, 'output', ''))
    return 0


def cmd_fetch_openbb_temporal_sensor_inputs(ns: argparse.Namespace) -> int:
    cfg = load_config(getattr(ns, "config", "") or None)
    provider = build_openbb_market_data_provider(cfg)
    if provider is None:
        raise SystemExit("OPENBB_PROVIDER_NOT_ENABLED")
    dates = json.loads(Path(ns.dates).read_text(encoding="utf-8"))
    payload = fetch_openbb_temporal_sensor_inputs_payload(
        dates,
        provider=provider,
        universe_label=ns.universe_label,
    )
    print_or_write_payload(payload, getattr(ns, "output", ""))
    return 0


def cmd_canonicalize_temporal_semantic_batch_openbb(ns: argparse.Namespace) -> int:
    cfg = load_config(getattr(ns, "config", "") or None)
    provider = build_openbb_market_data_provider(cfg)
    if provider is None:
        raise SystemExit("OPENBB_PROVIDER_NOT_ENABLED")
    manifest = _load_manifest(ns.input)
    generated_for_by_date = _load_generated_for_map(ns.generated_for_by_date) if getattr(ns, "generated_for_by_date", "") else None
    strategies_by_date = _load_strategies_map(ns.strategies_by_date) if getattr(ns, "strategies_by_date", "") else None
    payload = canonicalize_temporal_semantic_batch_with_openbb_payload(
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
