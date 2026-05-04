from __future__ import annotations

from datetime import date, datetime
from typing import Any

from strategy_validator.application.idempotency import derive_idempotency_key
from strategy_validator.contracts.oracle_core import StrategyHealthSnapshot
from strategy_validator.contracts.oracle_strategic_fusion import OracleSensorRawMacroInput, OracleSensorRawMicrostructureInput
from strategy_validator.contracts.oracle_temporal_results import TemporalCanonicalizationBatchResult, TemporalEventLogAppendBatchResult
from strategy_validator.contracts.oracle_temporal_semantics import TemporalProviderArtifactManifest, TemporalSemanticBatchManifest, TemporalSemanticBatchVerification, TemporalSemanticExtractionBatchRequest
from strategy_validator.validator.oracle_temporal_extraction import extract_temporal_semantic_batch
from strategy_validator.validator.oracle_temporal_materialization import materialize_temporal_semantic_sensor_inputs
from strategy_validator.validator.oracle_temporal_pipeline import canonicalize_temporal_semantic_batch
from strategy_validator.validator.oracle_temporal_event_log import append_temporal_canonicalization_to_event_log
from strategy_validator.validator.oracle_temporal_status import summarize_temporal_lane
from strategy_validator.validator.oracle_temporal_verification import verify_temporal_semantic_batch_manifest
from strategy_validator.validator.oracle_openbb_ingress import fetch_openbb_temporal_sensor_inputs


def build_temporal_semantic_batch_payload(
    manifest: TemporalSemanticBatchManifest,
    *,
    source_label: str,
) -> dict[str, Any]:
    payload = {
        "source_label": source_label,
        "manifest": manifest.model_dump(mode="json"),
    }
    return {
        "idempotency_key": derive_idempotency_key(
            command_name="build_temporal_semantic_batch_payload",
            payload=payload,
        ),
        "temporal_batch_request": payload,
    }


def verify_temporal_semantic_batch_payload(
    manifest: TemporalSemanticBatchManifest,
    *,
    expected_dates: list[date] | tuple[date, ...] | None = None,
    allowed_prefix_digests_by_date: dict[date, str] | None = None,
    max_citation_timestamp_by_date: dict[date, datetime] | None = None,
) -> dict[str, Any]:
    verification = verify_temporal_semantic_batch_manifest(
        manifest,
        expected_dates=expected_dates,
        allowed_prefix_digests_by_date=allowed_prefix_digests_by_date,
        max_citation_timestamp_by_date=max_citation_timestamp_by_date,
    )
    payload = verification.model_dump(mode="json")
    return {
        "idempotency_key": derive_idempotency_key(
            command_name="verify_temporal_semantic_batch_payload",
            payload=payload,
        ),
        "verification": payload,
    }


def materialize_temporal_semantic_sensor_payloads(
    manifest: TemporalSemanticBatchManifest,
    *,
    universe_label: str,
    macro_by_date: dict[date | datetime | str, OracleSensorRawMacroInput],
    microstructure_by_date: dict[date | datetime | str, OracleSensorRawMicrostructureInput],
    generated_for_by_date: dict[date | datetime | str, datetime] | None = None,
    strategies_by_date: dict[date | datetime | str, list[StrategyHealthSnapshot]] | None = None,
) -> dict[str, Any]:
    payloads = materialize_temporal_semantic_sensor_inputs(
        manifest,
        universe_label=universe_label,
        macro_by_date=macro_by_date,
        microstructure_by_date=microstructure_by_date,
        generated_for_by_date=generated_for_by_date,
        strategies_by_date=strategies_by_date,
    )
    serialized = [item.model_dump(mode="json") for item in payloads]
    return {
        "idempotency_key": derive_idempotency_key(
            command_name="materialize_temporal_semantic_sensor_payloads",
            payload={
                "universe_label": universe_label,
                "payloads": serialized,
            },
        ),
        "sensor_ingestion_payloads": serialized,
    }


def canonicalize_temporal_semantic_batch_payload(
    manifest: TemporalSemanticBatchManifest,
    *,
    universe_label: str,
    output_root,
    repo_root=None,
    macro_by_date: dict[date | datetime | str, OracleSensorRawMacroInput],
    microstructure_by_date: dict[date | datetime | str, OracleSensorRawMicrostructureInput],
    generated_for_by_date: dict[date | datetime | str, datetime] | None = None,
    strategies_by_date: dict[date | datetime | str, list[StrategyHealthSnapshot]] | None = None,
    verification=None,
    expected_dates: list[date] | tuple[date, ...] | None = None,
    allowed_prefix_digests_by_date: dict[date, str] | None = None,
    max_citation_timestamp_by_date: dict[date, datetime] | None = None,
    signing_private_key_path=None,
    public_key_path=None,
) -> dict[str, Any]:
    report = canonicalize_temporal_semantic_batch(
        manifest,
        universe_label=universe_label,
        output_root=output_root,
        repo_root=repo_root,
        macro_by_date=macro_by_date,
        microstructure_by_date=microstructure_by_date,
        generated_for_by_date=generated_for_by_date,
        strategies_by_date=strategies_by_date,
        verification=verification,
        expected_dates=expected_dates,
        allowed_prefix_digests_by_date=allowed_prefix_digests_by_date,
        max_citation_timestamp_by_date=max_citation_timestamp_by_date,
        signing_private_key_path=signing_private_key_path,
        public_key_path=public_key_path,
    )
    payload = report.model_dump(mode="json")
    return {
        "idempotency_key": derive_idempotency_key(
            command_name="canonicalize_temporal_semantic_batch_payload",
            payload=payload,
        ),
        "canonicalization": payload,
    }


