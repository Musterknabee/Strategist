"""
HTTP/JSON market-data provider skeleton (stdlib only).

Lawful behavior:
  - Successful parses return LIVE snapshots with explicit source_id (provider_id).
  - Malformed responses return None (MISSING at feed layer), never PROVISIONAL.
  - Timeouts raise TimeoutError for the resilience wrapper to classify.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Optional

from strategy_validator.contracts.market_data import BorrowSnapshot, LiquiditySnapshot


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


class HttpJsonMarketDataProvider:
    """
    Production-grade connector skeleton over HTTP JSON endpoints.

    URL templates may include `{asset_id}` which is substituted verbatim.
    Optional API key is read from `api_key_env_var` when set (never logged).
    """

    def __init__(
        self,
        provider_id: str,
        *,
        liquidity_url_template: str = "",
        borrow_url_template: str = "",
        api_key_env_var: Optional[str] = None,
        timeout_seconds: float = 10.0,
    ):
        self.provider_id = provider_id
        self._liquidity_url_template = liquidity_url_template
        self._borrow_url_template = borrow_url_template
        self._api_key_env_var = api_key_env_var
        self._timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "User-Agent": "strategy-validator-http-json/1.0"}
        if self._api_key_env_var:
            key = os.environ.get(self._api_key_env_var, "")
            if key:
                headers["Authorization"] = f"Bearer {key}"
        return headers

    def _get_json(self, url: str) -> Optional[dict[str, Any]]:
        if not url:
            return None
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout_seconds) as resp:  # noqa: S310 - controlled URL from operator config
                body = resp.read().decode("utf-8")
        except TimeoutError:
            raise
        except urllib.error.HTTPError as exc:
            suffix = ""
            if exc.code == 429:
                ra = exc.headers.get("Retry-After") if exc.headers else None
                if ra:
                    suffix = f"|RETRY_AFTER={ra.strip()}"
            raise RuntimeError(f"HTTP_JSON_HTTP_{exc.code}{suffix}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"HTTP_JSON_URL_ERROR:{exc.reason}") from exc
        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError("HTTP_JSON_INVALID_JSON") from exc
        if not isinstance(data, dict):
            raise RuntimeError("HTTP_JSON_JSON_NOT_OBJECT")
        return data

    def provide_liquidity(self, asset_id: str, timestamp: datetime) -> Optional[LiquiditySnapshot]:
        if not self._liquidity_url_template:
            return None
        url = self._liquidity_url_template.format(asset_id=asset_id)
        data = self._get_json(url)
        if data is None:
            return None
        if "adv_notional" not in data:
            raise RuntimeError("HTTP_JSON_LIQUIDITY_MISSING_ADV_NOTIONAL")
        try:
            adv_notional = float(data["adv_notional"])
            spread_bps = float(data.get("spread_bps", 0.0))
            volume_proxy = float(data.get("volume_proxy", 0.0))
        except (TypeError, ValueError) as exc:
            raise RuntimeError("HTTP_JSON_LIQUIDITY_FIELDS_INVALID") from exc
        snap_time = _parse_iso_dt(data.get("snapshot_time") or data.get("snapshot_time_iso"), timestamp)
        return LiquiditySnapshot(
            asset_id=asset_id,
            snapshot_time=snap_time,
            adv_notional=adv_notional,
            spread_bps=spread_bps,
            volume_proxy=volume_proxy,
            source_id=self.provider_id,
            source_mode="LIVE",
        )

    def provide_borrow(self, asset_id: str, timestamp: datetime) -> Optional[BorrowSnapshot]:
        if not self._borrow_url_template:
            return None
        url = self._borrow_url_template.format(asset_id=asset_id)
        data = self._get_json(url)
        if data is None:
            return None
        if "borrow_available" not in data:
            raise RuntimeError("HTTP_JSON_BORROW_MISSING_FLAGS")
        try:
            borrow_cost_bps = float(data.get("borrow_cost_bps", 0.0))
        except (TypeError, ValueError) as exc:
            raise RuntimeError("HTTP_JSON_BORROW_FIELDS_INVALID") from exc
        snap_time = _parse_iso_dt(data.get("snapshot_time") or data.get("snapshot_time_iso"), timestamp)
        return BorrowSnapshot(
            asset_id=asset_id,
            snapshot_time=snap_time,
            borrow_available=bool(data["borrow_available"]),
            borrow_cost_bps=borrow_cost_bps,
            locate_required=data.get("locate_required"),
            source_id=self.provider_id,
            source_mode="LIVE",
        )
