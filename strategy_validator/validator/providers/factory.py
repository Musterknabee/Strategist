"""Construct configured market-data providers from AppConfig."""
from __future__ import annotations

from typing import Optional

from strategy_validator.core.config import AppConfig
from strategy_validator.validator.providers.alpaca_rest_provider import AlpacaRestMarketDataProvider
from strategy_validator.validator.providers.http_json_provider import HttpJsonMarketDataProvider
from strategy_validator.validator.providers.nvidia_nim_semantic_provider import NvidiaNimTemporalSemanticProvider
from strategy_validator.validator.providers.openbb_provider import OpenBBMarketDataProvider


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



def build_openbb_market_data_provider(cfg: AppConfig) -> Optional[OpenBBMarketDataProvider]:
    """Return a configured OpenBB provider when enabled."""
    oc = cfg.market_data_openbb_connector
    if oc is None or not oc.enabled:
        return None
    return OpenBBMarketDataProvider(
        oc.provider_id,
        mode=oc.mode,
        base_url=oc.base_url,
        liquidity_url_template=oc.liquidity_url_template,
        borrow_url_template=oc.borrow_url_template,
        oracle_macro_url_template=oc.oracle_macro_url_template,
        oracle_microstructure_url_template=oc.oracle_microstructure_url_template,
        api_key_env_var=oc.api_key_env_var,
        timeout_seconds=oc.timeout_seconds,
        source_mode=oc.source_mode,
        default_equity_provider=oc.default_equity_provider,
        default_macro_provider=oc.default_macro_provider,
    )



def build_nvidia_nim_semantic_provider(cfg: AppConfig) -> Optional[NvidiaNimTemporalSemanticProvider]:
    """Return a configured NVIDIA NIM semantic provider when enabled."""
    nc = cfg.semantic_nvidia_nim_connector
    if nc is None or not nc.enabled:
        return None
    return NvidiaNimTemporalSemanticProvider(
        nc.provider_id,
        base_url=nc.base_url,
        api_key_env=nc.api_key_env,
        model=nc.model,
        timeout_seconds=nc.timeout_seconds,
        max_retries=nc.max_retries,
    )
