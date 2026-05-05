"""Governed evidence manifest linking provider samples, health, and digests."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvidenceArtifactDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    path: str
    sha256: str = Field(description="Full hex digest of artifact bytes")


class ProviderEvidenceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest_version: str = "provider_evidence_manifest/v1"
    generated_at_utc: str
    command: str = "python scripts/build_provider_evidence_manifest.py"
    command_args_redacted: tuple[str, ...] = ()
    paper_only: bool = True
    live_trading_blocked: bool = True
    replayable_offline: bool = True
    replay_manifest_path: str | None = None
    source_run_id: str
    provider_sample_manifest_digest: str
    normalized_records_digest: str
    provider_health_digest: str
    artifacts: tuple[EvidenceArtifactDescriptor, ...] = ()
    trust_summary: dict[str, Any] = Field(default_factory=dict)
    pit_summary: dict[str, Any] = Field(default_factory=dict)
    unavailable_providers: tuple[str, ...] = ()
    secret_redaction_assertion: str = (
        "no_raw_secrets_in_manifest_fields_v1"
    )
    dsse_signature_b64: str | None = None


__all__ = [
    "EvidenceArtifactDescriptor",
    "ProviderEvidenceManifest",
]
