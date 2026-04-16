"""Production-oriented market-data provider implementations."""

from strategy_validator.validator.providers.alpaca_rest_provider import AlpacaRestMarketDataProvider
from strategy_validator.validator.providers.factory import (
    build_alpaca_market_data_provider,
    build_http_json_market_data_provider,
    build_nvidia_nim_semantic_provider,
    build_openbb_market_data_provider,
)
from strategy_validator.validator.providers.http_json_provider import HttpJsonMarketDataProvider
from strategy_validator.validator.providers.nvidia_nim_semantic_provider import NvidiaNimTemporalSemanticProvider
from strategy_validator.validator.providers.openbb_provider import OpenBBMarketDataProvider
from strategy_validator.validator.market_data_feeds import provider_resilience_from_runtime_policy

__all__ = [
    "AlpacaRestMarketDataProvider",
    "HttpJsonMarketDataProvider",
    "OpenBBMarketDataProvider",
    "NvidiaNimTemporalSemanticProvider",
    "build_alpaca_market_data_provider",
    "build_http_json_market_data_provider",
    "build_openbb_market_data_provider",
    "build_nvidia_nim_semantic_provider",
    "provider_resilience_from_runtime_policy",
]
