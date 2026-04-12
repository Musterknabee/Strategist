"""Construct configured market-data providers from AppConfig."""
from __future__ import annotations

from typing import Optional

from strategy_validator.core.config import AppConfig
from strategy_validator.validator.providers.alpaca_rest_provider import AlpacaRestMarketDataProvider
from strategy_validator.validator.providers.http_json_provider import HttpJsonMarketDataProvider


def build_http_json_market_data_provider(cfg: AppConfig) -> Optional[HttpJsonMarketDataProvider]:
    """Return a configured HTTP/JSON provider when enabled; otherwise None."""
    mdc = cfg.market_data_http_connector
    if mdc is None or not mdc.enabled:
        return None
    return HttpJsonMarketDataProvider(
        mdc.provider_id,
        liquidity_url_template=mdc.liquidity_url_template,
        borrow_url_template=mdc.borrow_url_template,
        api_key_env_var=mdc.api_key_env_var,
        timeout_seconds=mdc.timeout_seconds,
    )


def build_alpaca_market_data_provider(cfg: AppConfig) -> Optional[AlpacaRestMarketDataProvider]:
    """Return a configured Alpaca Market Data v2 provider when enabled."""
    ac = cfg.market_data_alpaca_connector
    if ac is None or not ac.enabled:
        return None
    return AlpacaRestMarketDataProvider(
        ac.provider_id,
        data_base_url=ac.data_base_url,
        api_key_id_env=ac.api_key_id_env,
        api_secret_key_env=ac.api_secret_key_env,
        timeout_seconds=ac.timeout_seconds,
        enable_borrow_from_trading_api=ac.enable_borrow_from_trading_api,
        trading_base_url=ac.trading_base_url,
        etb_borrow_cost_bps=ac.etb_borrow_cost_bps,
        htb_borrow_cost_bps=ac.htb_borrow_cost_bps,
    )
