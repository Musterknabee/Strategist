"""Operator-facing provider setup and freshness console contracts."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProviderSetupEntry(BaseModel):
    """Secret-safe setup/freshness row for one provider integration."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str
    display_name: str
    category: str
    research_role: str
    access_type: str
    trust_level: str
    pit_suitability: str
    recommended_priority: int
    official_docs_url: str = ""
    signup_url: str = ""
    expected_env_vars: tuple[str, ...] = ()
    requires_secret: bool = False
    configured: bool = False
    reachable: bool = False
    classified_status: str = "NOT_CHECKED"
    canonical_status: str = "UNKNOWN"
    setup_status: str
    readiness_tier: str
    freshness_class: str
    freshness_age_seconds: int | None = None
    freshness_max_age_seconds: int
    last_checked_utc: str | None = None
    sample_digest_prefix: str | None = None
    evidence_reference: str = ""
    may_gate_live_promotion: bool = False
    unsafe_as_promotion_authority_without_license: bool = False
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    remediation: tuple[str, ...] = ()


class ProviderSetupConsolePayload(BaseModel):
    """Read-plane console payload. Never contains provider secret values."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "ui_provider_setup_console/v1"
    generated_at_utc: str
    read_plane_only: bool = True
    mutation_authority: str = "NONE"
    execution_authority: str = "NONE"
    no_network_calls: bool = True
    no_secret_values: bool = True
    freshness_max_age_seconds: int
    samples_manifest_path: str | None = None
    samples_manifest_digest_prefix: str | None = None
    execution_workflow_blockers: tuple[str, ...] = ()
    summary: dict[str, Any] = Field(default_factory=dict)
    entries: tuple[ProviderSetupEntry, ...]


__all__ = ["ProviderSetupConsolePayload", "ProviderSetupEntry"]
