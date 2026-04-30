from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import app


class _FakeReadiness:
    status = 'DEGRADED'
    adjudication_allowed = False
    blockers = [type('Blocker', (), {'code': 'X'})()]


def test_readiness_health_route_uses_service(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.readiness.get_readiness_health_payload',
        lambda: {
            'ok': False,
            'surface': 'readiness',
            'status': 'DEGRADED',
            'adjudication_allowed': False,
            'blocker_codes': ['X'],
        },
    )
    client = TestClient(app)
    response = client.get('/readiness/health')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'DEGRADED'
    assert payload['adjudication_allowed'] is False
    assert payload['blocker_codes'] == ['X']
