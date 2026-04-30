from __future__ import annotations

import asyncio

from strategy_validator.api.security import SecurityEnvelopeMiddleware


async def _call_app(scope, messages):
    async def app(scope, receive, send):
        await send({'type': 'http.response.start', 'status': 200, 'headers': []})
        await send({'type': 'http.response.body', 'body': b'ok'})

    sent = []

    async def receive():
        if messages:
            return messages.pop(0)
        return {'type': 'http.request', 'body': b'', 'more_body': False}

    async def send(message):
        sent.append(message)

    await SecurityEnvelopeMiddleware(app)(scope, receive, send)
    return sent


def test_security_envelope_preserves_valid_request_id():
    sent = asyncio.run(_call_app(
        {
            'type': 'http',
            'method': 'GET',
            'path': '/healthz',
            'headers': [(b'x-request-id', b'req-123')],
            'client': ('127.0.0.1', 1),
        },
        [{'type': 'http.request', 'body': b'', 'more_body': False}],
    ))
    response_start = sent[0]
    assert (b'x-request-id', b'req-123') in response_start['headers']


def test_security_envelope_rate_limits_mutation_requests(monkeypatch):
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_MUTATION_RATE_LIMIT_PER_MINUTE', '1')
    SecurityEnvelopeMiddleware._rate_windows.clear()
    scope = {
        'type': 'http',
        'method': 'POST',
        'path': '/ui/commands/claim-item',
        'headers': [],
        'client': ('192.0.2.10', 1),
    }
    first = asyncio.run(_call_app(dict(scope), [{'type': 'http.request', 'body': b'{}', 'more_body': False}]))
    second = asyncio.run(_call_app(dict(scope), [{'type': 'http.request', 'body': b'{}', 'more_body': False}]))
    assert first[0]['status'] == 200
    assert second[0]['status'] == 429
