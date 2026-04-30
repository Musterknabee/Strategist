"""OpenBB market-data ingress (HTTP JSON) for oracle temporal sensor pipelines.

Tests may subclass ``OpenBBMarketDataProvider`` and override ``_get_json`` to avoid network I/O.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from strategy_validator.contracts.oracle_strategic_fusion import (
    OracleSensorRawMacroInput,
    OracleSensorRawMicrostructureInput,
)


class OpenBBMarketDataProvider:
    """Fetch macro/microstructure oracle sensor inputs via configured URL templates."""

    def __init__(
        self,
        provider_id: str,
        *,
        mode: str = "http",
        base_url: str | None = None,
        oracle_macro_url_template: str = "",
        oracle_microstructure_url_template: str = "",
        api_key_env_var: str | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.provider_id = provider_id
        self._mode = mode
        self._base = (base_url or "").rstrip("/")
        self._macro_tpl = oracle_macro_url_template
        self._micro_tpl = oracle_microstructure_url_template
        self._api_key_env_var = api_key_env_var
        self._timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "User-Agent": "strategy-validator-openbb/1.0"}
        if self._api_key_env_var:
            key = os.environ.get(self._api_key_env_var, "")
            if key.strip():
                headers["Authorization"] = f"Bearer {key.strip()}"
        return headers

    def _absolute_url(self, template: str, *, universe_label: str, point_in_time_date: str) -> str:
        path = template.format(point_in_time_date=point_in_time_date, universe_label=universe_label)
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not self._base:
            return path
        return f"{self._base}{path if path.startswith('/') else '/' + path}"

    def _get_json(self, url: str) -> Any:
        if self._mode != "http":
            raise RuntimeError(f"OPENBB_MODE_UNSUPPORTED:{self._mode}")
        if not url:
            return None
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout_seconds) as resp:  # noqa: S310
                body = resp.read().decode("utf-8")
        except TimeoutError:
            raise
        except urllib.error.HTTPError as exc:
            if 400 <= int(exc.code) < 500:
                return None
            raise RuntimeError(f"OPENBB_HTTP_{exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OPENBB_URL_ERROR:{exc.reason}") from exc
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None

    def provide_oracle_macro_input(self, *, universe_label: str, point_in_time_date: str) -> OracleSensorRawMacroInput | None:
        url = self._absolute_url(self._macro_tpl, universe_label=universe_label, point_in_time_date=point_in_time_date)
        raw = self._get_json(url)
        if not isinstance(raw, dict):
            return None
        try:
            return OracleSensorRawMacroInput.model_validate(raw)
        except Exception:
            return None

    def provide_oracle_microstructure_input(
        self, *, universe_label: str, point_in_time_date: str
    ) -> OracleSensorRawMicrostructureInput | None:
        url = self._absolute_url(self._micro_tpl, universe_label=universe_label, point_in_time_date=point_in_time_date)
        raw = self._get_json(url)
        if not isinstance(raw, dict):
            return None
        try:
            return OracleSensorRawMicrostructureInput.model_validate(raw)
        except Exception:
            return None
