"""HTTP telemetry sink retry behavior against a local stub server."""
from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest

from strategy_validator.validator.telemetry_sinks import HttpPostTelemetrySink


class _FlakyHandler(BaseHTTPRequestHandler):
    def log_message(self, *args: Any) -> None:  # noqa: ANN401
        return

    def do_POST(self) -> None:  # noqa: N802
        self.server.attempts += 1  # type: ignore[attr-defined]
        if self.server.attempts < 3:
            self.send_error(503)
            return
        self.send_response(204)
        self.end_headers()


@pytest.mark.constitutional
def test_http_post_sink_retries_until_success() -> None:
    server = HTTPServer(("127.0.0.1", 0), _FlakyHandler)
    server.attempts = 0  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _, port = server.server_address
    url = f"http://127.0.0.1:{port}/ingest"
    try:
        sink = HttpPostTelemetrySink(
            url,
            timeout_seconds=2.0,
            max_retries=3,
            backoff_start_ms=1.0,
        )
        sink.emit({"event": "retry_test"})
        assert server.attempts == 3  # type: ignore[attr-defined]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
