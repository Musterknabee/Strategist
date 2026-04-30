"""
Sink-neutral telemetry export (must never disturb adjudication).

Configured only via environment variables so operators can wire exports
without touching core logic.
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any, Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class TelemetrySink(Protocol):
    def emit(self, record: dict[str, Any]) -> None: ...


class JsonlFileTelemetrySink:
    """Append one JSON object per line (durable local sink)."""

    def __init__(self, path: str):
        self._path = path

    def emit(self, record: dict[str, Any]) -> None:
        line = json.dumps(record, default=str, sort_keys=True) + "\n"
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(line)


class HttpPostTelemetrySink:
    """
    POST JSON to an operator collector with production-style retries and optional auth.

    Retries use exponential backoff; failures are logged, not raised.
    """

    def __init__(
        self,
        url: str,
        *,
        timeout_seconds: float = 5.0,
        max_retries: int = 3,
        backoff_start_ms: float = 100.0,
        bearer_token: Optional[str] = None,
        extra_headers: Optional[dict[str, str]] = None,
    ):
        self._url = url
        self._timeout = timeout_seconds
        self._max_retries = max(1, int(max_retries))
        self._backoff_start_ms = max(0.0, float(backoff_start_ms))
        self._bearer_token = bearer_token
        self._extra_headers = extra_headers or {}

    def emit(self, record: dict[str, Any]) -> None:
        payload = json.dumps(record, default=str).encode("utf-8")
        headers = {"Content-Type": "application/json", **self._extra_headers}
        if self._bearer_token:
            headers["Authorization"] = f"Bearer {self._bearer_token}"
        last_err: Optional[BaseException] = None
        for attempt in range(self._max_retries):
            req = urllib.request.Request(self._url, data=payload, method="POST", headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
                    try:
                        resp.read()
                    except OSError:
                        # Response headers already committed; body read can flake on Windows after 2xx.
                        pass
                return
            except (
                TimeoutError,
                urllib.error.URLError,
                urllib.error.HTTPError,
                ConnectionError,
                OSError,
            ) as exc:
                last_err = exc
                if attempt < self._max_retries - 1 and self._backoff_start_ms > 0:
                    delay = (self._backoff_start_ms / 1000.0) * (2**attempt)
                    time.sleep(delay)
        logger.warning("TELEMETRY_HTTP_EXHAUSTED_RETRIES: %s: %s", self._url, last_err)


def _sinks_from_env() -> list[TelemetrySink]:
    sinks: list[TelemetrySink] = []
    jl = os.environ.get("STRATEGY_VALIDATOR_TELEMETRY_JSONL_PATH")
    if jl:
        sinks.append(JsonlFileTelemetrySink(jl))
    hu = os.environ.get("STRATEGY_VALIDATOR_TELEMETRY_HTTP_URL")
    if hu:
        raw_to = os.environ.get("STRATEGY_VALIDATOR_TELEMETRY_HTTP_TIMEOUT_SECONDS", "5")
        try:
            to = float(raw_to)
        except ValueError:
            to = 5.0
        raw_retries = os.environ.get("STRATEGY_VALIDATOR_TELEMETRY_HTTP_MAX_RETRIES", "3")
        try:
            max_retries = int(raw_retries)
        except ValueError:
            max_retries = 3
        raw_bo = os.environ.get("STRATEGY_VALIDATOR_TELEMETRY_HTTP_BACKOFF_START_MS", "100")
        try:
            backoff_ms = float(raw_bo)
        except ValueError:
            backoff_ms = 100.0
        bearer: Optional[str] = None
        bearer_env_name = os.environ.get("STRATEGY_VALIDATOR_TELEMETRY_HTTP_BEARER_TOKEN_ENV")
        if bearer_env_name:
            bearer = os.environ.get(bearer_env_name.strip(), "")
            if bearer == "":
                bearer = None
        extra: dict[str, str] = {}
        raw_hdr = os.environ.get("STRATEGY_VALIDATOR_TELEMETRY_HTTP_AUTH_HEADER")
        if raw_hdr and ":" in raw_hdr:
            name, value = raw_hdr.split(":", 1)
            extra[name.strip()] = value.strip()
        sinks.append(
            HttpPostTelemetrySink(
                hu,
                timeout_seconds=to,
                max_retries=max_retries,
                backoff_start_ms=backoff_ms,
                bearer_token=bearer,
                extra_headers=extra or None,
            )
        )
    return sinks


def emit_decision_telemetry_sinks(telemetry_record: dict[str, Any]) -> None:
    """
    Emit a single telemetry record to all configured sinks.

    Swallows all sink failures — adjudication correctness must never depend on export.
    """
    for sink in _sinks_from_env():
        try:
            sink.emit(telemetry_record)
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, TypeError, ValueError) as exc:
            logger.warning("TELEMETRY_SINK_FAILED: %s: %s", sink.__class__.__name__, exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("TELEMETRY_SINK_FAILED: %s: %s", sink.__class__.__name__, exc)
