from __future__ import annotations

from strategy_validator.application.readiness import get_readiness_health_payload


class _FakeReadiness:
    status = 'READY'
    adjudication_allowed = True
    blockers = []
    storage_backend = 'sqlite_single_node'
    storage_upgrade_status = 'PATH_DECLARED_NOT_IMPLEMENTED'
    storage_upgrade_summary = 'Current ledger backend remains single-node SQLite.'


def test_readiness_payload_is_transport_neutral(monkeypatch) -> None:
    monkeypatch.setattr('strategy_validator.application.readiness.get_current_readiness', lambda: _FakeReadiness())
    payload = get_readiness_health_payload()
    assert payload['surface'] == 'readiness'
    assert payload['ok'] is True
    assert payload['status'] == 'READY'


def test_readiness_payload_exposes_storage_upgrade_posture(monkeypatch) -> None:
    monkeypatch.setattr('strategy_validator.application.readiness.get_current_readiness', lambda: _FakeReadiness())
    payload = get_readiness_health_payload()
    assert payload['storage_backend'] == 'sqlite_single_node'
    assert payload['storage_upgrade_status'] == 'PATH_DECLARED_NOT_IMPLEMENTED'
    assert 'SQLite' in payload['storage_upgrade_summary']
