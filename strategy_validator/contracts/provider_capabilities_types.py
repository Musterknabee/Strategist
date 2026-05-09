"""Provider capability schema and classification enums."""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "provider_capabilities/v2"


class ProviderCategory(str, Enum):
    FILINGS = "filings"
    MACRO = "macro"
    MARKET_DATA = "market_data"
    FUNDAMENTALS = "fundamentals"
    NEWS = "news"
    CRYPTO = "crypto"
    SPORTS_ODDS = "sports_odds"
    BROKER_EXECUTION = "broker_execution"


class ProviderAccessType(str, Enum):
    PUBLIC_NO_SIGNUP = "PUBLIC_NO_SIGNUP"
    FREE_KEY_REQUIRED = "FREE_KEY_REQUIRED"
    FREEMIUM_KEY_REQUIRED = "FREEMIUM_KEY_REQUIRED"
    PAID_OR_TRIAL = "PAID_OR_TRIAL"
    BROKER_ACCOUNT_REQUIRED = "BROKER_ACCOUNT_REQUIRED"


class DefaultTrustLevel(str, Enum):
    OFFICIAL_SOURCE = "OFFICIAL_SOURCE"
    LICENSED_PROVIDER = "LICENSED_PROVIDER"
    FREEMIUM_RESEARCH_ONLY = "FREEMIUM_RESEARCH_ONLY"
    PUBLIC_BEST_EFFORT = "PUBLIC_BEST_EFFORT"
    SNAPSHOT_ONLY = "SNAPSHOT_ONLY"
    BROKER_EXECUTION = "BROKER_EXECUTION"
    UNAVAILABLE = "UNAVAILABLE"


class PitSuitability(str, Enum):
    STRONG_PIT_SOURCE = "STRONG_PIT_SOURCE"
    PIT_WITH_RELEASE_TIMESTAMP = "PIT_WITH_RELEASE_TIMESTAMP"
    BEST_EFFORT_AS_OF = "BEST_EFFORT_AS_OF"
    NOT_PIT_SAFE_WITHOUT_ARCHIVE = "NOT_PIT_SAFE_WITHOUT_ARCHIVE"
    EXECUTION_ONLY = "EXECUTION_ONLY"


ResearchRole = Literal[
    "official_public_good",
    "research_filings",
    "research_macro",
    "research_market_data",
    "research_fundamentals",
    "research_news",
    "research_crypto",
    "research_sports_odds",
    "broker_execution_paper_first",
]


class ProviderCapability(BaseModel):
    """Machine-readable classification for one logical provider integration surface."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    category: ProviderCategory
    access_type: ProviderAccessType
    env_vars: tuple[str, ...] = ()
    requires_secret: bool = False
    official_docs_url: str = ""
    signup_url: str = ""
    research_role: ResearchRole
    may_gate_live_promotion: bool = False
    default_trust_level: DefaultTrustLevel
    pit_suitability: PitSuitability
    rate_limit_notes: str = ""
    license_notes: str = ""
    recommended_priority: int = Field(default=100, ge=0, le=999)
    unsafe_as_promotion_authority_without_license: bool = False
    personal_live_trading_env_gate: str | None = None


__all__ = (
    "SCHEMA_VERSION",
    "ProviderCategory",
    "ProviderAccessType",
    "DefaultTrustLevel",
    "PitSuitability",
    "ResearchRole",
    "ProviderCapability",
)
