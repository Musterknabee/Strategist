"""Advisory-only Oracle context derived from provider evidence (no ledger authority)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OracleProviderAdvisorySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "oracle_provider_advisory/v1"
    evidence_manifest_digest: str = ""
    provider_coverage: dict[str, Any] = Field(default_factory=dict)
    freshness_gaps: tuple[str, ...] = ()
    unavailable_providers: tuple[str, ...] = ()
    pit_trust_warnings: tuple[str, ...] = ()
    macro_context_hints: tuple[str, ...] = ()
    market_data_context_hints: tuple[str, ...] = ()
    news_context_hints: tuple[str, ...] = ()
    advisory_only: bool = True
    ledger_mutation_disclaimed: bool = True


__all__ = ["OracleProviderAdvisorySummary"]
