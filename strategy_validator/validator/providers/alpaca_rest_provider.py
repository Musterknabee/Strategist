"""
Alpaca REST market-data provider — liquidity + optional borrow/locate.

**Liquidity**: Alpaca Market Data v2 ``GET /v2/stocks/{symbol}/snapshot`` → ``LiquiditySnapshot`` (LIVE).

**Borrow / locate** (optional): Alpaca Trading API ``GET /v2/assets/{symbol}`` → ``BorrowSnapshot`` (LIVE).
  - ``borrow_available`` reflects ``shortable``.
  - ``locate_required`` is ``True`` when ``shortable`` and not ``easy_to_borrow`` (HTB / locate path).
  - The Trading API asset response does **not** include an annualized borrow fee; ``etb_borrow_cost_bps``
    and ``htb_borrow_cost_bps`` are **explicit operator-configured tier rates** (documented defaults),
    not silent guesses from the wire.

Credentials (same keys for typical Alpaca accounts):
  - ``APCA_API_KEY_ID`` and ``APCA_API_SECRET_KEY`` by default; configurable via connector settings.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any, Optional

from strategy_validator.contracts.market_data import BorrowSnapshot, LiquiditySnapshot


def _http_error_token(exc: urllib.error.HTTPError, *, prefix: str) -> str:
    """Stable RuntimeError token for taxonomy (status-specific auth / rate limit / 5xx)."""
    code = int(exc.code)
    suffix = ""
    if code == 429:
        ra = exc.headers.get("Retry-After") if exc.headers else None
        if ra:
            suffix = f"|RETRY_AFTER={ra.strip()}"
    return f"{prefix}_{code}{suffix}"


def _parse_iso_dt(value: Any, fallback: datetime) -> datetime:
    if value is None:
        return fallback
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return fallback
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return fallback


class AlpacaRestMarketDataProvider:
    """Live liquidity from Alpaca Market Data v2; optional borrow from Trading API assets."""

    def __init__(
        self,
        provider_id: str,
        *,
        data_base_url: str = "https://data.alpaca.markets",
        api_key_id_env: str = "APCA_API_KEY_ID",
        api_secret_key_env: str = "APCA_API_SECRET_KEY",
        timeout_seconds: float = 10.0,
        enable_borrow_from_trading_api: bool = False,
        trading_base_url: str = "https://paper-api.alpaca.markets",
        etb_borrow_cost_bps: float = 20.0,
        htb_borrow_cost_bps: float = 300.0,
    ):
        self.provider_id = provider_id
        self._base = data_base_url.rstrip("/")
        self._key_id_env = api_key_id_env
        self._secret_env = api_secret_key_env
        self._timeout = timeout_seconds
        self._enable_borrow = enable_borrow_from_trading_api
        self._trading_base = trading_base_url.rstrip("/") if trading_base_url else ""
        self._etb_bps = float(etb_borrow_cost_bps)
        self._htb_bps = float(htb_borrow_cost_bps)

    def _auth_headers(self) -> dict[str, str]:
        key_id = os.environ.get(self._key_id_env, "").strip()
        secret = os.environ.get(self._secret_env, "").strip()
        if not key_id or not secret:
            raise RuntimeError("ALPACA_CREDENTIALS_MISSING")
        return {
            "Accept": "application/json",
            "User-Agent": "strategy-validator-alpaca-rest/1.0",
            "APCA-API-KEY-ID": key_id,
            "APCA-API-SECRET-KEY": secret,
        }

    def _get_json(self, url: str) -> dict[str, Any]:
        req = urllib.request.Request(url, headers=self._auth_headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
                body = resp.read().decode("utf-8")
        except TimeoutError:
            raise
        except urllib.error.HTTPError as exc:
            raise RuntimeError(_http_error_token(exc, prefix="ALPACA_HTTP")) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"ALPACA_URL_ERROR:{exc.reason}") from exc
        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError("ALPACA_INVALID_JSON") from exc
        if not isinstance(data, dict):
            raise RuntimeError("ALPACA_JSON_NOT_OBJECT")
        return data

    def _snapshot(self, symbol: str) -> dict[str, Any]:
        path = f"/v2/stocks/{urllib.parse.quote(symbol, safe='.')}/snapshot"
        return self._get_json(f"{self._base}{path}")

    def _trading_asset(self, symbol: str) -> Optional[dict[str, Any]]:
        if not self._trading_base:
            return None
        path = f"/v2/assets/{urllib.parse.quote(symbol, safe='.')}"
        url = f"{self._trading_base}{path}"
        req = urllib.request.Request(url, headers=self._auth_headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
                body = resp.read().decode("utf-8")
        except TimeoutError:
            raise
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise RuntimeError(_http_error_token(exc, prefix="ALPACA_TRADING_HTTP")) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"ALPACA_TRADING_URL_ERROR:{exc.reason}") from exc
        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError("ALPACA_TRADING_INVALID_JSON") from exc
        if not isinstance(data, dict):
            raise RuntimeError("ALPACA_TRADING_JSON_NOT_OBJECT")
        return data

    def provide_liquidity(self, asset_id: str, timestamp: datetime) -> Optional[LiquiditySnapshot]:
        symbol = asset_id.strip().upper()
        if not symbol:
            return None
        data = self._snapshot(symbol)

        lq = data.get("latestQuote") or {}
        bp, ap = lq.get("bp"), lq.get("ap")
        if bp is None or ap is None:
            raise RuntimeError("ALPACA_LIQUIDITY_MISSING_QUOTES")
        try:
            fbp, fap = float(bp), float(ap)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("ALPACA_LIQUIDITY_NON_NUMERIC_QUOTES") from exc
        if fbp <= 0 or fap <= 0:
            raise RuntimeError("ALPACA_LIQUIDITY_NON_POSITIVE_QUOTES")
        mid = (fap + fbp) / 2.0
        spread_bps = (fap - fbp) / mid * 10000.0 if mid > 0 else 0.0

        bar = data.get("prevDailyBar") or data.get("dailyBar") or {}
        vol = float(bar.get("v") or 0.0)
        vw = bar.get("vw")
        close = bar.get("c")
        if vol > 0 and vw is not None:
            adv_notional = vol * float(vw)
        elif vol > 0 and close is not None:
            adv_notional = vol * float(close)
        else:
            adv_notional = 0.0

        t_raw = lq.get("t") or (data.get("latestTrade") or {}).get("t")
        snap_time = _parse_iso_dt(t_raw, timestamp)

        if adv_notional <= 0.0 and spread_bps <= 0.0:
            raise RuntimeError("ALPACA_LIQUIDITY_INSUFFICIENT_DEPTH")

        return LiquiditySnapshot(
            asset_id=asset_id,
            snapshot_time=snap_time,
            adv_notional=max(adv_notional, 0.0),
            spread_bps=max(spread_bps, 0.0),
            volume_proxy=max(vol, 0.0),
            source_id=self.provider_id,
            source_mode="LIVE",
        )

    def provide_borrow(self, asset_id: str, timestamp: datetime) -> Optional[BorrowSnapshot]:
        """
        LIVE borrow/locate from Alpaca Trading API asset record (when enabled).

        When disabled, returns ``None`` so a different ``BorrowFeed`` may be used.
        """
        if not self._enable_borrow or not self._trading_base:
            return None
        symbol = asset_id.strip().upper()
        if not symbol:
            return None
        data = self._trading_asset(symbol)
        if data is None:
            return None

        shortable = bool(data.get("shortable", False))
        easy = bool(data.get("easy_to_borrow", False))

        if not shortable:
            return BorrowSnapshot(
                asset_id=asset_id,
                snapshot_time=timestamp,
                borrow_available=False,
                borrow_cost_bps=0.0,
                locate_required=False,
                source_id=self.provider_id,
                source_mode="LIVE",
            )

        locate_required = not easy
        cost_bps = self._etb_bps if easy else self._htb_bps

        return BorrowSnapshot(
            asset_id=asset_id,
            snapshot_time=timestamp,
            borrow_available=True,
            borrow_cost_bps=cost_bps,
            locate_required=locate_required,
            source_id=self.provider_id,
            source_mode="LIVE",
        )
