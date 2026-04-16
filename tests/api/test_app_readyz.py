from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import app


def test_readyz_reports_ready_when_readiness_service_is_ready(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.app.get_readiness_health_payload',
        lambda: {
            'ok': True,
            'surface': 'readiness',
            'status': 'READY',
            'adjudication_allowed': True,
            'blocker_codes': [],
        },
    )
    client = TestClient(app)

    response = client.get('/readyz')

    assert response.status_code == 200
    assert response.json()['status'] == 'READY'


def test_readyz_fails_closed_when_readiness_service_is_blocked(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.app.get_readiness_health_payload',
        lambda: {
            'ok': False,
            'surface': 'readiness',
            'status': 'BLOCKED',
            'adjudication_allowed': False,
            'blocker_codes': ['INCOMPATIBLE_SCHEMA'],
        },
    )
    client = TestClient(app)

    response = client.get('/readyz')

    assert response.status_code == 503
    payload = response.json()
    assert payload['status'] == 'BLOCKED'
    assert payload['blocker_codes'] == ['INCOMPATIBLE_SCHEMA']
