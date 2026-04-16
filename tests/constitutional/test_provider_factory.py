from __future__ import annotations

import pytest

from strategy_validator.core.config import (
    AlpacaMarketDataConnectorSettings,
    AppConfig,
    HttpJsonMarketDataConnectorSettings,
    RuntimePolicy,
)
from strategy_validator.core.enums import RuntimeMode
from strategy_validator.validator.providers.factory import (
    build_alpaca_market_data_provider,
    build_http_json_market_data_provider,
)


@pytest.mark.constitutional
def test_factory_returns_none_when_disabled() -> None:
    cfg = AppConfig(
        mode=RuntimeMode.DEV,
        runtime_policy=RuntimePolicy(),
        market_data_http_connector=HttpJsonMarketDataConnectorSettings(enabled=False),
    )
    assert build_http_json_market_data_provider(cfg) is None


@pytest.mark.constitutional
def test_factory_builds_provider_when_enabled() -> None:
    cfg = AppConfig(
        mode=RuntimeMode.DEV,
        runtime_policy=RuntimePolicy(),
        market_data_http_connector=HttpJsonMarketDataConnectorSettings(
            enabled=True,
            provider_id="p1",
            liquidity_url_template="http://127.0.0.1:1/l/{asset_id}",
        ),
    )
    p = build_http_json_market_data_provider(cfg)
    assert p is not None
    assert p.provider_id == "p1"


@pytest.mark.constitutional
def test_factory_builds_alpaca_when_enabled() -> None:
    cfg = AppConfig(
        mode=RuntimeMode.DEV,
        runtime_policy=RuntimePolicy(),
        market_data_alpaca_connector=AlpacaMarketDataConnectorSettings(enabled=True),
    )
    p = build_alpaca_market_data_provider(cfg)
    assert p is not None
    assert p.provider_id == "alpaca_data_v2"
