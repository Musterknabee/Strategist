from __future__ import annotations

from strategy_validator.core.config import AppConfig
from strategy_validator.validator.providers.alpaca_rest_provider import AlpacaRestMarketDataProvider
from strategy_validator.validator.providers.http_json_provider import HttpJsonMarketDataProvider
from strategy_validator.validator.providers.nvidia_nim_semantic_provider import NvidiaNimTemporalSemanticProvider
from strategy_validator.validator.providers.openbb_provider import OpenBBMarketDataProvider


def build_alpaca_market_data_provider(cfg: AppConfig) -> AlpacaRestMarketDataProvider:
    alpaca = cfg.market_data_alpaca_connector
    if alpaca is None:
        raise RuntimeError("ALPACA_CONNECTOR_NOT_CONFIGURED")
    return AlpacaRestMarketDataProvider(
        alpaca.provider_id,
        data_base_url=alpaca.data_base_url,
        api_key_id_env=alpaca.api_key_id_env,
        api_secret_key_env=alpaca.api_secret_key_env,
        timeout_seconds=alpaca.timeout_seconds,
        enable_borrow_from_trading_api=alpaca.enable_borrow_from_trading_api,
        trading_base_url=alpaca.trading_base_url,
        etb_borrow_cost_bps=alpaca.etb_borrow_cost_bps,
        htb_borrow_cost_bps=alpaca.htb_borrow_cost_bps,
    )


def build_http_json_market_data_provider(cfg: AppConfig) -> HttpJsonMarketDataProvider:
    http_json = cfg.market_data_http_json_connector
    if http_json is None:
        raise RuntimeError("HTTP_JSON_CONNECTOR_NOT_CONFIGURED")
    return HttpJsonMarketDataProvider(
        http_json.provider_id,
        liquidity_url_template=http_json.liquidity_url_template,
        borrow_url_template=http_json.borrow_url_template,
        api_key_env_var=http_json.api_key_env_var,
        timeout_seconds=http_json.timeout_seconds,
    )


def build_openbb_market_data_provider(cfg: AppConfig) -> OpenBBMarketDataProvider:
    openbb = cfg.market_data_openbb_connector
    if openbb is None:
        raise RuntimeError("OPENBB_CONNECTOR_NOT_CONFIGURED")
    return OpenBBMarketDataProvider(
        openbb.provider_id,
        mode=openbb.mode,
        base_url=openbb.base_url,
        oracle_macro_url_template=openbb.oracle_macro_url_template,
        oracle_microstructure_url_template=openbb.oracle_microstructure_url_template,
        api_key_env_var=openbb.api_key_env_var,
        timeout_seconds=openbb.timeout_seconds,
    )


def build_nvidia_nim_semantic_provider(cfg: AppConfig) -> NvidiaNimTemporalSemanticProvider:
    nim = cfg.semantic_nvidia_nim_connector
    if nim is None:
        raise RuntimeError("NVIDIA_NIM_CONNECTOR_NOT_CONFIGURED")
    return NvidiaNimTemporalSemanticProvider(
        nim.provider_id,
        base_url=nim.base_url,
        api_key_env=nim.api_key_env,
        model=nim.model,
        timeout_seconds=nim.timeout_seconds,
        max_retries=nim.max_retries,
    )
