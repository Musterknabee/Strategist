"""
Typed vendor / transport failure taxonomy for market-data lookups.

Used alongside human-readable ``provider_errors`` strings so operators and
sinks can aggregate without parsing free text.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

VendorFailureDomain = Literal[
    "NETWORK",
    "AUTH",
    "RATE_LIMIT",
    "VENDOR_4XX",
    "VENDOR_5XX",
    "TIMEOUT",
    "CIRCUIT",
    "SCHEMA",
    "MISSING",
    "UNKNOWN",
]


class VendorFailureEvent(BaseModel):
    """One classified failure along a market-data path (append-only semantics)."""
    domain: VendorFailureDomain = "UNKNOWN"
    code: str = Field(default="UNSPECIFIED", min_length=1)
    detail: str = ""
    feed_kind: Literal["liquidity", "borrow", "fallback_liquidity", "fallback_borrow"] = "liquidity"
    provider_id: str = Field(default="unknown", min_length=1)
    occurred_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"extra": "forbid"}


def classify_vendor_failure_detail(
    detail: str,
    *,
    feed_kind: Literal["liquidity", "borrow", "fallback_liquidity", "fallback_borrow"],
    provider_id: str,
) -> VendorFailureEvent:
    """
    Map a captured error string (from provider or urllib) into a typed event.

    Heuristic but deterministic: prefers stable prefixes used by in-repo providers.
    """
    d = (detail or "").strip()
    low = d.lower()
    domain: VendorFailureDomain = "UNKNOWN"
    code = "UNSPECIFIED"

    if "circuit_open" in low or d == "CIRCUIT_OPEN":
        domain, code = "CIRCUIT", "CIRCUIT_OPEN"
    elif "timeouterror" in low or "timeout" in low or "timed out" in low:
        domain, code = "TIMEOUT", "TIMEOUT"
    elif "alpaca_http_401" in low or "alpaca_trading_http_401" in low:
        domain, code = "AUTH", "HTTP_401"
    elif "alpaca_http_403" in low or "alpaca_trading_http_403" in low:
        domain, code = "AUTH", "HTTP_403"
    elif "http_401" in low:
        domain, code = "AUTH", "HTTP_401"
    elif "http_403" in low:
        domain, code = "AUTH", "HTTP_403"
    elif "alpaca_http_429" in low or "alpaca_trading_http_429" in low or "http_429" in low:
        domain, code = "RATE_LIMIT", "HTTP_429"
    elif "retry_after=" in low:
        domain, code = "RATE_LIMIT", "RETRY_AFTER"
    elif "alpaca_http_4" in low or "alpaca_trading_http_4" in low or "http_4" in low:
        domain, code = "VENDOR_4XX", "HTTP_4XX"
    elif "alpaca_http_5" in low or "alpaca_trading_http_5" in low or "http_5" in low or "503" in d or "502" in d:
        domain, code = "VENDOR_5XX", "HTTP_5XX"
    elif "alpaca_liquidity_" in low or "alpaca_invalid_json" in low or "alpaca_json_not_object" in low:
        domain, code = "SCHEMA", "ALPACA_LIQUIDITY_SHAPE"
    elif "http_json_" in low or "json_not_object" in low or "invalid_json" in low:
        domain, code = "SCHEMA", "HTTP_JSON_SHAPE"
    elif "url_error" in low or "connection" in low or "errno" in low or "gaierror" in low:
        domain, code = "NETWORK", "TRANSPORT"
    elif "malformed" in low:
        domain, code = "SCHEMA", "PARSE"
    elif "credentials_missing" in low:
        domain, code = "AUTH", "MISSING_CREDENTIALS"
    elif not d:
        domain, code = "UNKNOWN", "EMPTY"
    else:
        code = "VENDOR_OR_APP"

    return VendorFailureEvent(
        domain=domain,
        code=code,
        detail=d[:2048],
        feed_kind=feed_kind,
        provider_id=provider_id or "unknown",
    )
