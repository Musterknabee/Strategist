from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import app


def test_api_security_headers_are_emitted() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cross-origin-opener-policy"] == "same-origin"


def test_api_security_envelope_rejects_declared_oversized_request(monkeypatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_MAX_REQUEST_BYTES", "8")
    client = TestClient(app)
    response = client.post("/readiness", content=b"x" * 16)
    assert response.status_code == 413
    assert response.json()["detail"] == "REQUEST_TOO_LARGE"


def test_security_envelope_rejects_streamed_body_without_content_length(monkeypatch) -> None:
    import asyncio

    from strategy_validator.api.security import SecurityEnvelopeMiddleware

    monkeypatch.setenv("STRATEGY_VALIDATOR_API_MAX_REQUEST_BYTES", "8")
    called = {"app": False}
    sent = []

    async def app(scope, receive, send):
        called["app"] = True
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    async def receive():
        return {"type": "http.request", "body": b"123456789", "more_body": False}

    async def send(message):
        sent.append(message)

    scope = {"type": "http", "method": "POST", "headers": []}
    asyncio.run(SecurityEnvelopeMiddleware(app)(scope, receive, send))

    assert called["app"] is False
    assert sent[0]["status"] == 413
