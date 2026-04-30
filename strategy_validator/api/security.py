"""HTTP security envelope for the FastAPI API.

The API is still a single-tenant operator backend, but production deployment must
not rely on route-level auth alone.  This middleware provides transport-neutral
hardening that is safe for tests and containers:

* reject requests whose declared or streamed body exceeds the configured cap;
* add conservative browser/security headers to every HTTP response;
* attach a stable request id header to every response/rejection;
* optionally rate-limit mutating methods with a small in-process window;
* keep the policy explicit without enabling broad CORS by default.
"""
from __future__ import annotations

import json
import os
import re
import time
from collections import defaultdict, deque
from typing import Any
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_ENV_MAX_REQUEST_BYTES = "STRATEGY_VALIDATOR_API_MAX_REQUEST_BYTES"
_ENV_MUTATION_RATE_LIMIT_PER_MINUTE = "STRATEGY_VALIDATOR_API_MUTATION_RATE_LIMIT_PER_MINUTE"
_DEFAULT_MAX_REQUEST_BYTES = 1_048_576
_REQUEST_ID_HEADER = b"x-request-id"
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_.:@-]{1,128}$")
_SECURITY_HEADERS = {
    b"x-content-type-options": b"nosniff",
    b"x-frame-options": b"DENY",
    b"referrer-policy": b"no-referrer",
    b"cross-origin-opener-policy": b"same-origin",
    b"cache-control": b"no-store",
}
_MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _max_request_bytes() -> int:
    raw = os.environ.get(_ENV_MAX_REQUEST_BYTES, "").strip()
    if not raw:
        return _DEFAULT_MAX_REQUEST_BYTES
    try:
        value = int(raw)
    except ValueError:
        return _DEFAULT_MAX_REQUEST_BYTES
    return max(1, value)


def _mutation_rate_limit_per_minute() -> int:
    raw = os.environ.get(_ENV_MUTATION_RATE_LIMIT_PER_MINUTE, "").strip()
    if not raw:
        return 0
    try:
        return max(0, int(raw))
    except ValueError:
        return 0


def _header_value(scope: Scope, header_name: bytes) -> bytes | None:
    for name, value in scope.get("headers") or []:
        if name.lower() == header_name:
            return value
    return None


def _method_can_have_body(scope: Scope) -> bool:
    return str(scope.get("method") or "").upper() in _MUTATION_METHODS


def _request_id(scope: Scope) -> str:
    raw = _header_value(scope, _REQUEST_ID_HEADER)
    if raw is not None:
        try:
            candidate = raw.decode("ascii").strip()
        except UnicodeDecodeError:
            candidate = ""
        if _REQUEST_ID_RE.fullmatch(candidate):
            return candidate
    return f"sv-{uuid4().hex}"


def _client_key(scope: Scope) -> str:
    client = scope.get("client")
    host = client[0] if isinstance(client, tuple) and client else "unknown"
    method = str(scope.get("method") or "").upper()
    path = str(scope.get("path") or "")
    return f"{host}:{method}:{path}"


async def _buffer_request_messages(receive: Receive, *, max_bytes: int) -> tuple[list[Message], bool]:
    messages: list[Message] = []
    consumed = 0
    while True:
        message = await receive()
        messages.append(message)
        if message.get("type") != "http.request":
            return messages, False
        body = message.get("body") or b""
        consumed += len(body)
        if consumed > max_bytes:
            return messages, True
        if not message.get("more_body", False):
            return messages, False


def _replay_receive(messages: list[Message]) -> Receive:
    pending = list(messages)

    async def receive() -> Message:
        if pending:
            return pending.pop(0)
        return {"type": "http.request", "body": b"", "more_body": False}

    return receive


class SecurityEnvelopeMiddleware:
    """Small ASGI middleware for API transport hardening."""

    _rate_windows: dict[str, deque[float]] = defaultdict(deque)

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    def _rate_limited(self, scope: Scope) -> bool:
        limit = _mutation_rate_limit_per_minute()
        if limit <= 0 or not _method_can_have_body(scope):
            return False
        now = time.monotonic()
        cutoff = now - 60.0
        bucket = self._rate_windows[_client_key(scope)]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            return True
        bucket.append(now)
        return False

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        request_id = _request_id(scope)
        max_bytes = _max_request_bytes()
        declared_length = _header_value(scope, b"content-length")
        if declared_length is not None:
            try:
                if int(declared_length.decode("ascii")) > max_bytes:
                    await self._send_rejected(send, request_id=request_id)
                    return
            except ValueError:
                await self._send_rejected(send, request_id=request_id, status=400, code="INVALID_CONTENT_LENGTH")
                return

        if self._rate_limited(scope):
            await self._send_rejected(send, request_id=request_id, status=429, code="MUTATION_RATE_LIMIT_EXCEEDED")
            return

        replay_receive = receive
        if _method_can_have_body(scope):
            buffered_messages, too_large = await _buffer_request_messages(receive, max_bytes=max_bytes)
            if too_large:
                await self._send_rejected(send, request_id=request_id)
                return
            replay_receive = _replay_receive(buffered_messages)

        async def send_with_headers(message: Message) -> None:
            if message.get("type") == "http.response.start":
                headers = list(message.get("headers") or [])
                present = {name.lower() for name, _ in headers}
                for name, value in _SECURITY_HEADERS.items():
                    if name not in present:
                        headers.append((name, value))
                if _REQUEST_ID_HEADER not in present:
                    headers.append((_REQUEST_ID_HEADER, request_id.encode("ascii")))
                message["headers"] = headers
            await send(message)

        await self.app(scope, replay_receive, send_with_headers)

    async def _send_rejected(
        self,
        send: Send,
        *,
        request_id: str,
        status: int = 413,
        code: str = "REQUEST_TOO_LARGE",
    ) -> None:
        body = json.dumps({"detail": code, "request_id": request_id}, separators=(",", ":")).encode("utf-8")
        headers = [(b"content-type", b"application/json"), (_REQUEST_ID_HEADER, request_id.encode("ascii")), *_SECURITY_HEADERS.items()]
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})


def install_security_envelope(app: Any) -> None:
    """Install the API hardening middleware on a FastAPI app."""
    app.add_middleware(SecurityEnvelopeMiddleware)
