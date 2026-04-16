from __future__ import annotations

from strategy_validator.application.readiness import get_readiness_health_payload


class _FakeReadiness:
    status = 'READY'
    adjudication_allowed = True
    blockers = []


def test_readiness_payload_is_transport_neutral(monkeypatch) -> None:
    monkeypatch.setattr('strategy_validator.application.readiness.get_current_readiness', lambda: _FakeReadiness())
    payload = get_readiness_health_payload()
    assert payload['surface'] == 'readiness'
    assert payload['ok'] is True
    assert payload['status'] == 'READY'