def extract_temporal_semantic_batch_payload(
    request: TemporalSemanticExtractionBatchRequest,
    *,
    provider,
    artifact_root=None,
    temperature: float = 0.0,
) -> dict[str, Any]:
    manifest, artifact = extract_temporal_semantic_batch(
        request,
        provider=provider,
        artifact_root=artifact_root,
        temperature=temperature,
    )
    payload = {
        "manifest": manifest.model_dump(mode="json"),
        "provider_artifact": artifact.model_dump(mode="json"),
    }
    return {
        "idempotency_key": derive_idempotency_key(
            command_name="extract_temporal_semantic_batch_payload",
            payload=payload,
        ),
        "temporal_semantic_batch": payload["manifest"],
        "provider_artifact": payload["provider_artifact"],
    }


def append_temporal_canonicalization_to_event_log_payload(
    canonicalization,
    *,
    lane_path,
    repo_root=None,
    require_complete_success: bool = False,
) -> dict[str, Any]:
    canonicalization_model = (
        canonicalization
        if isinstance(canonicalization, TemporalCanonicalizationBatchResult)
        else TemporalCanonicalizationBatchResult.model_validate(canonicalization)
    )
    report = append_temporal_canonicalization_to_event_log(
        canonicalization_model,
        lane_path=lane_path,
        repo_root=repo_root,
        require_complete_success=require_complete_success,
    )
    payload = report.model_dump(mode="json")
    return {
        "idempotency_key": derive_idempotency_key(
            command_name="append_temporal_canonicalization_to_event_log_payload",
            payload=payload,
        ),
        "event_log_append": payload,
    }


def summarize_temporal_lane_payload(
    manifest,
    *,
    universe_label: str,
    verification=None,
    canonicalization=None,
    append_report=None,
) -> dict[str, Any]:
    manifest_model = manifest if isinstance(manifest, TemporalSemanticBatchManifest) else TemporalSemanticBatchManifest.model_validate(manifest)
    verification_model = None if verification is None else (verification if isinstance(verification, TemporalSemanticBatchVerification) else TemporalSemanticBatchVerification.model_validate(verification))
    canonicalization_model = None if canonicalization is None else (canonicalization if isinstance(canonicalization, TemporalCanonicalizationBatchResult) else TemporalCanonicalizationBatchResult.model_validate(canonicalization))
    append_model = None if append_report is None else (append_report if isinstance(append_report, TemporalEventLogAppendBatchResult) else TemporalEventLogAppendBatchResult.model_validate(append_report))
    report = summarize_temporal_lane(
        manifest_model,
        universe_label=universe_label,
        verification=verification_model,
        canonicalization=canonicalization_model,
        append_report=append_model,
    )
    payload = report.model_dump(mode="json")
    return {
        "idempotency_key": derive_idempotency_key(
            command_name="summarize_temporal_lane_payload",
            payload=payload,
        ),
        "temporal_lane_status": payload,
    }


def fetch_openbb_temporal_sensor_inputs_payload(
    dates: list[date | datetime | str] | tuple[date | datetime | str, ...],
    *,
    provider,
    universe_label: str,
) -> dict[str, Any]:
    macro_by_date, microstructure_by_date, report = fetch_openbb_temporal_sensor_inputs(
        dates,
        provider=provider,
        universe_label=universe_label,
    )
    payload = {
        "macro_by_date": {k.isoformat(): v.model_dump(mode="json") for k, v in macro_by_date.items()},
        "microstructure_by_date": {k.isoformat(): v.model_dump(mode="json") for k, v in microstructure_by_date.items()},
        "ingress_report": report.model_dump(mode="json"),
    }
    return {
        "idempotency_key": derive_idempotency_key(
            command_name="fetch_openbb_temporal_sensor_inputs_payload",
            payload=payload,
        ),
        "macro_by_date": payload["macro_by_date"],
        "microstructure_by_date": payload["microstructure_by_date"],
        "ingress_report": payload["ingress_report"],
    }


def canonicalize_temporal_semantic_batch_with_openbb_payload(
    manifest: TemporalSemanticBatchManifest,
    *,
    provider,
    universe_label: str,
    output_root,
    repo_root=None,
    generated_for_by_date: dict[date | datetime | str, datetime] | None = None,
    strategies_by_date: dict[date | datetime | str, list[StrategyHealthSnapshot]] | None = None,
) -> dict[str, Any]:
    macro_by_date, microstructure_by_date, ingress_report = fetch_openbb_temporal_sensor_inputs(
        [day.point_in_time_date for day in manifest.days],
        provider=provider,
        universe_label=universe_label,
    )
    canonicalization = canonicalize_temporal_semantic_batch_payload(
        manifest,
        universe_label=universe_label,
        output_root=output_root,
        repo_root=repo_root,
        macro_by_date=macro_by_date,
        microstructure_by_date=microstructure_by_date,
        generated_for_by_date=generated_for_by_date,
        strategies_by_date=strategies_by_date,
    )
    payload = {
        "ingress_report": ingress_report.model_dump(mode="json"),
        "canonicalization": canonicalization["canonicalization"],
    }
    return {
        "idempotency_key": derive_idempotency_key(
            command_name="canonicalize_temporal_semantic_batch_with_openbb_payload",
            payload=payload,
        ),
        "ingress_report": payload["ingress_report"],
        "canonicalization": payload["canonicalization"],
    }
