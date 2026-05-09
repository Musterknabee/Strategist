"""Provider capability registry entries for execution."""
from __future__ import annotations

from strategy_validator.contracts.provider_capabilities_types import (
    DefaultTrustLevel,
    PitSuitability,
    ProviderAccessType,
    ProviderCapability,
    ProviderCategory,
)

EXECUTION_PROVIDER_CAPABILITIES: tuple[ProviderCapability, ...] = (
    ProviderCapability(
            provider_id="alpaca",
            display_name="Alpaca Markets",
            category=ProviderCategory.BROKER_EXECUTION,
            access_type=ProviderAccessType.BROKER_ACCOUNT_REQUIRED,
            env_vars=(
                "ALPACA_API_KEY",
                "ALPACA_API_SECRET",
                "APCA_API_KEY_ID",
                "APCA_API_SECRET_KEY",
                "STRATEGY_VALIDATOR_ALPACA_API_KEY_ID_ENV",
                "STRATEGY_VALIDATOR_ALPACA_API_SECRET_KEY_ENV",
            ),
            requires_secret=True,
            official_docs_url="https://docs.alpaca.markets/",
            signup_url="https://alpaca.markets/",
            research_role="broker_execution_paper_first",
            may_gate_live_promotion=False,
            default_trust_level=DefaultTrustLevel.BROKER_EXECUTION,
            pit_suitability=PitSuitability.EXECUTION_ONLY,
            rate_limit_notes="Paper vs live endpoints and limits differ.",
            license_notes="Not canonical PIT tape; live money requires explicit operator approval and KYC outside this repo.",
            recommended_priority=20,
            unsafe_as_promotion_authority_without_license=True,
            personal_live_trading_env_gate="PERSONAL_LIVE_APPROVED",
        ),
)


__all__ = ("EXECUTION_PROVIDER_CAPABILITIES",)
