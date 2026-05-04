"""Assemble provider evidence manifest payloads from sample + normalized + health digests."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.contracts.evidence_manifest import EvidenceArtifactDescriptor, ProviderEvidenceManifest
from strategy_validator.contracts.provider_health import ProviderHealthSnapshot


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""


def _json_digest(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_provider_evidence_manifest_payload(
    *,
    samples_manifest_path: Path,
    normalized_records_path: Path | None,
    health_snapshot: ProviderHealthSnapshot,
    generated_at_utc: str | None = None,
    source_run_id: str | None = None,
) -> ProviderEvidenceManifest:
    when = generated_at_utc or datetime.now(timezone.utc).isoformat()
    run_id = source_run_id or str(uuid.uuid4())

    sp_digest = _file_digest(samples_manifest_path)
    norm_digest = _file_digest(normalized_records_path) if normalized_records_path else ""
    if not norm_digest and normalized_records_path is not None:
        norm_digest = "missing_normalized_file"

    health_obj = health_snapshot.model_dump(mode="json")
    health_digest = hashlib.sha256(
        json.dumps(health_obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    artifacts: list[EvidenceArtifactDescriptor] = [
        EvidenceArtifactDescriptor(
            kind="provider_samples_manifest",
            path=samples_manifest_path.as_posix(),
            sha256=sp_digest or "missing",
        )
    ]
    if normalized_records_path and normalized_records_path.is_file():
        artifacts.append(
            EvidenceArtifactDescriptor(
                kind="normalized_provider_observations",
                path=normalized_records_path.as_posix(),
                sha256=norm_digest,
            )
        )

    trust_counts: dict[str, int] = {}
    pit_counts: dict[str, int] = {}
    unavailable: list[str] = []
    bad_checked = {
        "AUTH_FAILED",
        "PLAN_LIMITED",
        "ENDPOINT_CHANGED",
        "RATE_LIMITED",
        "TEMPORARILY_UNAVAILABLE",
        "PARSE_ERROR",
    }
    for e in health_snapshot.entries:
        trust_counts[e.trust_level] = trust_counts.get(e.trust_level, 0) + 1
        pit_counts[e.pit_suitability] = pit_counts.get(e.pit_suitability, 0) + 1
        if e.classified_status in bad_checked:
            unavailable.append(e.provider_id)

    return ProviderEvidenceManifest(
        generated_at_utc=when,
        source_run_id=run_id,
        provider_sample_manifest_digest=sp_digest,
        normalized_records_digest=norm_digest or _json_digest([]),
        provider_health_digest=health_digest,
        artifacts=tuple(artifacts),
        trust_summary={"counts_by_trust_level": trust_counts},
        pit_summary={"counts_by_pit_suitability": pit_counts},
        unavailable_providers=tuple(sorted(set(unavailable))),
    )


__all__ = ["build_provider_evidence_manifest_payload"]
