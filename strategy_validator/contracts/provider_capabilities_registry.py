"""Aggregate provider capability registry helpers."""
from __future__ import annotations

from strategy_validator.contracts.provider_capabilities_alternative import ALTERNATIVE_PROVIDER_CAPABILITIES
from strategy_validator.contracts.provider_capabilities_execution import EXECUTION_PROVIDER_CAPABILITIES
from strategy_validator.contracts.provider_capabilities_market import MARKET_PROVIDER_CAPABILITIES
from strategy_validator.contracts.provider_capabilities_official import OFFICIAL_PROVIDER_CAPABILITIES
from strategy_validator.contracts.provider_capabilities_types import SCHEMA_VERSION, ProviderCapability

_PROVIDER_ID_ORDER: tuple[str, ...] = (
    "alpha_vantage",
    "alpaca",
    "api_sports",
    "binance_public",
    "bls",
    "bls_registered_api",
    "coingecko",
    "coinmarketcap",
    "ecb",
    "eodhd",
    "eurostat",
    "financial_modeling_prep",
    "finnhub",
    "football_data_org",
    "fred",
    "gdelt",
    "guardian_open_platform",
    "imf_data",
    "kraken_public",
    "massive",
    "mediastack",
    "nasdaq_data_link",
    "newsapi",
    "oecd",
    "polygon_io",
    "sec_edgar",
    "sportmonks",
    "the_odds_api",
    "tiingo",
    "twelve_data",
    "world_bank_open_data",
)
_PROVIDER_ORDER_INDEX = {provider_id: index for index, provider_id in enumerate(_PROVIDER_ID_ORDER)}

_PROVIDERS: tuple[ProviderCapability, ...] = tuple(
    sorted(
        (
            *OFFICIAL_PROVIDER_CAPABILITIES,
            *MARKET_PROVIDER_CAPABILITIES,
            *ALTERNATIVE_PROVIDER_CAPABILITIES,
            *EXECUTION_PROVIDER_CAPABILITIES,
        ),
        key=lambda provider: _PROVIDER_ORDER_INDEX[provider.provider_id],
    )
)


def all_provider_capabilities() -> tuple[ProviderCapability, ...]:
    return _PROVIDERS


def export_provider_capabilities_payload() -> dict[str, object]:
    providers = [provider.model_dump(mode="json") for provider in _PROVIDERS]
    return {
        "schema_version": SCHEMA_VERSION,
        "providers": providers,
        "provider_count": len(providers),
    }


def capability_by_provider_id() -> dict[str, ProviderCapability]:
    return {provider.provider_id: provider for provider in _PROVIDERS}


__all__ = (
    "all_provider_capabilities",
    "export_provider_capabilities_payload",
    "capability_by_provider_id",
)
