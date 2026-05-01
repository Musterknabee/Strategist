"""PIT-aware normalized observation from a provider sample."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FreshnessClassification(str, Enum):
    STRONG_TIMESTAMP = "STRONG_TIMESTAMP"
    RELEASE_OR_OBSERVATION = "RELEASE_OR_OBSERVATION"
    BEST_EFFORT_AS_OF = "BEST_EFFORT_AS_OF"
    UNKNOWN = "UNKNOWN"


class RevisionPolicy(str, Enum):
    OFFICIAL_VINTAGE = "OFFICIAL_VINTAGE"
    REVISION_SENSITIVE = "REVISION_SENSITIVE"
    SNAPSHOT_ONLY = "SNAPSHOT_ONLY"
    UNKNOWN = "UNKNOWN"


class ProviderObservationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_id: str
    source_endpoint_redacted: str = ""
    retrieved_at_utc: str
    observed_at_utc: str | None = None
    as_of_utc: str | None = None
    published_at_utc: str | None = None
    release_timestamp: str | None = None
    symbol: str | None = None
    series_id: str | None = None
    entity_id: str | None = None
    geography: str | None = None
    value_digest: str | None = Field(default=None, description="Compact hash of normalized values slice")
    raw_sample_digest: str = ""
    normalized_digest: str = ""
    trust_level: str = ""
    pit_suitability: str = ""
    license_scope: str = "research_optional"
    freshness_classification: FreshnessClassification = FreshnessClassification.UNKNOWN
    is_revision_sensitive: bool = False
    revision_policy: RevisionPolicy = RevisionPolicy.UNKNOWN
    may_be_used_for_validation: bool = False
    may_gate_live_promotion: bool = False
    evidence_uri: str = ""
    notes: tuple[str, ...] = ()


__all__ = [
    "FreshnessClassification",
    "ProviderObservationRecord",
    "RevisionPolicy",
]
