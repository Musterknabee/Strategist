from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from strategy_validator.contracts.oracle_strategic_fusion import OracleSensorRawSemanticInput
from strategy_validator.contracts.oracle_temporal_semantics import (
    TemporalEvidenceRef,
    TemporalProviderArtifactManifest,
    TemporalSemanticBatchManifest,
    TemporalSemanticDay,
    TemporalSemanticExtractionBatchRequest,
)
from strategy_validator.validator.providers.nvidia_nim_semantic_provider import NvidiaNimTemporalSemanticProvider


class _TemporalProviderDayResponse(BaseModel):
    semantic_raw: OracleSensorRawSemanticInput
    citations: list[TemporalEvidenceRef] = Field(default_factory=list)
    advisory_notes: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _build_system_prompt() -> str:
    return (
        "You are performing point-in-time semantic extraction for a constitutional oracle. "
        "You must use only the source records provided for the current day. "
        "Do not infer from future dates, external memory, or unprovided context. "
        "Return JSON with semantic_raw, citations, and advisory_notes. "
        "semantic_raw must contain hawkish_document_ratio, dovish_document_ratio, geopolitical_headline_share, contradiction_count, belief_conflict_score."
    )


def _build_user_prompt(request: TemporalSemanticExtractionBatchRequest, day_index: int) -> str:
    day = request.days[day_index]
    payload = {
        "batch_window": {
            "start": request.batch_start_date.isoformat(),
            "end": request.batch_end_date.isoformat(),
        },
        "current_day": {
            "point_in_time_date": day.point_in_time_date.isoformat(),
            "trading_session_id": day.trading_session_id,
            "allowed_prefix_digest_sha256": day.allowed_prefix_digest_sha256,
            "advisory_notes": day.advisory_notes,
            "source_records": [record.model_dump(mode="json") for record in day.source_records],
        },
        "instructions": {
            "citation_rule": "All citations must refer only to source_records provided in current_day.",
            "normalization_rule": "All scores must be between 0 and 1 except contradiction_count which is an integer >= 0.",
        },
    }
    return _json_dumps(payload)


def extract_temporal_semantic_batch(
    request: TemporalSemanticExtractionBatchRequest,
    *,
    provider: NvidiaNimTemporalSemanticProvider,
    artifact_root: Path | None = None,
    temperature: float = 0.0,
) -> tuple[TemporalSemanticBatchManifest, TemporalProviderArtifactManifest]:
    system_prompt = _build_system_prompt()
    manifest_days: list[TemporalSemanticDay] = []
    request_digests: list[str] = []
    response_digests: list[str] = []
    vendor_request_ids: list[str] = []

    artifact_root = artifact_root.resolve() if artifact_root is not None else None
    if artifact_root is not None:
        artifact_root.mkdir(parents=True, exist_ok=True)

    for idx, day_request in enumerate(request.days):
        user_prompt = _build_user_prompt(request, idx)
        request_digest = provider.build_request_digest(system_prompt=system_prompt, user_prompt=user_prompt)
        parsed, metadata = provider.complete_structured_json_with_metadata(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            response_model=_TemporalProviderDayResponse,
        )
        assert isinstance(parsed, _TemporalProviderDayResponse)
        raw_response = metadata.get("raw_response", {})
        response_digest = sha256(_json_dumps(raw_response).encode("utf-8")).hexdigest()
        request_digests.append(request_digest)
        response_digests.append(response_digest)
        if metadata.get("vendor_request_id"):
            vendor_request_ids.append(str(metadata["vendor_request_id"]))

        if artifact_root is not None:
            day_dir = artifact_root / day_request.point_in_time_date.isoformat()
            day_dir.mkdir(parents=True, exist_ok=True)
            (day_dir / "NVIDIA_NIM_TEMPORAL_REQUEST.json").write_text(
                json.dumps(metadata.get("request_body", {}), indent=2, default=str), encoding="utf-8"
            )
            (day_dir / "NVIDIA_NIM_TEMPORAL_RESPONSE.json").write_text(
                json.dumps(raw_response, indent=2, default=str), encoding="utf-8"
            )
            (day_dir / "TEMPORAL_SEMANTIC_DAY.json").write_text(
                json.dumps({
                    "point_in_time_date": day_request.point_in_time_date.isoformat(),
                    "trading_session_id": day_request.trading_session_id,
                    "semantic_raw": parsed.semantic_raw.model_dump(mode="json"),
                    "citations": [c.model_dump(mode="json") for c in parsed.citations],
                    "advisory_notes": parsed.advisory_notes,
                    "allowed_prefix_digest_sha256": day_request.allowed_prefix_digest_sha256,
                    "provider_response_sha256": response_digest,
                }, indent=2, default=str), encoding="utf-8"
            )

        manifest_days.append(
            TemporalSemanticDay(
                point_in_time_date=day_request.point_in_time_date,
                trading_session_id=day_request.trading_session_id,
                semantic_raw=parsed.semantic_raw,
                allowed_prefix_digest_sha256=day_request.allowed_prefix_digest_sha256,
                provider_response_sha256=response_digest,
                citations=parsed.citations,
                advisory_notes=parsed.advisory_notes,
            )
        )

    combined_request_sha = sha256("".join(request_digests).encode("utf-8")).hexdigest()
    combined_response_sha = sha256("".join(response_digests).encode("utf-8")).hexdigest()
    manifest = TemporalSemanticBatchManifest(
        generated_at_utc=datetime.now(timezone.utc),
        provider_kind=request.provider_kind,
        provider_id=request.provider_id,
        model_name=request.model_name,
        batch_start_date=request.batch_start_date,
        batch_end_date=request.batch_end_date,
        days=manifest_days,
    )
    artifact = TemporalProviderArtifactManifest(
        provider_kind=request.provider_kind,
        provider_id=request.provider_id,
        model_name=request.model_name,
        request_sha256=combined_request_sha,
        response_sha256=combined_response_sha,
        request_window_start=request.batch_start_date,
        request_window_end=request.batch_end_date,
        vendor_request_id=",".join(vendor_request_ids) or None,
        retry_count=0,
        timeout_seconds=provider._timeout_seconds,
    )
    if artifact_root is not None:
        (artifact_root / "TEMPORAL_SEMANTIC_BATCH_MANIFEST.json").write_text(
            json.dumps(manifest.model_dump(mode="json"), indent=2, default=str), encoding="utf-8"
        )
        (artifact_root / "TEMPORAL_PROVIDER_ARTIFACT_MANIFEST.json").write_text(
            json.dumps(artifact.model_dump(mode="json"), indent=2, default=str), encoding="utf-8"
        )
    return manifest, artifact
