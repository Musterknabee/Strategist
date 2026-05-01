"""Machine-readable provider health snapshot contracts (research/data spine)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RemediationSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKER_EXECUTION_ONLY = "BLOCKER_EXECUTION_ONLY"


class ProviderHealthEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_id: str
    display_name: str = ""
    configured: bool = False
    reachable: bool = False
    classified_status: str = Field(description="OK, PENDING_KEY, AUTH_FAILED, etc.")
    http_status: int | None = Field(
        default=None,
        description="Optional HTTP status from last provider sample fetch when manifest records it.",
    )
    access_type: str = ""
    trust_level: str = ""
    pit_suitability: str = ""
    last_checked_utc: str | None = None
    sample_digest_prefix: str | None = Field(default=None, description="SHA-256 hex prefix only")
    freshness_timestamp: str | None = None
    may_gate_live_promotion: bool = False
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    remediation: tuple[str, ...] = ()
    evidence_reference: str = ""
    execution_posture: dict[str, Any] | None = Field(
        default=None,
        description="Optional broker execution hints from env (e.g. Alpaca). No API keys; read-plane only.",
    )


class ProviderHealthSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "provider_health_snapshot/v1"
    generated_at_utc: str
    samples_manifest_path: str | None = None
    samples_manifest_digest_prefix: str | None = None
    execution_workflow_blockers: tuple[str, ...] = ()
    entries: tuple[ProviderHealthEntry, ...]
    summary: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "ProviderHealthEntry",
    "ProviderHealthSnapshot",
    "RemediationSeverity",
]
