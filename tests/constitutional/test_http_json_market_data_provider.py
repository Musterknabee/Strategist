"""Contract tests for the HTTP/JSON live connector skeleton."""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest

from strategy_validator.validator.providers.http_json_provider import HttpJsonMarketDataProvider


class _Handler(BaseHTTPRequestHandler):
    store: dict[str, Any] = {}

    def log_message(self, *args: Any) -> None:  # noqa: ANN401
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/liquidity/"):
            body = json.dumps(_Handler.store["liquidity"]).encode("utf-8")
        elif self.path.startswith("/borrow/"):
            body = json.dumps(_Handler.store["borrow"]).encode("utf-8")
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.mark.constitutional
def test_http_json_provider_parses_live_liquidity_and_borrow():
    _Handler.store["liquidity"] = {
        "adv_notional": 1_000_000.0,
        "spread_bps": 4.5,
        "snapshot_time": "2026-04-12T12:00:00+00:00",
    }
    _Handler.store["borrow"] = {
        "borrow_available": True,
        "borrow_cost_bps": 42.0,
        "snapshot_time": "2026-04-12T12:00:00+00:00",
    }
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://127.0.0.1:{port}"
    try:
        p = HttpJsonMarketDataProvider(
            "test_http_vendor",
            liquidity_url_template=f"{base}/liquidity/{{asset_id}}",
            borrow_url_template=f"{base}/borrow/{{asset_id}}",
            timeout_seconds=3.0,
        )
        ts = datetime(2026, 4, 12, 12, 0, tzinfo=timezone.utc)
        liq = p.provide_liquidity("AAPL", ts)
        brw = p.provide_borrow("AAPL", ts)
        assert liq is not None
        assert liq.source_mode == "LIVE"
        assert liq.source_id == "test_http_vendor"
        assert liq.adv_notional == 1_000_000.0
        assert brw is not None
        assert brw.source_mode == "LIVE"
        assert brw.borrow_cost_bps == 42.0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class _SlowHandler(BaseHTTPRequestHandler):
    def log_message(self, *args: Any) -> None:  # noqa: ANN401
        return

    def do_GET(self) -> None:  # noqa: N802
        import time

        time.sleep(0.5)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b"{}")


@pytest.mark.constitutional
def test_http_json_empty_payload_raises_schema_error():
    _Handler.store["liquidity"] = {}
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _, port = server.server_address
    base = f"http://127.0.0.1:{port}"
    try:
        p = HttpJsonMarketDataProvider(
            "test_http_vendor",
            liquidity_url_template=f"{base}/liquidity/{{asset_id}}",
            timeout_seconds=3.0,
        )
        with pytest.raises(RuntimeError, match="HTTP_JSON_LIQUIDITY_MISSING_ADV_NOTIONAL"):
            p.provide_liquidity("AAPL", datetime(2026, 4, 12, tzinfo=timezone.utc))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.constitutional
def test_http_json_provider_timeout_surfaces_as_timeout_error():
    server = HTTPServer(("127.0.0.1", 0), _SlowHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _, port = server.server_address
    base = f"http://127.0.0.1:{port}"
    p = HttpJsonMarketDataProvider(
        "slow",
        liquidity_url_template=f"{base}/liquidity/{{asset_id}}",
        timeout_seconds=0.05,
    )
    try:
        with pytest.raises(TimeoutError):
            p.provide_liquidity("AAPL", datetime.now(timezone.utc))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
