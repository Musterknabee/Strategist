"""Bounded OpenBB market-data provider.

The provider supports two modes:
  - http: treat OpenBB (or an OpenBB-backed sidecar) as an operator-supplied HTTP/JSON service
  - python: lazy-import the OpenBB Python client at call time

Both modes remain bounded behind the MarketDataProvider protocol so the repo does not
spray OpenBB imports across the validator core.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from importlib import import_module
from typing import Any, Literal, Optional

from strategy_validator.contracts.market_data import BorrowSnapshot, LiquiditySnapshot, SourceMode
from strategy_validator.contracts.oracle import OracleSensorRawMacroInput, OracleSensorRawMicrostructureInput

OpenBBProviderMode = Literal["http", "python"]


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


class OpenBBMarketDataProvider:
    def __init__(
        self,
        provider_id: str,
        *,
        mode: OpenBBProviderMode = "http",
        base_url: str | None = None,
        liquidity_url_template: str = "",
        borrow_url_template: str = "",
        oracle_macro_url_template: str = "",
        oracle_microstructure_url_template: str = "",
        api_key_env_var: Optional[str] = None,
        timeout_seconds: float = 10.0,
        source_mode: SourceMode = "SNAPSHOT",
        default_equity_provider: str | None = None,
        default_macro_provider: str | None = None,
    ):
        self.provider_id = provider_id
        self._mode = mode
        self._base_url = (base_url or "").rstrip("/")
        self._liquidity_url_template = liquidity_url_template
        self._borrow_url_template = borrow_url_template
        self._oracle_macro_url_template = oracle_macro_url_template
        self._oracle_microstructure_url_template = oracle_microstructure_url_template
        self._api_key_env_var = api_key_env_var
        self._timeout_seconds = timeout_seconds
        self._source_mode = source_mode
        self._default_equity_provider = default_equity_provider
        self._default_macro_provider = default_macro_provider

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "User-Agent": "strategy-validator-openbb/1.0"}
        if self._api_key_env_var:
            key = os.environ.get(self._api_key_env_var, "").strip()
            if key:
                headers["Authorization"] = f"Bearer {key}"
        return headers

    def _resolve_url(self, template: str, *, asset_id: str) -> str:
        url = template.format(asset_id=asset_id)
        if url.startswith("http://") or url.startswith("https://"):
            return url
        if self._base_url and url.startswith("/"):
            return f"{self._base_url}{url}"
        if self._base_url and url:
            return f"{self._base_url}/{url}"
        return url

    def _resolve_templated_url(self, template: str, **kwargs: Any) -> str:
        url = template.format(**{k: urllib.parse.quote(str(v), safe='-_:T') for k, v in kwargs.items()})
        if url.startswith("http://") or url.startswith("https://"):
            return url
        if self._base_url and url.startswith("/"):
            return f"{self._base_url}{url}"
        if self._base_url and url:
            return f"{self._base_url}/{url}"
        return url

    def _coerce_oracle_macro_input(self, data: dict[str, Any]) -> OracleSensorRawMacroInput:
        try:
            return OracleSensorRawMacroInput(
                yield_curve_slope_bps=float(data.get('yield_curve_slope_bps') or data.get('yield_curve_slope') or 0.0),
                high_yield_credit_spread_bps=float(data.get('high_yield_credit_spread_bps') or data.get('hy_credit_spread_bps') or data.get('credit_spread_bps') or 0.0),
                equity_bond_correlation_20d=float(data.get('equity_bond_correlation_20d') or data.get('equity_bond_correlation') or 0.0),
                cross_asset_correlation_20d=float(data.get('cross_asset_correlation_20d') or data.get('cross_asset_correlation') or 0.0),
                realized_volatility_20d=float(data.get('realized_volatility_20d') or data.get('realized_vol_20d') or 0.0),
                realized_volatility_252d=float(data.get('realized_volatility_252d') or data.get('realized_vol_252d') or 1e-6),
            )
        except (TypeError, ValueError) as exc:
            raise RuntimeError('OPENBB_ORACLE_MACRO_FIELDS_INVALID') from exc

    def _coerce_oracle_microstructure_input(self, data: dict[str, Any]) -> OracleSensorRawMicrostructureInput:
        try:
            return OracleSensorRawMicrostructureInput(
                buy_volume=float(data.get('buy_volume') or data.get('aggressive_buy_volume') or 0.0),
                sell_volume=float(data.get('sell_volume') or data.get('aggressive_sell_volume') or 0.0),
                median_spread_bps=float(data.get('median_spread_bps') or data.get('spread_bps') or 0.0),
                baseline_spread_bps=float(data.get('baseline_spread_bps') or data.get('baseline_spread') or 1e-6),
                top_book_depth_usd=float(data.get('top_book_depth_usd') or data.get('top_of_book_depth_usd') or 0.0),
                baseline_top_book_depth_usd=float(data.get('baseline_top_book_depth_usd') or data.get('baseline_depth_usd') or 1e-6),
                toxic_flow_ratio=float(data.get('toxic_flow_ratio') or data.get('vpin') or 0.0),
            )
        except (TypeError, ValueError) as exc:
            raise RuntimeError('OPENBB_ORACLE_MICROSTRUCTURE_FIELDS_INVALID') from exc

    def provide_oracle_macro_input(self, *, universe_label: str, point_in_time_date: Any) -> Optional[OracleSensorRawMacroInput]:
        if not self._oracle_macro_url_template:
            return None
        data = self._get_json(
            self._resolve_templated_url(
                self._oracle_macro_url_template,
                universe_label=universe_label,
                point_in_time_date=point_in_time_date,
                date=point_in_time_date,
            )
        )
        if data is None:
            return None
        return self._coerce_oracle_macro_input(data)

    def provide_oracle_microstructure_input(self, *, universe_label: str, point_in_time_date: Any) -> Optional[OracleSensorRawMicrostructureInput]:
        if self._oracle_microstructure_url_template:
            data = self._get_json(
                self._resolve_templated_url(
                    self._oracle_microstructure_url_template,
                    universe_label=universe_label,
                    point_in_time_date=point_in_time_date,
                    date=point_in_time_date,
                )
            )
            if data is None:
                return None
            return self._coerce_oracle_microstructure_input(data)
        if self._mode == 'python':
            return None
        return None

    def _get_json(self, url: str) -> Optional[dict[str, Any]]:
        if not url:
            return None
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout_seconds) as resp:  # noqa: S310
                body = resp.read().decode("utf-8")
        except TimeoutError:
            raise
        except urllib.error.HTTPError as exc:
            suffix = ""
            if exc.code == 429:
                ra = exc.headers.get("Retry-After") if exc.headers else None
                if ra:
                    suffix = f"|RETRY_AFTER={ra.strip()}"
            raise RuntimeError(f"OPENBB_HTTP_{exc.code}{suffix}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OPENBB_URL_ERROR:{exc.reason}") from exc
        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError("OPENBB_INVALID_JSON") from exc
        if isinstance(data, list):
            data = data[0] if data else {}
        if not isinstance(data, dict):
            raise RuntimeError("OPENBB_JSON_NOT_OBJECT")
        return data

    def _coerce_openbb_payload(self, payload: Any) -> dict[str, Any]:
        current = payload
        if hasattr(current, "model_dump"):
            current = current.model_dump(mode="json")
        elif hasattr(current, "to_dict"):
            current = current.to_dict()
        if isinstance(current, list):
            current = current[0] if current else {}
        if not isinstance(current, dict):
            raise RuntimeError("OPENBB_PYTHON_PAYLOAD_UNSUPPORTED")
        return current

    def _python_quote(self, asset_id: str) -> dict[str, Any]:
        try:
            openbb_module = import_module("openbb")
        except ModuleNotFoundError as exc:
            raise RuntimeError("OPENBB_PYTHON_NOT_INSTALLED") from exc
        obb = getattr(openbb_module, "obb", None)
        quote_fn = getattr(getattr(getattr(obb, "equity", None), "price", None), "quote", None)
        if quote_fn is None:
            raise RuntimeError("OPENBB_PYTHON_QUOTE_ENDPOINT_MISSING")
        kwargs: dict[str, Any] = {"symbol": asset_id}
        if self._default_equity_provider:
            kwargs["provider"] = self._default_equity_provider
        return self._coerce_openbb_payload(quote_fn(**kwargs))

    def provide_liquidity(self, asset_id: str, timestamp: datetime) -> Optional[LiquiditySnapshot]:
        if self._mode == "python":
            data = self._python_quote(asset_id)
        else:
            if not self._liquidity_url_template:
                return None
            data = self._get_json(self._resolve_url(self._liquidity_url_template, asset_id=asset_id))
            if data is None:
                return None
        try:
            bid = float(data.get("bid") or data.get("bid_price") or data.get("bp") or 0.0)
            ask = float(data.get("ask") or data.get("ask_price") or data.get("ap") or 0.0)
            last = float(data.get("last") or data.get("last_price") or data.get("price") or data.get("close") or 0.0)
            volume = float(data.get("volume") or data.get("volume_proxy") or data.get("shares") or 0.0)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("OPENBB_LIQUIDITY_FIELDS_INVALID") from exc
        if ask > 0.0 and bid > 0.0:
            mid = (ask + bid) / 2.0
            spread_bps = ((ask - bid) / mid * 10_000.0) if mid > 0.0 else 0.0
        else:
            spread_bps = float(data.get("spread_bps") or 0.0)
        price_for_notional = last or ask or bid
        adv_notional = float(data.get("adv_notional") or 0.0)
        if adv_notional <= 0.0 and volume > 0.0 and price_for_notional > 0.0:
            adv_notional = volume * price_for_notional
        snap_time = _parse_iso_dt(data.get("snapshot_time") or data.get("last_timestamp") or data.get("date"), timestamp)
        source_id = self.provider_id
        if self._default_equity_provider:
            source_id = f"{source_id}:{self._default_equity_provider}"
        return LiquiditySnapshot(
            asset_id=asset_id,
            snapshot_time=snap_time,
            adv_notional=max(adv_notional, 0.0),
            spread_bps=max(spread_bps, 0.0),
            volume_proxy=max(volume, 0.0),
            source_id=source_id,
            source_mode=self._source_mode,
        )

    def provide_borrow(self, asset_id: str, timestamp: datetime) -> Optional[BorrowSnapshot]:
        if self._mode == "python":
            return None
        if not self._borrow_url_template:
            return None
        data = self._get_json(self._resolve_url(self._borrow_url_template, asset_id=asset_id))
        if data is None:
            return None
        try:
            borrow_cost_bps = float(data.get("borrow_cost_bps") or 0.0)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("OPENBB_BORROW_FIELDS_INVALID") from exc
        snap_time = _parse_iso_dt(data.get("snapshot_time") or data.get("snapshot_time_iso"), timestamp)
        source_id = self.provider_id
        if self._default_equity_provider:
            source_id = f"{source_id}:{self._default_equity_provider}"
        return BorrowSnapshot(
            asset_id=asset_id,
            snapshot_time=snap_time,
            borrow_available=bool(data.get("borrow_available", False)),
            borrow_cost_bps=borrow_cost_bps,
            locate_required=data.get("locate_required"),
            source_id=source_id,
            source_mode=self._source_mode,
        )
