from __future__ import annotations

import pytest

from strategy_validator.api.app import create_app
from strategy_validator.contracts.provider_capabilities import (
    PitSuitability,
    ProviderAccessType,
    ProviderCategory,
    SCHEMA_VERSION,
    all_provider_capabilities,
    export_provider_capabilities_payload,
)


# Minimum set the product team asked to classify; registry may grow.
_REQUIRED_PROVIDER_IDS = frozenset(
    {
        "sec_edgar",
        "ecb",
        "eurostat",
        "world_bank_open_data",
        "oecd",
        "imf_data",
        "gdelt",
        "binance_public",
        "kraken_public",
        "fred",
        "bls",
        "bls_registered_api",
        "alpha_vantage",
        "finnhub",
        "financial_modeling_prep",
        "twelve_data",
        "tiingo",
        "eodhd",
        "nasdaq_data_link",
        "polygon_io",
        "massive",
        "guardian_open_platform",
        "newsapi",
        "mediastack",
        "coingecko",
        "coinmarketcap",
        "the_odds_api",
        "football_data_org",
        "api_sports",
        "sportmonks",
        "alpaca",
    }
)


def test_provider_registry_contains_required_providers() -> None:
    ids = {p.provider_id for p in all_provider_capabilities()}
    missing = _REQUIRED_PROVIDER_IDS - ids
    assert not missing, f"missing provider_id(s): {sorted(missing)}"


def test_provider_ids_are_unique() -> None:
    providers = all_provider_capabilities()
    ids = [p.provider_id for p in providers]
    assert len(ids) == len(set(ids))


def test_export_payload_schema() -> None:
    payload = export_provider_capabilities_payload()
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["provider_count"] == len(all_provider_capabilities())
    assert len(payload["providers"]) == len(all_provider_capabilities())


def test_every_provider_has_explicit_pit_suitability() -> None:
    for p in all_provider_capabilities():
        assert isinstance(p.pit_suitability, PitSuitability), p.provider_id


def test_public_providers_do_not_require_secrets() -> None:
    for p in all_provider_capabilities():
        if p.access_type == ProviderAccessType.PUBLIC_NO_SIGNUP:
            assert p.requires_secret is False, p.provider_id


def test_key_required_providers_list_env_vars() -> None:
    for p in all_provider_capabilities():
        if p.access_type in (
            ProviderAccessType.FREE_KEY_REQUIRED,
            ProviderAccessType.FREEMIUM_KEY_REQUIRED,
            ProviderAccessType.PAID_OR_TRIAL,
        ):
            assert p.env_vars, f"{p.provider_id} must document env_vars for key-gated access"
        if p.requires_secret:
            assert p.env_vars, f"{p.provider_id} requires_secret but has no env_vars"


def test_freemium_market_data_does_not_gate_live_promotion_by_default() -> None:
    for p in all_provider_capabilities():
        if (
            p.access_type == ProviderAccessType.FREEMIUM_KEY_REQUIRED
            and p.category == ProviderCategory.MARKET_DATA
        ):
            assert p.may_gate_live_promotion is False, p.provider_id


def test_alpaca_has_personal_live_trading_env_gate() -> None:
    alpaca = next(p for p in all_provider_capabilities() if p.provider_id == "alpaca")
    assert alpaca.personal_live_trading_env_gate == "PERSONAL_LIVE_APPROVED"
    assert alpaca.access_type == ProviderAccessType.BROKER_ACCOUNT_REQUIRED


def test_backend_create_app_without_provider_keys() -> None:
    """Smoke: optional providers are not part of default ASGI wiring."""
    app = create_app()
    assert app.title == "strategy-validator-api"


@pytest.mark.parametrize(
    "provider_id,access_type,category",
    [
        ("sec_edgar", ProviderAccessType.PUBLIC_NO_SIGNUP, ProviderCategory.FILINGS),
        ("fred", ProviderAccessType.FREE_KEY_REQUIRED, ProviderCategory.MACRO),
        ("alpaca", ProviderAccessType.BROKER_ACCOUNT_REQUIRED, ProviderCategory.BROKER_EXECUTION),
    ],
)
def test_sample_provider_classification(provider_id: str, access_type: ProviderAccessType, category: ProviderCategory) -> None:
    p = next(x for x in all_provider_capabilities() if x.provider_id == provider_id)
    assert p.access_type == access_type
    assert p.category == category
