from __future__ import annotations

import pytest

from strategy_validator.core.provider_url_policy import validate_provider_url, validate_provider_url_template


def test_provider_url_policy_rejects_insecure_absolute_urls() -> None:
    with pytest.raises(ValueError):
        validate_provider_url("http://example.com", field_name="provider.base_url")


def test_provider_url_template_allows_relative_paths() -> None:
    assert validate_provider_url_template("/v1/liquidity/{asset_id}") == "/v1/liquidity/{asset_id}"


def test_provider_url_env_overrides_are_validated_before_assignment(monkeypatch) -> None:
    from strategy_validator.core.config import load_config

    monkeypatch.setenv("STRATEGY_VALIDATOR_ALPACA_MARKET_DATA_ENABLED", "true")
    monkeypatch.setenv("STRATEGY_VALIDATOR_ALPACA_DATA_BASE_URL", "http://localhost:8080")

    cfg = load_config()

    assert cfg.market_data_alpaca_connector is not None
    assert cfg.market_data_alpaca_connector.data_base_url == "https://data.alpaca.markets"
    assert any("STRATEGY_VALIDATOR_ALPACA_DATA_BASE_URL" in item for item in cfg.runtime_policy.invalid_environment_overrides)


def test_provider_url_policy_rejects_protocol_relative_and_private_network_targets() -> None:
    with pytest.raises(ValueError, match="protocol-relative"):
        validate_provider_url_template("//metadata.internal/v1")
    with pytest.raises(ValueError, match="private"):
        validate_provider_url("https://10.0.0.1/v1", field_name="provider.base_url")
